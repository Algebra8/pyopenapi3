from typing import Optional, Any, Union, Dict
import inspect

from .fields import (
    Number,
    String,
    Boolean,
    Integer,
    Array,
    Field,
    is_arb_type
)
from .typedefs import (
    OpenApiSchema,
    ObjectSchema,
    PrimitiveSchema,
    ArraySchema
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


def create_reference(name, path: str = "#/components/schemas") -> Ref:
    return Ref((path, name))


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
