from __future__ import annotations

from typing import (
    Optional,
    Any,
    Union,
    Type,
    Tuple,
    cast,
    Dict,
    List,
    Generator,
    Iterable,
    TypeVar
)
from string import Formatter

from .objects import (
    OpenApiObject,
    MediaType
)
from .data_types import (
    Array,
    Field,
    Primitive,
    Component,
)
# Used to dynamically retrieve field in `parse_name_and_type
# _from_fmt_str`
import pyopenapi3.data_types
from .schemas import (
    Schema,
    StringDTSchema,
    ByteDTSchema,
    BinaryDTSchema,
    DateDTSchema,
    DateTimeDTSchema,
    PasswordDTSchema,
    IntegerDTSchema,
    Int32DTSchema,
    Int64DTSchema,
    NumberDTSchema,
    FloatDTSchema,
    DoubleDTSchema,
    EmailDTSchema,
    BoolDTSchema,
    ArrayDTSchema,
    ReferenceObject,
    PrimitiveDTSchema,
    DTSchema,
    MediaTypeEnum,
    AnyTypeArrayDTSchema,
    MixedTypeArrayDTSchema,
    MediaTypeObject,
    SchemaObject,
    ObjectsDTSchema
)


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

    # In-line Objects
    Object = ObjectsDTSchema

    def __call__(self, cls_or_name: Union[str, Type]) -> Type[DTSchema]:
        """Return the schema of a Data Type.

        Note that only non-complex data types are allowered here:
        cannot
        """
        if isinstance(cls_or_name, type):
            n = cls_or_name.__name__
        else:
            n = cls_or_name
        if hasattr(self, n):
            return getattr(self, n)
        raise ValueError(f"Could not find type {cls_or_name}")


ObjectToDTSchema = _ObjectToDTSchema()


# Helper for formating descriptions.
def format_description(s: Optional[str]) -> Optional[str]:
    # TODO what if s is None...
    if s is None:
        return None
    s = s.strip()
    s = s.replace("\n", "")
    s = s.replace("\t", "")
    return " ".join(s.split())


def parse_name_and_type_from_fmt_str(
        formatted_str: str,
        allowed_types: Optional[Dict[str, Component]] = None
) -> Generator[Tuple[str, Union[Type[Field], str]], None, None]:
    """
    Parse a formatted string and return the names of the args
    and their types. Will raise a ValueError if the type is not
    a pyopenapi3 `Field` or an already defined Component Parameter
    type.

    In the case that the type represents a `Field`, then its
    type will be returned, respectively. Otherwise, if it is an
    already defined Component Parameter, then the name of the
    class that defines the parameter will be returned.

    .. code:: none
        # E.g. 1

        "/user/{id:String}" -> ("id", pyopenapi3.data_types.String)

        # E.g. 2

        @open_bldr.component.parameter
        class PetId: ...

        "/pets/{pet:PetId}" -> ("pet", "PetId")

    If the string is not formatted, then will return (None, None).
    """
    for _, arg_name, _type_name, _ in Formatter().parse(formatted_str):
        if arg_name is not None:
            try:
                assert _type_name is not None
                _type = (
                    allowed_types[_type_name] if allowed_types is not None
                    and _type_name in allowed_types
                    else getattr(pyopenapi3.data_types, _type_name)
                )
                yield arg_name, _type
            except AttributeError:
                raise ValueError(
                    "A non-`Field` or `OpenApiObject` type was found. "
                    f"Can't use `{_type_name}` as a type in {formatted_str}. "
                    f"Must be a stringified pyopenapi3 `data_type`, such "
                    f"as `pyopenapi3.data_types.String`, or a reference to a "
                    f"Component."
                ) from None


def create_reference(
    name: str,
    component_dir: str = "schemas"
) -> ReferenceObject:
    return ReferenceObject(ref=f"#/components/{component_dir}/{name}")


def create_schema(
        __type: Type[OpenApiObject],
        **kwargs: Any
) -> Union[SchemaObject, ReferenceObject]:
    if isinstance(__type, Schema):
        # Case where a Schema is already defined, don't need
        # to recreate it.
        return __type
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
    """Convert a custom object to a schema.

    This is done by create a reference to the object. Any non-reference
    object should be created by the Components builder.

    param `obj` **must** be a subtype of `data_types.Component`. Its
    type will determine what kind of component it is, e.g. '#/components/
    schemas/...' or '#/components/parameters/...'.
    """
    cmp_type: str = 'schemas'  # default component type
    if hasattr(obj, '__cmp_type__'):
        cmp_type = obj.__cmp_type__.lower()  # type: ignore
    return create_reference(obj.__name__, cmp_type)


def convert_primitive_to_schema(
        primitive: Type[Primitive], **kwargs) -> PrimitiveDTSchema:
    return cast(PrimitiveDTSchema, ObjectToDTSchema(primitive)(**kwargs))


def convert_array_to_schema(
        array: Type[Array], **kwargs: Any) -> ArrayDTSchema:
    schema_type = cast(Type[ArrayDTSchema], ObjectToDTSchema(array))
    if schema_type is AnyTypeArrayDTSchema:
        return schema_type(**kwargs)
    else:
        sub_schemas: List[Union[ReferenceObject, SchemaObject]] = []
        assert array.tvars is not None
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


ComponentType = TypeVar('ComponentType', bound=Component)


def inject_component(cls, cmp_type: Type[ComponentType]):
    """'Inject' the `Component` class into the custom, user defined,
    soon-to-be Component, class.

    This will help when building a property that involves a user defined
    custom Component.

    param `cmp_type` is some subtype of `data_types.Component`, e.g.
    whether it is a Schema component or Parameter component.
    """
    if issubclass(cls, Component):
        return cls
    else:
        injected = type(
            "Injected",
            (cls, cmp_type),
            {attr_name: attr for attr_name, attr in cls.__dict__.items()}
        )
        injected.__qualname__ = f'Component[{cls.__name__}]'
        # Make sure not to override name, because it will be
        # used in the conversion to an Open API object, e.g.
        # {__name__: <rest of properties>}.
        injected.__name__ = cls.__name__
        injected.__cmp_type__ = cmp_type.__name__  # type: ignore

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
) -> Optional[ContentSchema]:
    if content is None:
        return None
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
