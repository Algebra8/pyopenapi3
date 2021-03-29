# Brief example for `pyopenapi3`.
from pyopenapi3 import OpenApiBuilder
from pyopenapi3.objects import (
    Response,
    RequestBody,
    JSONMediaType,
    XMLMediaType,
    Op
)
from pyopenapi3.data_types import Email, Int64, Int32, String, Array


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
        content=[JSONMediaType(Int64), XMLMediaType(String)]
    )

    @open_bldr.path.op(summary="Some summary for the get")
    @open_bldr.path.query_param(name='email', schema=Email, required=True)
    def get(self) -> Op[..., responses]:
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


# with open("ex1.json", 'w') as f:
#     f.write(open_bldr.json(indent=2))
