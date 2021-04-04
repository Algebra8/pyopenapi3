from __future__ import annotations

from typing import Optional, Dict, List, Any, Union, Sequence, Mapping
from string import Formatter
from enum import Enum

from pathlib import Path

from pydantic import (  # type: ignore
    BaseModel,
    Field,
    AnyUrl,
    EmailStr,
    validator,
    root_validator
)

from .types import VariableAnyUrl, MediaTypeEnum


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

    def json(self, *, exclude_none=True, by_alias=True, **kwargs):
        return super().json(
            exclude_none=exclude_none,
            by_alias=by_alias,
            **kwargs
        )


class JsonSchemaDef(Schema):
    """Subset of JSON Schema Specification Wright Draft 00.

    Based on FastApi's OpenApi Models, SchemaBase.
    """

    ref: Optional[str] = Field(None, alias="$ref")
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
    one_of: Optional[Sequence[Any]] = Field(None, alias='oneOf')
    any_of: Optional[List[Any]] = Field(None, alias='anyOf')
    not_: Optional[Any] = Field(None, alias="not")
    items: Optional[Any]
    properties: Optional[Mapping[str, Any]]
    additional_properties: Optional[
        Union[Dict[str, Any], bool]
    ] = Field(None, alias='additionalProperties')
    description: Optional[str]
    format: Optional[str]
    default: Optional[Any]


class ReferenceObject(OpenApiJsonSchemaDef):

    ref: str = Field(..., alias="$ref")


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
    discriminator: Optional[DiscriminatorObject] = None

    # Relevant only for Schema "properties" definitions.
    # Declares the property as "read only".
    read_only: Optional[bool] = Field(None, alias='readOnly')

    # Relevant only for Schema "properties" definitions.
    # Declares the property as "write only".
    write_only: Optional[bool] = Field(None, alias='writeOnly')

    # Adds additional metadata to describe the XML representation
    # of this property.
    xml: Optional[XMLObject] = None

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
    one_of: Optional[
        Sequence[OpenApiJsonSchemaDef]
    ] = Field(None, alias='oneOf')
    any_of: Optional[List[OpenApiJsonSchemaDef]] = Field(None, alias='anyOf')
    not_: Optional[OpenApiJsonSchemaDef] = Field(None, alias="not")
    items: Optional[OpenApiJsonSchemaDef]
    properties: Optional[Mapping[str, OpenApiJsonSchemaDef]]
    additional_properties: Optional[
        Union[Dict[str, OpenApiJsonSchemaDef], bool]
    ] = Field(None, alias='additionalProperties')

    # Make Reference Object distinct from a Schema Object.
    ref: Optional[str] = Field(None, alias="$ref", const=True)


# Data Types
class DTSchema(SchemaObject):

    ...


class ObjectsDTSchema(DTSchema):

    type: str = Field('object', const=True)

    # Optional to allow Free-Form objects. See issue-82.
    properties: Optional[Dict[str, Union[ReferenceObject, SchemaObject]]]


class PrimitiveDTSchema(DTSchema):
    ...


class StringDTSchema(PrimitiveDTSchema):

    type: str = Field("string", const=True)
    format: Optional[str] = Field(None, const=True)


class ByteDTSchema(StringDTSchema):

    format: str = Field("byte", const=True)


class BinaryDTSchema(StringDTSchema):

    format: str = Field("binary", const=True)


class DateDTSchema(StringDTSchema):

    format: str = Field("data", const=True)


class DateTimeDTSchema(StringDTSchema):

    format: str = Field("date-time", const=True)


class PasswordDTSchema(StringDTSchema):

    format: str = Field("password", const=True)


class EmailDTSchema(StringDTSchema):

    format: str = Field("email", const=True)


class IntegerDTSchema(PrimitiveDTSchema):

    type: str = Field("integer", const=True)
    format: Optional[str] = Field(None, const=True)


class Int32DTSchema(IntegerDTSchema):

    format: str = Field("int32", const=True)


class Int64DTSchema(IntegerDTSchema):

    format: str = Field("int64", const=True)


