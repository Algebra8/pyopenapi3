from .builder import Builder
from .typedefs import OpenApiObject
from .fields import Int64, String, Email, Boolean, Double, Array


b = Builder()


class Customer(OpenApiObject):
    """A SeeTickets customer"""

    @b(read_only=True)
    def id(self) -> Int64:
        """Unique identifier for the customer"""

    @b(read_only=True, example="some_user@gmail.com")
    def email(self) -> Email:
        """Customer's email address"""

    @b(read_only=True, example="Mike")
    def firstName(self) -> String:
        """Customer's first name"""

    @b(read_only=True, example="Cat")
    def lastName(self) -> String:
        """Customer's last name"""


# This is where things get tricky:
# we want to incorporate nested objects.
class Store(OpenApiObject):
    """A store for buying things"""

    @b(read_only=True)
    def id(self) -> Int64:
        """Store's unique identification number"""

    @b()
    def customer(self) -> Customer:
        """The store's customer"""
        # Question: Will this override Customer's description?
        # Answer, no it will not!


class TicketType(OpenApiObject):
    """The ticket type of a SeeTickets ticket"""

    @b(read_only=True, example=960919)
    def id(self) -> Int64:
        """ID for the ticket type"""

    @b(read_only=True)
    def isSoldOut(self) -> Boolean:
        """Whether the ticket is sold out or not"""

    @b(read_only=True, example="GA PASS")
    def name(self) -> String:
        """The name of the ticket"""


class Ticket(OpenApiObject):
    """A SeeTicket's ticket"""

    @b(read_only=True)
    def id(self) -> Int64:
        """ID for a given ticket"""

    @b(read_only=True)
    def barcode(self) -> String:
        """Barcode for a given ticket"""

    @b(read_only=True)
    def email(self) -> Email:
        """Email for customer that holds the given ticket"""

    @b(read_only=True)
    def firstName(self) -> String:
        """
        First name for the customer that holds the given
        SeeTicket's ticket
        """

    @b(read_only=True)
    def lastName(self) -> String:
        """
        Last name for the customer that holds the given
        SeeTicket's ticket
        """

    @b(read_only=True)
    def rfid(self) -> String:
        """RFID for the given ticket"""

    @b(example="GA")
    def row(self) -> String:
        """Row for the given ticket"""

    @b(example="GA")
    def seat(self) -> String:
        """Seat for the given ticket"""

    @b(example="GA")
    def section(self) -> String:
        """Section for the given ticket"""

    @b(example="purchased — transferred to Lyte")
    def status(self) -> String:
        """Status of the given ticket"""

    @b()
    def ticketType(self) -> TicketType:
        """The ticket type for the given ticket"""
        # Question: will this override TicketType's description?
        # Answer: No it will not.

    @b(example=131.94)
    def totalPrice(self) -> Double:
        """Total price paid for the ticket"""


class PullManifestData(OpenApiObject):
    """Data containing entire Manifest."""

    @b(read_only=True, example=16262906)
    def id(self) -> Int64:
        """Unique identifier"""

    @b()
    def isValid(self) -> Boolean:
        """Validity of the order"""

    @b(example='abcd123')
    def orderNumber(self) -> String:
        """The order number"""

    @b()
    def customer(self) -> Customer:
        """Customer for the order --- this will get overridden"""

    @b()
    def tickets(self) -> Array[Ticket]:
        """Tickets for the order."""


class SomeArray(OpenApiObject):
    """An array object"""

    @b()
    def myArray(self) -> Array[Int64, Email, Customer]:
        """An array with int64, emails, and customers"""
        # TODO If there is a custom object defined anywhere, then we
        #  should write that object to the same yaml file under '#/components
        #  /schemas', and then $ref to that object. This means that we should
        #  have a dedicated builder that can keep track of the objects to
        #  convert.

    @b()
    def myAnyArray(self) -> Array[...]:
        """An array that holds anything"""



