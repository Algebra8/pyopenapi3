from typing import Optional, Dict, List, Any, Union, Generic, TypeVar
from string import Formatter

from pydantic import (
    BaseModel,
    Field,
    AnyUrl,
    EmailStr,
    validator,
    ValidationError
)
from pydantic.generics import GenericModel

from .types import VariableAnyUrl


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


# TODO ReferenceObject
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

    # The default value to use for substitution, which SHALL
    # be sent if an alternate value is not supplied.
    default: str
    # An enumeration of string values to be used if the
    # substitution options are from a limited set.
    enum: Optional[List[str]]
    # An optional description for the server variable.
    description: Optional[str]


class ServerSchema(Schema):
    """Serialized Server Object.
    """

    # A URL to the target host.
    url: Optional[VariableAnyUrl]
    # An optional string describing the host designated by the URL.
    description: Optional[str]
    # A map between a variable name and its value.
    variables: Optional[Dict[str, ServerVariableSchema]]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'url' in d:
            d['url'] = str(d['url'])
        return d

    @validator('variables')
    def validate_url_with_vars(cls, v, values, **kwargs):
        """
        Validate that any, and only any, variables defined in `url`
        are present in `variables`.

        E.g.,
            If the url is
            "https://{username}.gigantic-server.com:{port}/{basePath}"
            then the variables should look like
            {'username': ..., 'port': ..., 'basePath': ...}.

        """
        _url = str(values['url'])
        args = [a for _, a, _, _, in Formatter().parse(_url)]
        if (
                not all([var in v for var in args])
                or len(v) > len(args)
        ):
            raise ValueError(
                "Any, and only any, variable defined in the url "
                "must exist in `variables`. Please refer to "
                "https://swagger.io/specification/#server-object."
            )
        return v


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


# TODO RequestBodyObject
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

# TODO ParameterObject
class ParamSchema(SchemaMapping[FieldSchemaT]):

    name: str
    # alias will be returned by default.
    # See `SchemaMapping`.
    in_field: str = Field(..., alias='in')
    description: Optional[str]
    required: bool = False


# TODO ExternalDocObject
class ExternalDocObject(Schema):
    ...


# TODO SecurityReqObject
class SecurityReqObject(Schema):
    ...


class CallbackObject(Schema):
    ...


class OperationObject(Schema):
    """Schema for an Operation Object.

    Describes a single API operation on a path. Based on spec
    described in https://swagger.io/specification/#operation-object.
    """

    # A list of tags for API documentation control.
    tags: Optional[List[str]]

    # 	A short summary of what the operation does.
    summary: Optional[str]

    # A verbose explanation of the operation behavior.
    description: Optional[str]

    # Additional external documentation for this operation.
    external_docs: Optional[
        ExternalDocObject
    ] = Field(None, alias="externalDocs")

    # Unique string used to identify the operation.
    # TODO Computational?
    operation_id: Optional[str] = Field(None, alias="operationId")

    # A list of parameters that are applicable for this operation.
    parameters: Optional[List[Union[ParamSchema, ReferenceSchema]]]

    # The list of possible responses as they are returned from
    # executing this operation.
    responses: Dict[str, ResponseSchema]

    # The request body applicable for this operation.
    request_body: Optional[
        Union[RequestBodySchema, ReferenceSchema]
    ] = Field(None, alias="requestBody")

    # A map of possible out-of band callbacks related to the
    # parent operation.
    callbacks: Optional[Dict[str, Union[CallbackObject, ReferenceSchema]]]

    # Declares this operation to be deprecated.
    deprecated: Optional[bool]

    # A declaration of which security mechanisms can be used
    # for this operation.
    security: List[SecurityReqObject]

    # An alternative server array to service this operation.
    servers: Optional[List[ServerSchema]]


class PathItemObject(Schema):
    """Schema for a Path Item Object.

    Describes the operations available on a single path. Based
    on spec described in https://swagger.io/specification/#path-item-object.

    A Path Item MAY be empty, due to ACL constraints.
    The path itself is still exposed to the documentation viewer
    but they will not know which operations and parameters are
    available.
    """

    # Allows for an external definition of this path item.
    ref: Optional[str] = Field(None, alias="$ref")

    # An optional, string summary, intended to apply to all
    # operations in this path.
    summary: Optional[str]

    # An optional, string description, intended to apply to
    # all operations in this path.
    description: Optional[str]

    # A definition of a GET operation on this path.
    get:        Optional[OperationObject]

    # A definition of a POST operation on this path.
    post:       Optional[OperationObject]

    # A definition of a PUT operation on this path.
    put:        Optional[OperationObject]

    # A definition of a PATCH operation on this path.
    patch:      Optional[OperationObject]

    # A definition of a DELETE operation on this path.
    delete:     Optional[OperationObject]

    # A definition of a HEAD operation on this path.
    head:       Optional[OperationObject]

    # A definition of a OPTIONS operation on this path.
    options:    Optional[OperationObject]

    # A definition of a TRACE operation on this path.
    trace:      Optional[OperationObject]

    # An alternative server array to service all operations
    # in this path.
    servers: Optional[List[ServerSchema]]

    # A list of parameters that are applicable for all the
    # operations described under this path.
    parameters: Optional[List[Union[ParamSchema, ReferenceSchema]]]


class PathObject(Schema):
    """Schema for a Path Object.

    Holds the relative paths to the individual endpoints and
    their operations. Based on spec described in
    https://swagger.io/specification/#paths-object.

    The path is appended to the URL from the Server Object in order
    to construct the full URL. The Paths MAY be empty, due to ACL
    constraints.
    """

    # A relative path to an individual endpoint.
    paths: Dict[str, PathItemObject]