class NumberDTSchema(PrimitiveDTSchema):

    type: str = Field("number", const=True)
    format: Optional[str] = Field(None, const=True)


class FloatDTSchema(NumberDTSchema):

    format: str = Field("float", const=True)


class DoubleDTSchema(NumberDTSchema):

    format: str = Field("double", const=True)


class BoolDTSchema(PrimitiveDTSchema):

    type: str = Field('boolean', const=True)
    format: Optional[str] = Field(None, const=True)


class ArrayDTSchema(DTSchema):

    type: str = Field("array", const=True)
    items: Union[ReferenceObject, SchemaObject]


class AnyTypeArrayDTSchema(ArrayDTSchema):

    items: Union[ReferenceObject, SchemaObject] = Field({}, const=True)


class _OneOf(SchemaObject):

    one_of: List[
        Union[ReferenceObject, SchemaObject]
    ] = Field(..., alias='oneOf')


class MixedTypeArrayDTSchema(ArrayDTSchema):

    items: _OneOf


class SecuritySchemeObject(Schema):
    ...


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
    url: Optional[Union[VariableAnyUrl, Path]]  # Path allows '/' for default

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


class ExampleObject(Schema):
    """Schema for an Example Object.

    Described in https://swagger.io/specification/#example-object.
    """

    # Short description for the example.
    summary: Optional[str]

    # Long description for the example.
    description: Optional[str]

    # Embedded literal example.
    value: Any

    # A URL that points to the literal example.
    external_value: Optional[AnyUrl] = Field(None, alias='externalValue')


class EncodingObject(Schema):
    """Schema for an Encoding Object.

    A single encoding definition applied to a single schema property.
    Described in https://swagger.io/specification/#encoding-object.
    """

    # The Content-Type for encoding a specific property.
    content_type: Optional[str] = Field(None, alias='contentType')

    # A map allowing additional information to be provided as headers.
    headers: Optional[Dict[str, Union[HeaderObject, ReferenceObject]]]

    # Describes how a specific property value will be serialized
    # depending on its type.
    style: Optional[str]

    # When this is true, property values of type array or object
    # generate separate parameters for each value of the array,
    # or key-value-pair of the map.
    explode: Optional[bool]

    # Determines whether the parameter value SHOULD allow reserved
    # characters, as defined by RFC3986 :/?#[]@!$&'()*+,;= to be
    # included without percent-encoding.
    allow_reserved: Optional[bool] = Field(None, alias='allowReserved')


class DiscriminatorObject(Schema):
    """Schema for a Discriminator Object.

    When request bodies or response payloads may be one of a number
    of different schemas, a discriminator object can be used to aid
    in serialization, deserialization, and validation. Described
    in https://swagger.io/specification/#discriminator-object.
    """

    # The name of the property in the payload that will hold
    # the discriminator value.
    property_name: str = Field(..., alias='propertyName')

    # An object to hold mappings between payload values and
    # schema names or references.
    mapping: Optional[Dict[str, str]]


class XMLObject(Schema):
    """Schema for an XML Object.

    A metadata object that allows for more fine-tuned XML model
    definitions. Described in https://swagger.io/specification/#xml-object.
    """

    # Replaces the name of the element/attribute used for the
    # described schema property.
    name: Optional[str]

    # The URI of the namespace definition.
    namespace: Optional[AnyUrl]

    # The prefix to be used for the name.
    prefix: Optional[str]

    # Declares whether the property definition translates to
    # an attribute instead of an element.
    attribute: Optional[bool]

    # MAY be used only for an array definition.
    wrapped: Optional[bool]


class ExternalDocObject(Schema):
    """Schema for an External Documentation Object.

    Allows referencing an external resource for extended documentation.
    Described in
    https://swagger.io/specification/#external-documentation-object.
    """
    # A short description of the target documentation.
    description: Optional[str]

    # The URL for the target documentation.
    url: AnyUrl


