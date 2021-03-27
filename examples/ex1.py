import json

from pyopenapi3 import OpenApiBuilder
from pyopenapi3.objects import (
    JSONMediaType,
    Response,
    RequestBody,
    Op
)
from pyopenapi3.data_types import (
    Int64,
    Int32,
    Array,
    String,
    Email
)


open_bldr = OpenApiBuilder()


@open_bldr.info
class Info:

    title = "Pet store api."
    version = "0.0.1"
    description = "A store for buying pets online."


@open_bldr.path
class Path1:

    path = '/users/{id:Int64}'

    responses = [
        Response(status=200, description="ok"),
        Response(status=404, description="not found")
    ]
    request_body = RequestBody(
        description="A request body",
        content=[JSONMediaType(Int64)]
    )

    @open_bldr.path.op(summary="Some summary for the get")
    @open_bldr.path.query_param(name='email', schema=Email, required=True)
    def get(self) -> Op[..., responses]:
        """Get request for path."""


@open_bldr.path
class Path2:

    path = '/pets'

    responses = [
        Response(status=200, description="ok for pets"),
        Response(status=404, description="not found for pets")
    ]
    request_body = RequestBody(
        description="A request body for pets",
        content=[JSONMediaType(Int64)]
    )

    @open_bldr.path.query_param(name='pet_id', schema=String, required=True)
    def get(self) -> Op[None, responses]:
        """Get request for path."""

    @open_bldr.path.query_param(name='pet_id', schema=String, required=True)
    def post(self) -> Op[request_body, responses]:
        """Get request for path."""


component = open_bldr.component


@component.schema
class Customer:
    """A store's customer"""

    @component.schema_field(read_only=True)
    def id(self) -> Int64:
        """Unique identifier for the customer"""

    @component.schema_field(read_only=True, example="some_user@gmail.com")
    def email(self) -> Email:
        """Customer's email address"""

    @component.schema_field(read_only=True, example="Mike")
    def firstName(self) -> String:
        """Customer's first name"""

    @component.schema_field(read_only=True, example="Cat")
    def lastName(self) -> String:
        """Customer's last name"""


@component.schema
class Store:
    """A store for buying things"""

    @component.schema_field(read_only=True)
    def id(self) -> Int64:
        """Store's unique identification number"""

    @component.schema_field
    def customer(self) -> Customer:
        """The store's customer"""

    @component.schema_field
    def someArray(self) -> Array[Customer, Int32]:
        """Just some array that can accept one of Customer or Int32"""

    @component.schema_field
    def anyArray(self) -> Array[...]:
        """An array that accepts anything"""


@component.schema
class GeneralError:

    @component.schema_field
    def code(self) -> Int32:
        ...

    @component.schema_field
    def message(self) -> String:
        ...


@component.response
class NotFound:
    description = "Entity not found."


@component.response
class IllegalInput:
    description = "Illegal input for operation."


@component.response
class GeneralError:
    description = "General Error"
    content = [JSONMediaType(GeneralError)]


@component.parameter
class skipParam:
    name = "skip"
    in_field = "query"
    description = "number of items to skip"
    required = True
    schema = Int32


@component.parameter
class limitParam:
    name = "limit"
    in_field = "query"
    description = "max records to return"
    required = True
    schema = Int32


@open_bldr.server
class Server1:
    """A server with variables in it url."""

    url = "https://{username}.gigantic-server.com:{port}/{basePath}"
    description = "The production API server"
    variables = {
        "username": {
            "default": "demo",
            "description": (
                "this value is assigned by the service provider, "
                "in this example `gigantic-server.com`"
            )
        },
        "port": {
            "enum": [
                "8443",
                "443"
            ],
            "default": "8443"
        },
        "basePath": {"default": "v2"}
    }


# Demonstrate that multiple servers can be built.
@open_bldr.server
class DevServer:

    url = "https://development.gigantic-server.com/v1"
    description = "Development server"


@open_bldr.server
class StageServer:

    url = "https://staging.gigantic-server.com/v1"
    description = "Staging server"


@open_bldr.server
class ProdServer:

    url = "https://api.gigantic-server.com/v1"
    description = "Production server"


# with open("ex1.json", 'w') as f:
#     f.write(open_bldr.json(indent=2))
