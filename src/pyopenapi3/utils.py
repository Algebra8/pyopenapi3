from __future__ import annotations

from typing import (
    Optional,
    Any,
    Union,
    Type,
    Tuple,
    cast,
    Callable,
    Dict,
    List,
    Generator,
    Iterable
)
from string import Formatter
import inspect

from .objects import (
    Number,
    String,
    Boolean,
    Integer,
    Array,
    Field,
    is_arb_type,
    Primitive,
    Component,
    OpenApiObject, Email, Float, Double, Int32, Int64,
    Date, DateTime, Byte, Binary, Password, MediaType
)
from .schemas import (
    StringDTSchema, ByteDTSchema, BinaryDTSchema, DateDTSchema,
    DateTimeDTSchema, PasswordDTSchema, IntegerDTSchema, Int32DTSchema,
    Int64DTSchema, NumberDTSchema, FloatDTSchema, DoubleDTSchema,
    EmailDTSchema,
    BoolDTSchema, ArrayDTSchema,
    ComponentsObject,
    ReferenceObject,
    PrimitiveDTSchema,
    ObjectsDTSchema,
    DTSchema,
    Schema,
    FieldSchemaT,
    SchemaMapping,
    MediaTypeEnum,
    AnyTypeArrayDTSchema,
    MixedTypeArrayDTSchema,
    MediaTypeObject
)


OPENAPI_DEF = '__OPENAPIDEF__FIELD_OR_COMPONENT__'


class _ObjectToDTSchema:

    # Strings
    String = StringDTSchema
    Byte = ByteDTSchema
    Binary = BinaryDTSchema
    Date = DateDTSchema
    DateTime = DateTimeDTSchema
    Password = PasswordDTSchema
    Email = EmailDTSchema

    # Numbers
    Number = NumberDTSchema
    Float = FloatDTSchema
    Double = DoubleDTSchema
    Integer = IntegerDTSchema
    Int32 = Int32DTSchema
    Int64 = Int64DTSchema

    # Bool
    Boolean = BoolDTSchema

    # Arrays
    SingleArray = ArrayDTSchema
    MixedTypeArray = MixedTypeArrayDTSchema
    AnyTypeArray = AnyTypeArrayDTSchema

    # Objects
    Component = ReferenceObject

    def __call__(self, cls_or_name: Union[str, Type]) -> Type[DTSchema]:
        """Return the schema of a Data Type.

        Note that only non-complex data types are allowered here:
        cannot
        """
        if inspect.isclass(cls_or_name):
            n = cls_or_name.__name__
        else:
            n = cls_or_name
        if hasattr(self, n):
            return getattr(self, n)
        # TODO raise error?


ObjectToDTSchema = _ObjectToDTSchema()


# Helper for formating descriptions.
def format_description(s: Optional[str]) -> Optional[str]:
    # TODO what if s is None...
    if s is None:
        return
    s = s.strip()
    s = s.replace("\n", "")
    s = s.replace("\t", "")
    return " ".join(s.split())


def parse_name_and_type_from_fmt_str(
        formatted_str) -> Generator[Tuple[str, Type[DTSchema]]]:
    """
    Parse a formatted string and return the names
    of the args and their types.

    E.g. "/user/{id:int}" -> ("id", "int")

    If the string is not formatted, then will return (None, None).
    """
    for _, arg_name, _type_name, _ in Formatter().parse(formatted_str):
        if arg_name is not None:
            try:
                yield arg_name, ObjectToDTSchema(_type_name)
            except AttributeError:
                raise ValueError(
                    "A non-`Field` or `OpenApiObject` type was found. "
                    f"Can't use `{_type_name}` as a type in {formatted_str}."
                ) from None


def create_reference(name: str) -> ReferenceObject:
    return ReferenceObject(ref=f"#/components/schemas/{name}")


def mark_component_and_attach_schema(obj, schema):
    """Mark an object as relating to an Open API schema
    and attach said schema to it.

    This will be used by `create_object` to build the entire
    `ObjectSchema`.
    """
    setattr(obj, OPENAPI_DEF, schema)


