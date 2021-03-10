from typing import Optional, Dict, List, Tuple, Any, Union, Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


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

    # TODO use_enum_values

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


SchemaT = TypeVar("SchemaT")


class SchemaMapping(GenericModel, Generic[SchemaT]):

    schema_field: SchemaT = Field(..., alias='schema')

    def dict(self, *args, by_alias=True, **kwargs):
        """Return alias by default."""
        print(self)
        return super().dict(*args, by_alias=by_alias, **kwargs)


class RequestBodySchema(GenericModel, Generic[SchemaT]):
    """Serialized Request Body Object.
    """

    class Config:
        arbitrary_types_allowed = True

    description: Optional[str]
    content: Optional[Dict[MediaType, SchemaMapping[SchemaT]]]
    required: bool = False


class ParamSchema(SchemaMapping[Schema]):

    name: str
    # alias will be returned by default.
    # See `SchemaMapping`.
    in_field: str = Field(..., alias='in')
    description: Optional[str]
    required: bool = False


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

