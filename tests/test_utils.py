
from pyopenapi3.objects import (
    TextPlainMediaType,
    JSONMediaType,
    Email,
    Int64,
    String,
    Component
)
from pyopenapi3.types import MediaTypeEnum
from pyopenapi3.utils import build_mediatype_schema_from_content


def test_build_mediatype_from_object__success():
    class Customer(Component):
        ...

    text = TextPlainMediaType(String)
    json = JSONMediaType(Customer)

    b = build_mediatype_schema_from_content([text, json])

    assert b == {
        MediaTypeEnum.JSON: {
            'schema': {'$ref': '#/components/schemas/Customer'}},
        MediaTypeEnum.PNG: {
            'schema': {'type': 'integer', 'format': 'int64'}}
    }