def create_schema(
        __type: Type[OpenApiObject],
        **kwargs: Any
) -> Schema:
    if issubclass(__type, Component):
        return convert_objects_to_schema(__type)
    elif issubclass(__type, Primitive):
        return convert_primitive_to_schema(__type, **kwargs)
    elif issubclass(__type, Array):
        return convert_array_to_schema(__type, **kwargs)
    else:
        # TODO Error handling
        raise ValueError("Wrong type.")


def convert_objects_to_schema(obj: Type[Component]) -> ReferenceObject:
    # Any non-reference object should be created by the
    # Components builder.
    return create_reference(obj.__name__)


def convert_primitive_to_schema(
        primitive: Type[Primitive], **kwargs) -> PrimitiveDTSchema:
    return cast(PrimitiveDTSchema, ObjectToDTSchema(primitive)(**kwargs))


def convert_array_to_schema(
        array: Type[Array], **kwargs: Any) -> ArrayDTSchema:
    schema_type = cast(Type[ArrayDTSchema], ObjectToDTSchema(array))
    if schema_type is AnyTypeArrayDTSchema:
        return schema_type(**kwargs)
    else:
        sub_schemas = []
        for _type in array.tvars:
            if issubclass(_type, Component):
                sub_schemas.append(create_reference(_type.__name__))
                continue
            sub_schemas.append(ObjectToDTSchema(_type)())

        if schema_type is MixedTypeArrayDTSchema:
            items = {'oneOf': sub_schemas}
            return schema_type(items=items, **kwargs)
        else:
            return schema_type(items=sub_schemas[0], **kwargs)


def build_property_schema_from_func(
        f: Callable, *,
        # `read_only` and `example` are
        # inputted from the user directly.
        read_only: Optional[bool],
        example: Optional[Any],
) -> Schema:
    """Convert data on a custom object's method to a `Field`
    or `Component` schema and return its Open API representation,
    i.e. {name: schema}.
    """
    if not hasattr(f, '__annotations__'):
        raise ValueError("Must include 'return' annotations.")

    property_type = f.__annotations__['return']
    description = f.__doc__

    schema = create_schema(
        property_type, description=format_description(description),
        read_only=read_only, example=example,
        # If a custom object is found here, then it
        # should only be referenced.
        is_reference=True
    )

    return schema


def inject_component(cls):
    """'Inject' the `Component` class into the custom, user defined,
    soon-to-be Component, class.

    This will help when building a property that involves a user defined
    custom Component.
    """
    if issubclass(cls, Component):
        return cls
    else:
        # @functools.wraps(cls, updated=())
        # class Injected(cls, Component):
        #     pass
        injected = type(
            "Injected",
            (cls, Component),
            {attr_name: attr for attr_name, attr in cls.__dict__.items()}
        )
        injected.__qualname__ = f'Component[{cls.__name__}]'
        # Make sure not to override name, because it will be
        # used in the conversion to an Open API object, e.g.
        # {__name__: <rest of properties>}.
        injected.__name__ = cls.__name__

        return injected


ContentSchema = Optional[
    Union[
        Dict[MediaTypeEnum, MediaTypeObject],
        Dict[str, Dict[str, Any]]
    ]
]


def build_mediatype_schema_from_content(
        content: Optional[List[Union[MediaType, Iterable]]],
        # Allow validating once; by returning a dict,
        # other side can use `construct` for quicker
        # build time.
        as_dict=False
) -> ContentSchema:
    if content is None:
        return
    content_schema = {}
    for media_type, field_type, example, examples, encoding in content:
        # Note, only bare-bones or references allowed, such as
        # Int64, Array[~], ref->Objects.
        schema = create_schema(field_type)  # validated schema
        media_type = MediaTypeEnum(media_type)
        media_object = MediaTypeObject(
            schema=schema, example=example, examples=examples,
            encoding=encoding
        )

        if as_dict:
            media_object = media_object.dict()

        content_schema[media_type] = media_object

    return content_schema
