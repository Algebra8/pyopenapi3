from pyopenapi3.objects import (
    TextPlainMediaType,
    JSONMediaType,
    Email,
    Int64,
    String,
    Component
)
from pyopenapi3.schemas import MediaTypeObject
from pyopenapi3.types import MediaTypeEnum
from pyopenapi3.utils import build_mediatype_schema_from_content


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




