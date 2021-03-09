from typing import Optional, Dict, List, Tuple, Any, Union

from pydantic import BaseModel


class Schema(BaseModel):

    def dict(self, *, exclude_none=True, **kwargs):
        """Make default `dict` method exclude `None`s by default."""
        return super().dict(exclude_none=exclude_none, **kwargs)


# Field Schemas
class PrimitiveSchema(Schema):

    type: str
    format: Optional[str]
    description: Optional[str]
    readOnly: Optional[bool]
    example: Optional[Any]


class ArraySchema(Schema):

    class Config:
        arbitrary_types_allowed = True

    type: str
    items: Dict[
        str,
        Union[str, Dict[str, Schema], List[Schema]]
    ]


class ComponentSchema(Schema):

    type: str = 'object'
    description: Optional[str]
    properties: Dict[str, Any] = {}


class ReferenceSchema(Schema):

    ref: str

    def dict(self, *args, **kwargs):
        """Return $ref as key for reference."""
        d = super().dict(*args, **kwargs)
        d["$ref"] = d["ref"]
        del d["ref"]
        return d


FieldSchema = Union[
    PrimitiveSchema,
    ArraySchema,
    ComponentSchema,
    ReferenceSchema
]


# Info metadata schemas.
class ContactObject(Schema):
    ...


class LicenseObject(Schema):
    ...


class InfoSchema(Schema):
    """Serialized Info Object.
    """

    title: str
    version: str
    description: Optional[str]
    terms_of_service: Optional[str]
    contact: Optional[ContactObject]
    license: Optional[LicenseObject]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'terms_of_service' in d:
            d['termsOfService'] = d['terms_of_service']
            del d['terms_of_service']
        return d


# Server schemas
class ServerVariableSchema(Schema):

    enum: Optional[List[str]]
    default: str
    description: Optional[str]


class ServerSchema(Schema):
    """Serialized Server Object.
    """

    url: str
    description: Optional[str]
    # Not sure if Pydantic can handle typing.Mapping
    variables: Optional[Dict[str, ServerVariableSchema]]


# Path schemas
class MediaType(str):

    json = "application/json"
    xml = "application/xml"
    pdf = "application/pdf"
    url_encoded = "application/x-www-form-urlencoded"
    multipart = "multipart/form-data"
    plain = "text/plain; charset=utf-8"
    html = "text/html"
    png = "image/png"


class ResponseSchema(Schema):
    """Serialized Response Object.
    """

    class Config:
        arbitrary_types_allowed = True

    status: int
    description: Optional[str]
    content: Optional[List[Tuple[MediaType, Schema]]]


class MediaToFieldMappingSchema(Schema):

    schema: FieldSchema


class RequestBodySchema(Schema):
    """Serialized Request Body Object.
    """

    class Config:
        arbitrary_types_allowed = True

    description: Optional[str]
    # TODO Fix this type
    content: Optional[Dict[MediaType, MediaToFieldMappingSchema]]
    required: bool = False


class ParamSchema(Schema):

    name: str
    __in: str
    description: Optional[str]
    required: bool = False
    _schema: Schema

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)

        # __in -> in
        d['in'] = d['__in']
        del d['__in']

        # _schema -> schema
        d['schema'] = d['_schema']
        del d['_schema']

        return d


class HttpMethodSchema(Schema):

    tags: Optional[List[str]]
    summary: Optional[str]
    description: Optional[str]
    operation_id: Optional[str]
    parameters: Optional[List[ParamSchema]]
    # The str for `responses` are the status codes,
    # e.g. {'200': ResponseSchema()}
    responses: Dict[str, ResponseSchema]
    request_body: Optional[RequestBodySchema]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)

        if 'operation_id' in d:
            d['operationId'] = d['operation_id']
            del d['operation_id']

        if 'request_body' in d:
            d['requestBody'] = d['request_body']
            del d['request_body']
        return d


class HttpMethodMappingSchema(Schema):

    get:        Optional[HttpMethodSchema]
    post:       Optional[HttpMethodSchema]
    put:        Optional[HttpMethodSchema]
    patch:      Optional[HttpMethodSchema]
    delete:     Optional[HttpMethodSchema]
    head:       Optional[HttpMethodSchema]
    options:    Optional[HttpMethodSchema]
    trace:      Optional[HttpMethodSchema]


class PathMappingSchema(Schema):

    paths: Dict[str, HttpMethodMappingSchema]

