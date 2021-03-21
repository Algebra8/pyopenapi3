import ruamel.yaml as yaml

from pyopenapi3.builders import OpenApiBuilder
from pyopenapi3.objects import (
    Response,
    RequestBody,
    JSONMediaType,
    Int64,
    Email,
    Op,
    String
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


@open_bldr.component.response
class NotFound:

    description = "Entity not found"


@open_bldr.component.response
class IllegalInput:

    description = "Illegal input for operation"


@open_bldr.component.response
class GeneralError:

    description = "General Error"


component = open_bldr.component


@component.schema
class Customer:
    """An api for a customer of the store."""

    @component.schema_field(read_only=True)
    def id(self) -> Int64:
        """A unique identifier for the customer."""

    @component.schema_field
    def email(self) -> Email:
        """An email for the customer"""


@component.schema
class Store:
    """An online store for selling animal stuff"""

    @component.schema_field
    def customer(self) -> Customer:
        """The customer that entered the store."""


with open('something.yaml', 'w') as f:
    yaml.dump(
        open_bldr.build.dict(),
        f,
        Dumper=yaml.RoundTripDumper
    )
