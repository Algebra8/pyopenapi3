from typing import Iterable

from .objects import OpenApiObject

__all__ = (
    "Boolean",
    "String",
    "Byte",
    "Binary",
    "Date",
    "DateTime",
    "Password",
    "Email",
    "Number",
    "Float",
    "Double",
    "Integer",
    "Int32",
    "Int64",
    "Array",
)


class Field(OpenApiObject):

    def __repr__(self):
        return self.__class__.__qualname__


class Primitive(Field):
    ...


# Primitives
class Boolean(Primitive):
    ...


class String(Primitive):
    ...


class Byte(String):

    ...


class Date(String):
    ...


class Binary(String):
    ...


class DateTime(String):
    ...


class Password(String):
    ...


class Email(String):
    ...


class Number(Primitive):
    ...


class Float(Number):
    ...


class Double(Number):
    ...


class Integer(Primitive):
    ...


class Int32(Integer):
    ...


class Int64(Integer):
    ...


# namespaces
SingleArray = "SingleArray"
MixedTypeArray = "MixedTypeArray"
AnyTypeArray = "AnyTypeArray"


class Array(Field, Iterable):
    """An OpenAPI Array type.

    The `array` itself is just a container and holds
    some another Field or nested structure.
    """

    # Some of the magic methods listed below are to mock
    # the interface of a subsciptable type with variadic
    # generic types, e.g. `typing.Tuple`. Others act as
    # helpers/convenience methods.
    #
    # Ideally, non of this would be necessary, but
    # until variadic generics (PEP 646) become a thing,
    # this should do.
    tvars = None

    def __repr__(self):
        return f"Array{self.tvars}"

    def __class_getitem__(cls, parameters):
        if parameters == Ellipsis:
            args = ()
            _cls = type(AnyTypeArray, (Array,), {'tvars': args})
            s = '...'
        elif not isinstance(parameters, tuple):
            args = (parameters,)
            _cls = type(SingleArray, (Array,), {'tvars': args})
            s = parameters.__name__
        elif isinstance(parameters, tuple):
            args = parameters
            _cls = type(MixedTypeArray, (Array,), {'tvars': args})
            s = ", ".join([_type.__name__ for _type in args])
        else:
            raise ValueError()

        _cls.__qualname__ = f"{cls.__qualname__}[{s}]"

        return _cls


# Components (Custom defined objects)
class Component(OpenApiObject):
    ...
