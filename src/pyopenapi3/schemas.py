from typing import Optional, Dict, List, Any, Union, Generic, TypeVar

from pydantic import BaseModel, Field, AnyUrl, EmailStr
from pydantic.generics import GenericModel


class Schema(BaseModel):

    class Config:

        allow_population_by_field_name = True

    def dict(self, *, exclude_none=True, by_alias=True, **kwargs):
        """Make `dict` exclude `None`s and use aliases by default."""
        return super().dict(
            exclude_none=exclude_none,
            by_alias=by_alias,
            **kwargs
        )


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

    ref: str = Field(..., alias="$ref")


FieldSchema = Union[
    PrimitiveSchema,
    ArraySchema,
    ComponentSchema,
    ReferenceSchema
]


# Info metadata schemas.
class ContactSchema(Schema):

    # The identifying name of the contact person/organization.
    name: Optional[str]
    # The URL pointing to the contact information.
    url: Optional[AnyUrl]
    # The email address of the contact person/organization.
    email: Optional[EmailStr]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'url' in d:
            d['url'] = str(d['url'])
        return d


class LicenseSchema(Schema):

    # The license name used for the API.
    name: str
    # A URL to the license used for the API.
    url: Optional[AnyUrl]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'url' in d:
            d['url'] = str(d['url'])
        return d


class InfoSchema(Schema):
    """Serialized Info Object.
    """

    # The title of the API.
    title: str
    # The version of the OpenAPI document.
    version: str
    # A short description of the API.
    description: Optional[str]
    # A URL to the Terms of Service for the API.
    terms_of_service: Optional[AnyUrl] = Field(None, alias="termsOfService")
    # The contact information for the exposed API.
    contact: Optional[ContactSchema]
    # The license information for the exposed API.
    license: Optional[LicenseSchema]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'termsOfService' in d:
            d['termsOfService'] = str(d['termsOfService'])
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


SchemaT = TypeVar("SchemaT", bound=Schema)
FieldSchemaT = TypeVar(
    "FieldSchemaT",
    PrimitiveSchema, ArraySchema,
    ComponentSchema, ReferenceSchema
)


class SchemaMapping(GenericModel, Generic[SchemaT], Schema):

    schema_field: SchemaT = Field(..., alias='schema')


class ResponseSchema(Schema):
    """Serialized Response Object.
    """

    class Config:

        arbitrary_types_allowed = True

    description: str
    # Needs to be Any: there can be variable number of
    # FieldSchemaT types, but we don't have variadic generics.
    # So, we use FieldSchemaT to validate the content's schema,
    # and use Any here to prevent Pydantic from arbitrarily
    # picking a schema belonging to some constraint in FieldSchemaT.
    content: Optional[Dict[MediaType, SchemaMapping[Any]]]


class RequestBodySchema(Schema):
    """Serialized Request Body Object.
    """

    class Config:

        arbitrary_types_allowed = True

    description: Optional[str]
    # See ResponseSchema.content above for why we use Any.
    content: Optional[Dict[MediaType, SchemaMapping[Any]]]
    required: bool = False
    # TODO add examples


class ParamSchema(SchemaMapping[FieldSchemaT]):

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
    operation_id: Optional[str] = Field(None, alias="operationId")
    parameters: Optional[List[ParamSchema]]
    # The str for `responses` are the status codes,
    # e.g. {'200': ResponseSchema()}
    responses: Dict[str, ResponseSchema]
    request_body: Optional[
        RequestBodySchema
    ] = Field(None, alias="requestBody")


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

    # Map a path to an HttpMethodMappingSchema,
    # e.g. {'/users': {'get': ..., 'post': ..., ...}}
    paths: Dict[str, HttpMethodMappingSchema]