class LinkObject(Schema):
    """Schema for a Link Object.

    The Link object represents a possible design-time link for a response.
    Described in https://swagger.io/specification/#link-object.
    """

    # A relative or absolute URI reference to an OAS operation.
    operation_ref: Optional[str] = Field(None, alias='operationRef')

    # The name of an existing, resolvable OAS operation, as defined
    # with a unique operationId.
    operation_id: Optional[str] = Field(None, alias='operationId')

    # A map representing parameters to pass to an operation as
    # specified with operationId or identified via operationRef.
    parameters: Optional[Dict[str, Any]]

    # A literal value or {expression} to use as a request body when
    # calling the target operation.
    request_body: Optional[Any] = Field(None, alias='requestBody')

    # A description of the link.
    description: Optional[str]

    # A server object to be used by the target operation.
    server: Optional[ServerObject]


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
        ReferenceObject
    ] = Field(..., alias='schema')

    # Example of the media type.
    example: Optional[Any]

    # Examples of the media type.
    examples: Optional[Dict[str, Union[ExampleObject, ReferenceObject]]]

    # A map between a property name and its encoding information.
    encoding: Optional[Dict[str, EncodingObject]]


class ParamLocation(str, Enum):

    PATH = 'path'
    QUERY = 'query'
    HEADER = 'header'
    COOKIE = 'cookie'


class ParameterObject(Schema):
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

    # Simple serialization

    # Describes how the parameter value will be serialized
    # depending on the type of the parameter value.
    style: Optional[str]

    # When this is true, parameter values of type array or
    # object generate separate parameters for each value of
    # the array or key-value pair of the map.
    explode: Optional[bool]

    # Determines whether the parameter value SHOULD allow
    # reserved characters, as defined by RFC3986 :/?#[]@!$&'()*+,;=
    # to be included without percent-encoding.
    allow_reserved: Optional[bool] = Field(None, alias='allowReserved')

    # The schema defining the type used for the parameter.
    schema_field: Optional[
        Union[SchemaObject, ReferenceObject]
    ] = Field(None, alias='schema')

    # Example of the parameter's potential value.
    example: Optional[Any]

    # Examples of the parameter's potential value.
    examples: Optional[Dict[str, Union[ExampleObject, ReferenceObject]]]

    # Complex serialization

    # A map containing the representations for the parameter.
    content: Optional[Dict[MediaTypeEnum, MediaTypeObject]]

    @root_validator(pre=True)
    def validate_serialization(cls, v):
        has_content = 'content' in v
        has_schema = 'schema' in v

        neither = not (has_content or has_schema)
        both = has_content and has_schema

        if both or neither:
            raise ValueError(
                "A parameter MUST contain either a schema property, "
                "or a content property, but not both. You provided "
                f"{'neither' if neither else 'both'}. See https://"
                "swagger.io/specification/#parameter-object for more"
                " info."
            )
        return v


class HeaderObject(ParameterObject):
    """Schema for a Header Object.

    Described in https://swagger.io/specification/#header-object.
    """

    # `name` MUST NOT be specified, it is given in the corresponding
    # headers map.
    name: str = Field(None, const=True)

    # `in` MUST NOT be specified, it is implicitly in header.
    in_field: ParamLocation = Field(ParamLocation.HEADER,
                                    const=True, alias='in')


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
    headers: Optional[Dict[str, Union[HeaderObject, ReferenceObject]]]

    # A map containing descriptions of potential response payloads.
    # The key is a media type or media type range and the value
    # describes it.
    content: Optional[Dict[MediaTypeEnum, MediaTypeObject]]

    # A map of operations links that can be followed from the response.
    links: Optional[Dict[str, Union[LinkObject, ReferenceObject]]]


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
    content: Dict[MediaTypeEnum, MediaTypeObject]

    # Determines if the request body is required in the request.
    required: Optional[bool]


class SecurityReqObject(Schema):
    ...


# TODO Callback Object
class CallbackObject(Schema):
    ...


