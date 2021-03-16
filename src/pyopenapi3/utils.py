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
    List
)
from string import Formatter

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
    Date, DateTime, Byte, Binary, Password
)
import pyopenapi3.objects  # Used to get a class from a name.
from .schemas import (
    StringDTSchema, ByteDTSchema, BinaryDTSchema, DateDTSchema,
    DateTimeDTSchema, PasswordDTSchema, IntegerDTSchema, Int32DTSchema,
    Int64DTSchema, NumberDTSchema, FloatDTSchema, DoubleDTSchema,
    EmailDTSchema,
    BoolDTSchema, ArrayDTSchema,
    ArraySchema,
    ComponentsObject,
    ReferenceObject,
    DTSchema,
    Schema,
    FieldSchemaT,
    SchemaMapping,
    MediaType
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

    def __call__(self, cls: Type):
        n = cls.__name__
        if hasattr(self, n):
            return getattr(self, n)


ObjectToDTSchema = _ObjectToDTSchema()


# Helper for formating descriptions.
def _format_description(s: Optional[str]) -> Optional[str]:
    # TODO what if s is None...
    if s is None:
        return
    s = s.strip()
    s = s.replace("\n", "")
    s = s.replace("\t", "")
    return " ".join(s.split())


def parse_name_and_type_from_fmt_str(
        formatted_str) -> Tuple[Optional[str]]:
    """
    Parse a formatted string and return the names
    of the args and their types.

    E.g. "/user/{id:int}" -> ("id", "int")

    If the string is not formatted, then will return (None, None).
    """
    for _, arg_name, _type_name, _ in Formatter().parse(formatted_str):
        if arg_name is not None:
            try:
                yield arg_name, _get_field_from_name(_type_name)
            except AttributeError:
                raise ValueError(
                    "A non-`Field` or `OpenApiObject` type was found. "
                    f"Can't use `{_type_name}` as a type in {formatted_str}."
                ) from None


def _get_field_from_name(name: Optional[str]) -> Optional[Type[Field]]:
    """Get the Field type from a given name.

    E.g. "Int64" -> <class 'pyopenapi3.fields.Int64'>
    """
    if name is not None:
        return getattr(pyopenapi3.objects, name)


# Field parsers.
def parse_attr(o):
    if issubclass(o, Number):
        return parse_numbers(o)
    elif issubclass(o, String):
        return parse_strings(o)
    elif o == Boolean:
        return {'type': 'boolean'}
    raise ValueError(f"Attr for {o} not defined.")


def parse_strings(s):
    if s == String:
        return {'type': 'string'}
    else:
        return {'type': 'string', 'format': s.__name__.lower()}


def parse_numbers(n):
    if n == Number:
        return {'type': 'number'}
    elif n == Integer:
        return {'type': 'integer'}
    elif issubclass(n, Number) and not issubclass(n, Integer):
        return {'type': 'number', 'format': n.__name__.lower()}
    elif issubclass(n, Integer):
        return {'type': 'integer', 'format': n.__name__.lower()}


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
        is_reference: Optional[bool] = None,
        description: Optional[str] = None,
        read_only: Optional[bool] = None,
        example: Optional[Any] = None,
        **kwargs
) -> Schema:
    if issubclass(__type, Primitive):
        return convert_primitive_to_schema(
            __type, description=description,
            read_only=read_only, example=example
        )
    if issubclass(__type, Array):
        return convert_array_to_schema(__type)
    if issubclass(__type, Component):
        assert is_reference is not None
        return convert_component_to_schema(
            __type, description=description,
            is_reference=is_reference
        )


def convert_component_to_schema(
        component: Type[Component],
        description: Optional[str],
        is_reference: bool
) -> Union[ComponentsObject, ReferenceObject]:
    assert is_reference is not None
    if is_reference:
        return create_reference(component.__name__)
    else:
        return _convert_component_to_schema(component, description=description)


def _convert_component_to_schema(
        component: Type[Component],
        description: Optional[str]
) -> ComponentsObject:
    """Convert non-reference Component object."""
    schema = ComponentsObject(description=description)
    for attr in component.__dict__.values():
        if hasattr(attr, OPENAPI_DEF):
            property_schema: Union[
                _PrimitiveDTSchema,
                ComponentsObject,
                ReferenceObject,
                ArraySchema
            ] = getattr(attr, OPENAPI_DEF)
            # Don't need to `.dict()` these because
            # top-level `.dict()` called on `schema`
            # will recursively convert them.
            schema.properties.update(property_schema)
    return schema


def convert_primitive_to_schema(
        primitive: Type[Primitive], *,
        description: Optional[str],
        read_only: bool,
        example: Optional[Any]
) -> _PrimitiveDTSchema:
    schema = _PrimitiveDTSchema(**parse_attr(primitive))
    if description is not None:
        schema.description = description
    if read_only:
        # This may seem redundant but we do not want to
        # clutter the OpenAPI definition with 'readOnly = false'.
        # So, only set `readOnly` if it is True.
        schema.readOnly = True
    if example is not None:
        schema.example = example
    return schema


def convert_array_to_schema(array: Type[Array]) -> ArraySchema:
    """Convert a concrete array type to an ArraySchema."""
    schema = ArraySchema(type='array', items={})

    # The types contained in the Array:
    # Array[int, str] -> tvars = (int, str)
    tvars: Tuple[
        Type[
            Union[Component, Field]
        ]
    ] = array.tvars
    if len(tvars) == 1:
        # The array only holds one type: could be
        # a specific schema or arbitrary types (aka ...).
        if is_arb_type(tvars[0]):
            return schema
        schema.items = create_schema(
            cast(Type[OpenApiObject], tvars[0]),
            # In case it is a custom object,
            # only pass in a reference
            is_reference=True
        )
    else:
        # The array is a "mixed-type array",
        # e.g. ["foo", 5, -2, "bar"]
        schema.items = {'oneOf': []}
        for t in tvars:
            schema.items['oneOf'].append(
                create_schema(
                    cast(Type[OpenApiObject], t),
                    # As mentioned above, in the case that
                    # it is a custom object, only return a
                    # reference.
                    if_reference=True
                )
            )
    return schema


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
        property_type, description=_format_description(description),
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


def map_field_to_schema(
        field_type, is_reference: bool = False) -> Type[FieldSchemaT]:
    if issubclass(field_type, Primitive):
        return _PrimitiveDTSchema
    elif issubclass(field_type, Array):
        return ArraySchema
    elif issubclass(field_type, Component):
        if is_reference:
            return ReferenceObject
        return ComponentsObject
    else:
        raise ValueError(
            "Must provide a `Field` or custom component."
        )


ContentSchema = Optional[Dict[MediaType, SchemaMapping[FieldSchemaT]]]


def build_content_schema_from_content(
        content: List[Tuple[str, Any]]) -> ContentSchema:
    if content is None:
        return
    content_schema = {}
    for media_type, field_type in content:
        field_schema_tp = map_field_to_schema(
            field_type, is_reference=True
        )
        media_type = cast(MediaType, media_type)
        schema = cast(
            Type[FieldSchemaT],
            create_schema(field_type, is_reference=True)
        )
        content_schema[media_type] = \
            SchemaMapping[field_schema_tp](schema=schema)

    return content_schema


