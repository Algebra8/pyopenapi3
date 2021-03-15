from typing import Optional, Dict, List, Any, Union, Generic, TypeVar
from string import Formatter
from enum import Enum

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
class ContactObject(Schema):
    """Schema for a Contact Object.

    Described in https://swagger.io/specification/#contact-object.
    """

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


class LicenseObject(Schema):
    """Schema for a License Object.

    License information for the exposed API, as described in
    https://swagger.io/specification/#license-object.
    """

    # The license name used for the API.
    name: str

    # A URL to the license used for the API.
    url: Optional[AnyUrl]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'url' in d:
            d['url'] = str(d['url'])
        return d


class InfoObject(Schema):
    """Schema for a Schema Object.

    The object provides metadata about the API, as described in
    https://swagger.io/specification/#info-object.
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
    contact: Optional[ContactObject]

    # The license information for the exposed API.
    license: Optional[LicenseObject]

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if 'termsOfService' in d:
            d['termsOfService'] = str(d['termsOfService'])
        return d


# Server schemas
class ServerVariableObject(Schema):
    """Schema for a Server Variable Object.

    An object representing a Server Variable for server URL template
    substitution, as described in
    https://swagger.io/specification/#server-variable-object.
    """

    # The default value to use for substitution, which SHALL
    # be sent if an alternate value is not supplied.
    default: str

    # An enumeration of string values to be used if the
    # substitution options are from a limited set.
    enum: Optional[List[str]]

    # An optional description for the server variable.
    description: Optional[str]


class ServerObject(Schema):
    """Schema for a Server Object.

    An object representing a Server, as described in
    https://swagger.io/specification/#server-object.
    """

    # A URL to the target host.
    url: Optional[VariableAnyUrl]

    # An optional string describing the host designated by the URL.
    description: Optional[str]

    # A map between a variable name and its value.
    variables: Optional[Dict[str, ServerVariableObject]]

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
class MediaType(str, Enum):

    JSON = "application/json"
    XML = "application/xml"
    PDF = "application/pdf"
    URL_ENCODED = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    PLAIN = "text/plain; charset=utf-8"
    HTML = "text/html"
    PNG = "image/png"


SchemaT = TypeVar("SchemaT", bound=Schema)
# TODO ComponentSchema is different from ReferenceSchema.
FieldSchemaT = TypeVar(
    "FieldSchemaT",
    PrimitiveSchema, ArraySchema
)


class ExampleObject(Schema):
    ...


class EncodingObject(Schema):
    ...


class DiscriminatorObject(Schema):

    ...


class XMLObject(Schema):

    ...


# TODO ExternalDocObject
class ExternalDocObject(Schema):
    ...


class LinkObject(Schema):
    ...


class HeaderObject(Schema):

    ...


class SchemaMapping(GenericModel, Generic[SchemaT], Schema):

    schema_field: SchemaT = Field(..., alias='schema')


class JsonSchemaDef(Schema):
    """Subset of JSON Schema Specification Wright Draft 00.

    Based on FastApi's OpenApi Models, SchemaBase.
    """

    title: Optional[str]
    multiple_of: Optional[float] = Field(None, alias='multipleOf')
    maximum: Optional[float]
    exclusive_maximum: Optional[float] = Field(None, alias='exclusiveMaximum')
    minimum: Optional[float]
    exclusive_minimum: Optional[float] = Field(None, alias='exclusiveMinimum')
    max_length: Optional[int] = Field(None, alias='maxLength', gte=0)
    min_length: Optional[int] = Field(None, alias='minLength', gte=0)
    pattern: Optional[str]
    max_items: Optional[int] = Field(None, alias='maxItems', gte=0)
    min_items: Optional[int] = Field(None, alias='minItems', gte=0)
    unique_items: Optional[bool] = Field(None, alias='uniqueItems')
    max_properties: Optional[int] = Field(None, alias='maxProperties', gte=0)
    min_properties: Optional[int] = Field(None, alias='minProperties', gte=0)
    required: Optional[List[str]]
    enum: Optional[List[Any]]


class OpenApiJsonSchemaDef(JsonSchemaDef):
    """
    Properties from JSON Schema definition with adjusted definitions
    for OpenAPI Specification.

    Based on FastApi's OpenApi Models, SchemaBase.
    """

    type: Optional[str]
    all_of: Optional[List[Any]] = Field(None, alias='allOf')
    one_of: Optional[List[Any]] = Field(None, alias='oneOf')
    any_of: Optional[List[Any]] = Field(None, alias='anyOf')
    not_: Optional[Any] = Field(None, alias="not")
    items: Optional[Any]
    properties: Optional[Dict[str, Any]]
    additional_properties: Optional[
        Union[Dict[str, Any], bool]
    ] = Field(None, alias='additionalProperties')
    description: Optional[str]
    format: Optional[str]
    default: Optional[Any]


class SchemaObject(OpenApiJsonSchemaDef):
    """Schema for a Schema Object.

    The Schema Object allows the definition of input and output data
    types, as described in https://swagger.io/specification/#schema-object.

    These types can be objects, but also primitives and arrays.
    """

    # A true value adds "null" to the allowed type specified
    # by the type keyword, only if type is explicitly defined
    # within the same Schema Object.
    nullable: Optional[bool]

    # Adds support for polymorphism.
    discriminator: Optional[DiscriminatorObject]

    # Relevant only for Schema "properties" definitions.
    # Declares the property as "read only".
    read_only: Optional[bool] = Field(None, alias='readOnly')

    # Relevant only for Schema "properties" definitions.
    # Declares the property as "write only".
    write_only: Optional[bool] = Field(None, alias='writeOnly')

    # Adds additional metadata to describe the XML representation
    # of this property.
    xml: Optional[XMLObject]

    # Additional external documentation for this schema.
    external_docs: Optional[
        ExternalDocObject
    ] = Field(None, alias='externalDocs')

    # A free-form property to include an example of an instance
    # for this schema.
    example: Optional[Any]

    # Specifies that a schema is deprecated and SHOULD be
    # transitioned out of usage.
    deprecated: Optional[bool]

    # The next few properties are taken from FastApi.Models.Schema:
    # The idea is to allow recursive properties for the given fields.
    # So, we overwrite some of the previous OpenApiJsonSchemaDef to
    # include self type references.
    all_of: Optional[List[OpenApiJsonSchemaDef]] = Field(None, alias='allOf')
    one_of: Optional[List[OpenApiJsonSchemaDef]] = Field(None, alias='oneOf')
    any_of: Optional[List[OpenApiJsonSchemaDef]] = Field(None, alias='anyOf')
    not_: Optional[OpenApiJsonSchemaDef] = Field(None, alias="not")
    items: Optional[OpenApiJsonSchemaDef]
    properties: Optional[Dict[str, OpenApiJsonSchemaDef]]
    additional_properties: Optional[
        Union[Dict[str, OpenApiJsonSchemaDef], bool]
    ] = Field(None, alias='additionalProperties')


class MediaTypeObject(Schema):
    """Schema for a Media Type Object.

    Each Media Type Object provides schema and examples for the media
    type identified by its key, as described in
    https://swagger.io/specification/#media-type-object.
    """

    # The schema defining the content of the request, response,
    # or parameter.
    schema_field: Union[
        SchemaObject,
        ReferenceSchema
    ] = Field(..., alias='schema')

    # Example of the media type.
    example: Optional[Any]

    # Examples of the media type.
    examples: Optional[Dict[str, Union[ExampleObject, ReferenceSchema]]]

    # A map between a property name and its encoding information.
    encoding: Optional[Dict[str, EncodingObject]]


class ResponseObject(Schema):
    """Schema for a Response Object.

    Describes a single response from an API Operation, including
    design-time, static links to operations based on the response,
    as described in https://swagger.io/specification/#response-object.
    """

    class Config:

        arbitrary_types_allowed = True
        use_enum_values = True

    # A short description of the response.
    description: str

    # Maps a header name to its definition.
    headers: Optional[Dict[str, Union[HeaderObject, ReferenceSchema]]]

    # A map containing descriptions of potential response payloads.
    # The key is a media type or media type range and the value
    # describes it.
    content: Optional[Dict[MediaType, SchemaMapping[Any]]]

    # A map of operations links that can be followed from the response.
    links: Optional[Dict[str, Union[LinkObject, ReferenceSchema]]]


class RequestBodyObject(Schema):
    """Schema for a Request Body Object.

    Describes a single request body, as described in
    https://swagger.io/specification/#request-body-object.
    """

    class Config:

        arbitrary_types_allowed = True
        use_enum_values = True

    # A brief description of the request body.
    description: Optional[str]

    # The content of the request body.
    content: Dict[MediaType, MediaTypeObject]

    # Determines if the request body is required in the request.
    required: Optional[bool]


class ParamLocation(str, Enum):

    PATH = 'path'
    QUERY = 'query'
    HEADER = 'header'
    COOKIE = 'cookie'


class ParameterObject(SchemaMapping[FieldSchemaT]):
    """Schema for a Parameter Object.

    Describes a single operation parameter, as described in
    https://swagger.io/specification/#parameter-object.

    A unique parameter is defined by a combination of a name and location.
    """

    class Config:

        use_enum_values = True

    # The name of the parameter.
    name: str

    # The location of the parameter.
    in_field: ParamLocation = Field(..., alias='in')

    # A brief description of the parameter.
    description: Optional[str]

    # Determines whether this parameter is mandatory.
    required: Optional[bool]

    # Specifies that a parameter is deprecated and SHOULD
    # be transitioned out of usage.
    deprecated: Optional[bool]

    # Sets the ability to pass empty-valued parameters.
    allow_empty_value: Optional[bool] = Field(None, alias='allowEmptyValue')


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
    parameters: Optional[List[Union[ParameterObject, ReferenceSchema]]]

    # The list of possible responses as they are returned from
    # executing this operation. This includes `default`.
    responses: Dict[str, ResponseObject]

    # The request body applicable for this operation.
    request_body: Optional[
        Union[RequestBodyObject, ReferenceSchema]
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

    # Taken from RFC7231:
    # https://tools.ietf.org/html/rfc7231#section-6
    _status_codes = range(100, 600)

    @validator('responses')
    def validate_response_mapping(cls, v):
        mut_v = {k: v for k, v in v.items()}
        mut_v.pop('default', None)
        for key in mut_v.keys():
            try:
                status_code = int(key)
            except ValueError:
                # Another non-digit key
                raise ValueError(
                    "The only non-digit key for a response "
                    f"must be 'default'. Can't include '{key}'"
                ) from None
            else:
                if status_code not in cls._status_codes:
                    raise ValueError(
                        "Only valid status codes allowed. Must be between "
                        f"100 and 511 (inclusive). Not {status_code}."
                    )

        return v


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
    parameters: Optional[List[Union[ParameterObject, ReferenceSchema]]]


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

