from unittest import mock

from pyopenapi3.objects import (
    TextPlainMediaType,
    JSONMediaType,
)
from pyopenapi3.data_types import (
    Email,
    Int64,
    String,
    Component,
    Array
)
from pyopenapi3.schemas import (
    MediaTypeObject,
    Int64DTSchema,
    EmailDTSchema,
    ReferenceObject,
    ArrayDTSchema,
    AnyTypeArrayDTSchema,
    MixedTypeArrayDTSchema
)
from pyopenapi3.types import MediaTypeEnum
from pyopenapi3.utils import (
    build_mediatype_schema_from_content,
    convert_primitive_to_schema,
    convert_objects_to_schema,
    convert_array_to_schema,
    create_schema,
    parse_name_and_type_from_fmt_str
)


def test_build_mediatype_from_object__success():
    class Customer(Component):  # Test custom components.
        ...

    text = TextPlainMediaType(String)
    json = JSONMediaType(Customer)

    b = build_mediatype_schema_from_content([text, json])

    should_be = {
        MediaTypeEnum.JSON: MediaTypeObject(
            schema={'ref': '#/components/schemas/Customer'}),
        MediaTypeEnum.PLAIN: MediaTypeObject(
            schema={'type': 'string'})
    }

    assert b == should_be


def test_build_mediatype_from_tuples__success():
    content = [
        (MediaTypeEnum.PNG, Int64, None, None, None),
        (MediaTypeEnum.JSON, String, None, None, None),
        (MediaTypeEnum.PLAIN, Email, None, None, None)
    ]

    b = build_mediatype_schema_from_content(content)

    should_be = {
        MediaTypeEnum.PNG: MediaTypeObject(
            schema={'type': 'integer', 'format': 'int64'}),
        MediaTypeEnum.JSON: MediaTypeObject(
            schema={'type': 'string'}),
        MediaTypeEnum.PLAIN: MediaTypeObject(
            schema={'type': 'string', 'format': 'email'})
    }

    assert b == should_be


def test_convert_primitive_to_schema():
    p = convert_primitive_to_schema(Int64)
    assert p == Int64DTSchema()


def test_convert_objects_to_schema():

    class Pet(Component):
        ...

    r = convert_objects_to_schema(Pet)

    assert r == ReferenceObject(ref='#/components/schemas/Pet')


def test_array_to_schema():
    kwargs = {'min_length': 1, 'max_length': 10}

    arb_array = convert_array_to_schema(Array[...], **kwargs)
    assert arb_array == AnyTypeArrayDTSchema(**kwargs)

    single_array = convert_array_to_schema(Array[Int64], **kwargs)
    assert single_array == ArrayDTSchema(
        items={'type': 'integer', 'format': 'int64'},
        **kwargs
    )

    mixed_array = convert_array_to_schema(Array[Int64, Email], **kwargs)
    assert mixed_array == MixedTypeArrayDTSchema(
        items={'oneOf': [
            {'type': 'integer', 'format': 'int64'},
            {'type': 'string', 'format': 'email'}
        ]},
        **kwargs
    )


@mock.patch('pyopenapi3.utils.convert_array_to_schema')
@mock.patch('pyopenapi3.utils.convert_primitive_to_schema')
@mock.patch('pyopenapi3.utils.convert_objects_to_schema')
def test_create_schema(
        mock_objects_to_schema,
        mock_prim_to_schema,
        mock_arr_to_schema
):
    kwargs = {'a': 1, 'b': 2}

    # objects to schema
    class Customer(Component):
        ...

    create_schema(Customer, **kwargs)
    # create_schema will only create references for custom components,
    # so kwargs should not be passed to it.
    mock_objects_to_schema.assert_called_once_with(Customer)

    # primitive to schema
    create_schema(Int64, **kwargs)
    mock_prim_to_schema.assert_called_once_with(Int64, **kwargs)

    # array to schema
    arr = Array[Int64, Email, Customer]
    create_schema(arr, **kwargs)
    mock_arr_to_schema.assert_called_once_with(arr, **kwargs)


def test_parse_name_and_type():
    fmt_str = "{id:Int64}/{email:Email}/"

    parsed_gen = parse_name_and_type_from_fmt_str(fmt_str)

    _id = next(parsed_gen)
    assert _id == ("id", Int64)

    email = next(parsed_gen)
    assert email == ("email", Email)
