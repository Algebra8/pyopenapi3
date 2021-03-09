from typing import Optional, Any, Union, Dict, Type, Tuple, cast
import inspect
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
    Component
)
import pyopenapi3.objects  # Used to get a class from a name.
from .typedefs import (
    OpenApiSchema,
    ObjectSchema,
    # PrimitiveSchema,
    # ArraySchema,
    OpenApiObject
)
from .schemas import (
    ArraySchema,
    ComponentSchema,
    ReferenceSchema,
    PrimitiveSchema,
    Schema
)
from ._yaml import Ref


OPENAPI_DEF = '__OPENAPIDEF__'


# Helper for formating descriptions.
def _format_description(s: Optional[str]) -> Optional[str]:
    # TODO what if s is None...
    if s is None:
        return
    s = s.strip()
    s = s.replace("\n", "")
    s = s.replace("\t", "")
    return " ".join(s.split())


# Helper for issubclass so it won't break
# every time a non-class is checked.
def _issubclass(c1, c2):
    if inspect.isclass(c1):
        return issubclass(c1, c2)
    return False


def get_name_and_type(formatted_str):
    """
    Parse a formatted string and return the names
    of the args and their types.

    E.g. "/user/{id:int}" -> ("id", "int")
    """
    for _, arg_name, _type_name, _ in Formatter().parse(formatted_str):
        try:
            yield arg_name, _get_field_from_name(_type_name)
        except AttributeError:
            raise ValueError(
                "A non-`Field` or `OpenApiObject` type was found. "
                f"Can't use `{_type_name}` as a type in {formatted_str}."
            ) from None


def _get_field_from_name(name):
    """Get the Field type from a given name.

    E.g. "Int64" -> <class 'pyopenapi3.fields.Int64'>
    """
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


# def create_schema(
#         schema_type: Union[Type[Field], OpenApiObject],
#         # If `schema_type` is some subclass of `OpenApiObject`,
#         # then we might want to just return a reference to the
#         # object.
#         reference_only: bool = False
# ) -> Any:
#     if _issubclass(schema_type, OpenApiObject):
#         if reference_only:
#             return create_reference(schema_type.__name__)
#         else:
#             return create_object(schema_type, descr=schema_type.__doc__)
#     else:
#         return convert_type_to_schema(schema_type, descr=None,
#                                       read_only=False, example=None)


def create_object(
        _cls, *, descr: Optional[str]
) -> ObjectSchema:
    """Convert a Python class to an OpenAPI format.

    The entrypoint for conversion.
    """
    schema = ObjectSchema(
        type='object',
        description=descr,
        properties={}
    )

    for attr in _cls.__dict__.values():
        if hasattr(attr, OPENAPI_DEF):
            prop_data = getattr(attr, OPENAPI_DEF)
            schema['properties'].update(prop_data)

    return schema


# TODO change name from PropertyObject to SchemaObject


def create_primitive(
        primitive, *,
        descr: Optional[str],
        read_only: bool,
        example: Optional[Any]
) -> PrimitiveSchema:
    """Build an Open API 3.0.0 primitive schema.
    """
    # TODO change parse_attr name to something more
    #  informative like parse_primitive.
    schema = PrimitiveSchema(**parse_attr(primitive))
    if descr is not None:
        schema['description'] = descr
    if read_only:
        # This may seem redundant but we do not want to
        # clutter the OpenAPI definition with 'readOnly = false'.
        # So doing something like `propdata['readOnly']
        # = read_only` in the outer scope is not an option.
        schema['readOnly'] = True
    if example is not None:
        schema['example'] = example
    return schema


def create_reference(name: str) -> ReferenceSchema:
    return ReferenceSchema(ref=f"#/components/schemas/{name}")


def create_array(arr: Array) -> ArraySchema:
    """Build an Open API 3.0.0 array schema.
    """
    schema = ArraySchema(type='array', items={})

    def _assign_type(__type):
        return (
            parse_attr(__type) if _issubclass(__type, Field)
            else create_reference(__type.__name__)
        )

    if len(arr) == 1:
        # The array only holds one type: could be
        # a specific schema or arbitrary types (aka ...).
        if is_arb_type(arr[0]):
            return schema
        schema['items'] = _assign_type(arr[0])
    else:
        # The array is a "mixed-type array",
        # e.g. ["foo", 5, -2, "bar"]
        schema['items'] = {'oneOf': []}
        for _type in arr:
            schema['items']['oneOf'].append(
                _assign_type(_type)
            )

    return schema


def convert_type_to_schema(
        __type, *,
        descr: Optional[str],
        read_only: bool,
        example: Optional[Any]
) -> Union[PrimitiveSchema, ArraySchema]:
    """Flow controller for the type to schema conversion.

    Will differentiate between an Array or Primitive and return
    the correct schema.
    """
    schema: Dict[str, OpenApiSchema]

    # Array.__class_getitem__ will return an instance of
    # an Array object, so using issubclass will break and
    # using _issubclass will miss the mark.
    if isinstance(__type, Array) or issubclass(__type, Field):
        if isinstance(__type, Array):
            schema = create_array(__type)
        else:
            # Primitive type.
            schema = create_primitive(
                __type, descr=descr,
                read_only=read_only, example=example
            )
    else:
        raise ValueError("Not a valid field.")

    return schema


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
        return convert_component_to_schema(__type, is_reference)


def convert_component_to_schema(
        component: Type[Component],
        is_reference: bool
) -> ComponentSchema:
    assert is_reference is not None
    if is_reference:
        return create_reference(component.__name__)
    else:
        return ComponentSchema("")


def convert_primitive_to_schema(
        primitive: Type[Primitive], *,
        description: Optional[str],
        read_only: bool,
        example: Optional[Any]
) -> PrimitiveSchema:
    schema = PrimitiveSchema(**parse_attr(primitive))
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
        Union[
            Type[Component],
            Type[Field]
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

