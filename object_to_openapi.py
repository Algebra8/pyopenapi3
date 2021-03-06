# """
# NOTE:
#
#     oneOf and anyOf and a few other directives are not supported
#     in Swagger 2.0 **but are supported** in Open API 3.0.
#
#     So, consider differentiating between the two through the
#     builder.
#
# """
#
# from typing import (
#     Dict,
#     Any,
#     Optional,
#     TypedDict,
#     Iterable
# )
# import functools
# import inspect
#
# import yaml
#
#
# OPENAPI_DEF = '__OPENAPIDEF__'
#
#
# # Helper for formating descriptions.
# def _format_description(s: Optional[str]) -> str:
#     # TODO what if s is None...
#     if s is None:
#         return ''
#     s = s.strip()
#     s = s.replace("\n", "")
#     s = s.replace("\t", "")
#     return " ".join(s.split())
#
#
# # Helper for issubclass so it won't break
# # every time a non-class is checked.
# def _issubclass(c1, c2):
#     if inspect.isclass(c1):
#         return issubclass(c1, c2)
#     return False
#
#
# # Stuff for yaml ###################################
# # This will let us create Open API 3.0.0 references,
# # i.e. $ref: ...
# class Ref(tuple):
#
#     ...
#
#
# def ref_presenter(dumper, data):
#     # Data should be a Tuple, containing the
#     # path of where the component lives and
#     # the component name.
#     p, d = data
#     return dumper.represent_dict(
#         {'$ref': f"{p}/{d}"}
#     )
#
#
# yaml.add_representer(Ref, ref_presenter)
#
# #####################################################
#
#
# class PropertyObject(TypedDict, total=False):
#
#     type: str
#     format: str
#     description: str
#     readOnly: Optional[bool]
#     example: Optional[Any]
#     items: Optional[Any]  # TODO fix type hint
#
#
# class OpenApiObject:
#     ...
#
#
# class Field:
#     ...
#
#
# class Boolean(Field):
#     ...
#
#
# class String(Field):
#     ...
#
#
# class Email(String):
#     ...
#
#
# class Number(Field):
#     ...
#
#
# class Float(Number):
#     ...
#
#
# class Double(Number):
#     ...
#
#
# class Integer(Number):
#     ...
#
#
# class Int32(Integer):
#     ...
#
#
# class Int64(Integer):
#     ...
#
#
# _arb_types = object()
#
#
# class Array(Field, Iterable):
#     """An OpenAPI Array type.
#
#     The `array` itself is just a container and holds
#     some another Field or nested structure.
#     """
#
#     # The magic methods listed below are to mock the
#     # interface of a subsciptable type with variadic
#     # generic types, e.g. `typing.Tuple`.
#     #
#     # Ideally, non of this would be necessary, but
#     # until variadic generics (PEP 646) become a thing,
#     # this should do.
#
#     def __init__(self, __args):
#         self._args = __args
#
#     def __repr__(self):
#         return f"Array{self._args}"
#
#     def __class_getitem__(cls, parameters):
#         args: Any
#
#         if parameters == Ellipsis:
#             # Arbitrary types
#             args = (_arb_types,)
#         elif not isinstance(parameters, tuple):
#             # Single type, e.g. [1, 2, 3] aka [int].
#             # Still put in tuple for uniform interface.
#             args = (parameters,)
#         elif isinstance(parameters, tuple):
#             # Mixed-type array, e.g. ["foo", 5, -2, "bar"]
#             args = parameters
#         else:
#             raise ValueError("Do things right.")
#
#         return Array(args)
#
#     def __iter__(self):
#         return iter(self._args)
#
#     def __len__(self):
#         return len(self._args)
#
#     def __getitem__(self, idx: int):
#         return self._args[idx]
#
#
# def create_object(
#         _cls, *,
#         override_name_with: Optional[str] = None
# ) -> Dict[str, Any]:
#     """Convert a Python class to an OpenAPI format.
#
#     The entrypoint for conversion.
#     """
#     name = override_name_with or _cls.__name__
#     descr = _format_description(_cls.__doc__)
#
#     clsdata = {
#         'description': descr,
#         'type': 'object',
#         'properties': {}
#     }
#
#     for attr in _cls.__dict__.values():
#         if hasattr(attr, OPENAPI_DEF):
#             # Some decorator should pass read_only in.
#             prop_data = getattr(attr, OPENAPI_DEF)
#             clsdata['properties'].update(prop_data)  # type: ignore
#
#     return {name: clsdata}
#
#
# def create_property(
#         field, name, description, *,
#         read_only: bool = False,
#         example: Optional[Any]
# ) -> Dict[str, Any]:
#     prop_data: Dict[str, Any] = parse_attr(field)
#     prop_data['description'] = description
#     if read_only:
#         # This may seem redundant but we do not want to
#         # clutter the OpenAPI definition with 'readOnly = false'.
#         # So doing something like `propdata['readOnly']
#         # = read_only` in the outer scope is not an option.
#         prop_data['readOnly'] = True
#     if example is not None:
#         prop_data['example'] = example
#     return {name: prop_data}
#
#
# # def _create_property(
# #         _prop, *,
# #         read_only: bool = False,
# #         example: Optional[Any] = None
# # ) -> Dict[str, PropertyObject]:
# #     propdata: PropertyObject
# #
# #     # TODO Clean and separate logic and actual type hints
# #     #  for the `create_property` function.
# #     return_annots = _prop.__annotations__['return']
# #     if isinstance(return_annots, Array):
# #         # Special case: `array` type.
# #         propdata = create_container(return_annots)
# #     else:
# #         # TODO fix type v format for non-integer types.
# #         prop_type = return_annots.__mro__[1].__name__.lower()
# #         prop_format = return_annots.__name__.lower()
# #
# #         propdata = PropertyObject(
# #             type=prop_type,
# #             format=prop_format,
# #         )
# #
# #     propdata['description'] = _format_description(_prop.__doc__)
# #
# #     if read_only:
# #         # This may seem redundant but we do not want to
# #         # clutter the OpenAPI definition with 'readOnly = false'.
# #         # So doing something like `propdata['readOnly']
# #         # = read_only` in the outer scope is not an option.
# #         propdata['readOnly'] = True
# #
# #     if example is not None:
# #         propdata['example'] = example
# #
# #     return {_prop.__name__: propdata}
#
#
# def create_container(container) -> PropertyObject:
#     container_data = {
#         'type': 'array',
#         'items': {}
#     }
#
#     def _assign_type(__type):
#         return (
#             parse_attr(__type) if _issubclass(__type, Field)
#             else Ref(('#/components/schemas', __type.__name__))
#         )
#
#     if len(container) == 1:
#         if container[0] is _arb_types:
#             return container_data
#
#         container_data['items'] = _assign_type(container[0])
#     else:
#         container_data['items'] = {'oneOf': []}
#         for _type in container:
#             container_data['items']['oneOf'].append(
#                 _assign_type(_type)
#             )
#
#     return PropertyObject(**container_data)
#
#
# def parse_attr(o):
#     if issubclass(o, Number):
#         return parse_numbers(o)
#     elif issubclass(o, String):
#         return parse_strings(o)
#     elif o == Boolean:
#         return {'type': 'boolean'}
#     raise ValueError(f"Attr for {o} not defined.")
#
#
# def parse_strings(s):
#     if s == String:
#         return {'type': 'string'}
#     else:
#         return {'type': 'string', 'format': s.__name__.lower()}
#
#
# def parse_numbers(n):
#     if n == Number:
#         return {'type': 'number'}
#     elif n == Integer:
#         return {'type': 'integer'}
#     elif issubclass(n, Number) and not issubclass(n, Integer):
#         return {'type': 'number', 'format': n.__name__.lower()}
#     elif issubclass(n, Integer):
#         return {'type': 'integer', 'format': n.__name__.lower()}
#
#
# def create_open_api_object(f, read_only: bool, example: Optional[Any]):
#     prop_data: Dict[str, Any]
#     _field = f.__annotations__['return']
#
#     if isinstance(_field, Array) or issubclass(_field, Field):
#         if isinstance(_field, Array):
#             prop_data = {f.__name__: create_container(_field)}
#         else:
#             # is a subclass of Field
#             prop_data = create_property(
#                 _field, f.__name__,
#                 _format_description(f.__doc__),
#                 read_only=read_only,
#                 example=example
#             )
#     elif issubclass(_field, OpenApiObject):
#         prop_data = create_object(
#             _field, override_name_with=f.__name__
#         )
#     else:
#         raise ValueError("Not a custom object or a Field.")
#
#     return prop_data
#
#
# class Builder:
#
#     def __call__(
#             self, *,
#             read_only: bool = False,
#             example: Optional[Any] = None,
#     ):
#         def func_wrapper(f):
#
#             @functools.wraps(f)
#             def wrapped(*args, **kwargs):
#                 return f(*args, **kwargs)
#
#             open_api_obj = create_open_api_object(
#                 f, read_only=read_only, example=example
#             )
#
#             setattr(
#                 wrapped, OPENAPI_DEF,
#                 open_api_obj
#             )
#
#             return wrapped
#
#         return func_wrapper
#
#
# b = Builder()
#
#
# class Customer(OpenApiObject):
#     """A SeeTickets customer"""
#
#     @b(read_only=True)
#     def id(self) -> Int64:
#         """Unique identifier for the customer"""
#
#     @b(read_only=True, example="some_user@gmail.com")
#     def email(self) -> Email:
#         """Customer's email address"""
#
#     @b(read_only=True, example="Mike")
#     def firstName(self) -> String:
#         """Customer's first name"""
#
#     @b(read_only=True, example="Cat")
#     def lastName(self) -> String:
#         """Customer's last name"""
#
#
# # This is where things get tricky:
# # we want to incorporate nested objects.
# class Store(OpenApiObject):
#     """A store for buying things"""
#
#     @b(read_only=True)
#     def id(self) -> Int64:
#         """Store's unique identification number"""
#
#     @b()
#     def customer(self) -> Customer:
#         """The store's customer"""
#         # Question: Will this override Customer's description?
#         # Answer, no it will not!
#
#
# class TicketType(OpenApiObject):
#     """The ticket type of a SeeTickets ticket"""
#
#     @b(read_only=True, example=960919)
#     def id(self) -> Int64:
#         """ID for the ticket type"""
#
#     @b(read_only=True)
#     def isSoldOut(self) -> Boolean:
#         """Whether the ticket is sold out or not"""
#
#     @b(read_only=True, example="GA PASS")
#     def name(self) -> String:
#         """The name of the ticket"""
#
#
# class Ticket(OpenApiObject):
#     """A SeeTicket's ticket"""
#
#     @b(read_only=True)
#     def id(self) -> Int64:
#         """ID for a given ticket"""
#
#     @b(read_only=True)
#     def barcode(self) -> String:
#         """Barcode for a given ticket"""
#
#     @b(read_only=True)
#     def email(self) -> Email:
#         """Email for customer that holds the given ticket"""
#
#     @b(read_only=True)
#     def firstName(self) -> String:
#         """
#         First name for the customer that holds the given
#         SeeTicket's ticket
#         """
#
#     @b(read_only=True)
#     def lastName(self) -> String:
#         """
#         Last name for the customer that holds the given
#         SeeTicket's ticket
#         """
#
#     @b(read_only=True)
#     def rfid(self) -> String:
#         """RFID for the given ticket"""
#
#     @b(example="GA")
#     def row(self) -> String:
#         """Row for the given ticket"""
#
#     @b(example="GA")
#     def seat(self) -> String:
#         """Seat for the given ticket"""
#
#     @b(example="GA")
#     def section(self) -> String:
#         """Section for the given ticket"""
#
#     @b(example="purchased — transferred to Lyte")
#     def status(self) -> String:
#         """Status of the given ticket"""
#
#     @b()
#     def ticketType(self) -> TicketType:
#         """The ticket type for the given ticket"""
#         # Question: will this override TicketType's description?
#         # Answer: No it will not.
#
#     @b(example=131.94)
#     def totalPrice(self) -> Double:
#         """Total price paid for the ticket"""
#
#
# class PullManifestData(OpenApiObject):
#     """Data containing entire Manifest."""
#
#     @b(read_only=True, example=16262906)
#     def id(self) -> Int64:
#         """Unique identifier"""
#
#     @b()
#     def isValid(self) -> Boolean:
#         """Validity of the order"""
#
#     @b(example='abcd123')
#     def orderNumber(self) -> String:
#         """The order number"""
#
#     @b()
#     def customer(self) -> Customer:
#         """Customer for the order --- this will get overridden"""
#
#     @b()
#     def tickets(self) -> Array[Ticket]:
#         """Tickets for the order."""
#
#
# class SomeArray(OpenApiObject):
#     """An array object"""
#
#     @b()
#     def myArray(self) -> Array[Int64, Email, Customer]:
#         """An array with int64, emails, and customers"""
#         # TODO If there is a custom object defined anywhere, then we
#         #  should write that object to the same yaml file under '#/components
#         #  /schemas', and then $ref to that object. This means that we should
#         #  have a dedicated builder that can keep track of the objects to
#         #  convert.
#
#     @b()
#     def myAnyArray(self) -> Array[...]:
#         """An array that holds anything"""
#
#
# def dump_yaml(filename, _object):
#     with open(filename, 'w') as f:
#         yaml.dump(_object, f, allow_unicode=True)
#
#
# # store_object = create_object(Store)
# # dump_yaml('store.yaml', store_object)
# #
# # customer_object = create_object(Customer)
# # dump_yaml('customer.yaml', customer_object)
# #
# # ticket_type_object = create_object(TicketType)
# # dump_yaml('ticket_type.yaml', ticket_type_object)
# #
# # ticket_object = create_object(Ticket)
# # dump_yaml('ticket.yaml', ticket_object)
#
# my_array_object = create_object(SomeArray)
# dump_yaml('my_array.yaml', my_array_object)
#
