from typing import Optional, Dict, List, Tuple, Any, Union

from pydantic import BaseModel


class Schema(BaseModel):

    def dict(self, *, exclude_unset=True, **kwargs):
        """Make default `dict` method exclude unsets by default."""
        return super().dict(exclude_unset=exclude_unset, **kwargs)


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
    ...


class ReferenceSchema(ComponentSchema):

    ref: str

    def dict(self, *args, **kwargs):
        """Return $ref as key for reference."""
        d = super().dict(*args, **kwargs)
        d["$ref"] = d["ref"]
        del d["ref"]
        return d


# Info metadata schemas.
class ContactObject(Schema):
    ...


class LicenseObject(Schema):
    ...


class InfoObject(Schema):
    """Serialized Info Object.
    """

    title: str
    version: str
    description: Optional[str]
    terms_of_service: Optional[str]
    contact: Optional[ContactObject]
    license: Optional[LicenseObject]


# Server schemas
class ServerVariableObject(Schema):

    enum: Optional[List[str]]
    default: str
    description: Optional[str]


class ServerObject(Schema):
    """Serialized Server Object.
    """

    url: str
    description: Optional[str]
    # Not sure if Pydantic can handle typing.Mapping
    variables: Optional[Dict[str, ServerVariableObject]]


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


class Response(Schema):
    """Serialized Response Object.
    """

    class Config:
        arbitrary_types_allowed = True

    status: int
    description: Optional[str]
    content: Optional[List[Tuple[MediaType, Schema]]]


class RequestBody(BaseModel):
    """Serialized Request Body Object.
    """

    class Config:
        arbitrary_types_allowed = True

    description: Optional[str]
    # TODO Fix this type
    content: Optional[Tuple[MediaType, Schema]]
    required: bool = False


class Parameter(BaseModel):

    name: str
    __in: str
    description: Optional[str]
    required: bool = False
    # schema: Schema








