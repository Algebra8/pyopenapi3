from src.pyopenapi3.builder import OpenApiBuilder
from src.pyopenapi3.typedefs import OpenApiObject
from src.pyopenapi3.fields import (
    Int64,
    String,
    Email,
)


open_bldr = OpenApiBuilder()


@open_bldr.component()
class Customer(OpenApiObject):
    """A SeeTickets customer"""

    @open_bldr.component(read_only=True)
    def id(self) -> Int64:
        """Unique identifier for the customer"""

    @open_bldr.component(read_only=True, example="some_user@gmail.com")
    def email(self) -> Email:
        """Customer's email address"""

    @open_bldr.component(read_only=True, example="Mike")
    def firstName(self) -> String:
        """Customer's first name"""

    @open_bldr.component(read_only=True, example="Cat")
    def lastName(self) -> String:
        """Customer's last name"""


# This is where things get tricky:
# we want to incorporate nested objects.
@open_bldr.component()
class Store(OpenApiObject):
    """A store for buying things"""

    @open_bldr.component(read_only=True)
    def id(self) -> Int64:
        """Store's unique identification number"""

    @open_bldr.component()
    def customer(self) -> Customer:
        """The store's customer"""
        # Question: Will this override Customer's description?
        # Answer, no it will not!


@open_bldr.info
class Info:

    title = "Pet store"
    description = "A store for pets"
    version = "1.0.0"
    terms_of_service = "path/to/terms_of_service"
    # contact = object()  # ContactObject
    # license = object()  # LicenseObject


# @open_bldr.server
# class Server1:
#
#     # url = "google.com/page1"
#     description = "The page1 for google or something"
#
#
# @open_bldr.server
# class Server2:
#
#     url = "google.com/page2"
#     description = "Page2 for google, or something like that"
#     variables = {
#         'var1': {'enum': ['enum1'], 'default': "a", 'description': "?"},
#         'var2': {'enum': ['enum2'], 'default': 'b', 'description': "?!"}
#     }


# open_bldr.component.as_yaml('other_info.yaml')
open_bldr.as_yaml('other_info.yaml')



