from typing import Optional, Dict, List, Tuple
from enum import Enum

from pydantic import BaseModel


class SchemaObject(BaseModel):
    ...


# info
class ContactObject(SchemaObject):
    ...


class LicenseObject(SchemaObject):
    ...


class InfoObject(SchemaObject):
    """Serialized Info Object.
    """

    title: str
    version: str
    description: Optional[str]
    terms_of_service: Optional[str]
    contact: Optional[ContactObject]
    license: Optional[LicenseObject]


# servers
class ServerVariableObject(SchemaObject):

    enum: Optional[List[str]]
    default: str
    description: Optional[str]


class ServerObject(SchemaObject):
    """Serialized Server Object.
    """

    url: str
    description: Optional[str]
    # Not sure if Pydantic can handle typing.Mapping
    variables: Optional[Dict[str, ServerVariableObject]]


# Paths
# Includes Response, Request Body, Media Type
class MediaType(str):

    json = "application/json"
    xml = "application/xml"
    pdf = "application/pdf"
    url_encoded = "application/x-www-form-urlencoded"
    multipart = "multipart/form-data"
    plain = "text/plain; charset=utf-8"
    html = "text/html"
    png = "image/png"


class Response(SchemaObject):
    """Serialized Response Object.
    """

    class Config:
        arbitrary_types_allowed = True

    status: int
    description: Optional[str]
    content: Optional[List[Tuple[MediaType, SchemaObject]]]


class RequestBody(BaseModel):
    """Serialized Request Body Object.
    """

    class Config:
        arbitrary_types_allowed = True

    description: Optional[str]
    # TODO Fix this type
    content: Optional[Tuple[MediaType, SchemaObject]]
    required: bool = False


class Parameter(BaseModel):

    name: str
    __in: str
    description: Optional[str]
    required: bool = False
    # schema: Schema








