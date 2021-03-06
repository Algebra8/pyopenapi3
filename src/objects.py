from typing import Optional, Dict, List

from pydantic import BaseModel


# info
class ContactObject(BaseModel):
    ...


class LicenseObject(BaseModel):
    ...


class InfoObject(BaseModel):
    """Serialized Info Object.
    """

    title: str
    version: str
    description: Optional[str]
    terms_of_service: Optional[str]
    contact: Optional[ContactObject]
    license: Optional[LicenseObject]


# servers
class ServerVariableObject(BaseModel):

    enum: Optional[List[str]]
    default: str
    description: Optional[str]


class ServerObject(BaseModel):
    """Serialized Server Object.
    """

    url: str
    description: Optional[str]
    # Not sure if Pydantic can handle typing.Mapping
    variables: Optional[Dict[str, ServerVariableObject]]