class OperationObject(Schema):
    """Schema for an Operation Object.

    Describes a single API operation on a path. Based on spec
    described in https://swagger.io/specification/#operation-object.
    """

    # A list of tags for API documentation control.
    tags: Optional[List[str]]

    # A short summary of what the operation does.
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
    parameters: Optional[List[Union[ParameterObject, ReferenceObject]]]

    # The list of possible responses as they are returned from
    # executing this operation. This includes `default`.
    responses: Dict[str, ResponseObject]

    # The request body applicable for this operation.
    request_body: Optional[
        Union[RequestBodyObject, ReferenceObject]
    ] = Field(None, alias="requestBody")

    # A map of possible out-of band callbacks related to the
    # parent operation.
    callbacks: Optional[Dict[str, Union[CallbackObject, ReferenceObject]]]

    # Declares this operation to be deprecated.
    deprecated: Optional[bool]

    # A declaration of which security mechanisms can be used
    # for this operation.
    security: Optional[List[SecurityReqObject]]

    # An alternative server array to service this operation.
    servers: Optional[List[ServerObject]]

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
    servers: Optional[List[ServerObject]]

    # A list of parameters that are applicable for all the
    # operations described under this path.
    parameters: Optional[List[Union[ParameterObject, ReferenceObject]]]


class TagObject(Schema):
    """Schema for a Tag Object.

    Adds metadata to a single tag that is used by the Operation Object.
    Described in https://swagger.io/specification/#tag-object.
    """

    # The name of the tag.
    name: str

    # A short description for the tag.
    description: Optional[str]

    # Additional external documentation for this tag.
    external_docs: Optional[ExternalDocObject] = Field(None,
                                                       alias='externalDocs')


class ComponentsObject(Schema):
    """Schema for a Components Object.

    Holds a set of reusable objects for different aspects of the OAS.
    As described in https://swagger.io/specification/#components-object.

    All objects defined within the components object will have no effect
    on the API unless they are explicitly referenced from properties
    outside the components object. Note `ReferenceObject` for referencing.
    """

    # An object to hold reusable Schema Objects.
    schemas: Optional[Dict[str, Union[SchemaObject, ReferenceObject]]]

    # An object to hold reusable Response Objects.
    responses: Optional[Dict[str, Union[ResponseObject, ReferenceObject]]]

    # An object to hold reusable Parameter Objects.
    parameters: Optional[Dict[str, Union[ParameterObject, ReferenceObject]]]

    # An object to hold reusable Example Objects.
    examples: Optional[Dict[str, Union[ExampleObject, ReferenceObject]]]

    # An object to hold reusable Request Body Objects.
    request_bodies: Optional[
        Dict[str, Union[RequestBodyObject, ReferenceObject]]
    ] = Field(None, alias='requestBodies')

    # An object to hold reusable Header Objects.
    headers: Optional[Dict[str, Union[HeaderObject, ReferenceObject]]]

    # An object to hold reusable Security Scheme Objects.
    security_schemes: Optional[
        Dict[str, Union[SecuritySchemeObject, ReferenceObject]]
    ] = Field(None, alias='securitySchemes')

    # An object to hold reusable Link Objects.
    links: Optional[Dict[str, Union[LinkObject, ReferenceObject]]]

    # An object to hold reusable Callback Objects.
    callbacks: Optional[Dict[str, Union[CallbackObject, ReferenceObject]]]


class OpenApiObject(Schema):
    """Schema for an OpenAPI Object.

    This is the root document object of the OpenAPI document, as
    described in https://swagger.io/specification/#openapi-object.
    """

    # This string MUST be the semantic version number of
    # the OpenAPI Specification version that the OpenAPI
    # document uses.
    openapi: str

    # Provides metadata about the API.
    info: InfoObject

    # An array of Server Objects, which provide connectivity
    # information to a target server.
    servers: Optional[List[ServerObject]]

    # The available paths and operations for the API.
    paths: Dict[str, PathItemObject]

    # An element to hold various schemas for the specification.
    components: Optional[ComponentsObject]

    # A declaration of which security mechanisms can be used
    # across the API.
    security: Optional[List[SecurityReqObject]]

    # A list of tags used by the specification with additional
    # metadata.
    tags: Optional[List[TagObject]]

    # Additional external documentation.
    external_docs: Optional[ExternalDocObject] = Field(None,
                                                       alias='externalDocs')
