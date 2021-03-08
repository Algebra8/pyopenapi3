from typing import Iterable, Any
import functools


class Field:
    ...


class Boolean(Field):
    ...


class String(Field):
    ...


class Email(String):
    ...


class Number(Field):
    ...


class Float(Number):
    ...


class Double(Number):
    ...


class Integer(Number):
    ...


class Int32(Integer):
    ...


class Int64(Integer):
    ...


class ArbitraryArray:
    ...


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
        args: Any

        if parameters == Ellipsis:
            # Arbitrary types
            args = (ArbitraryArray,)
        elif not isinstance(parameters, tuple):
            # Single type, e.g. [1, 2, 3] aka [int].
            # Still put in tuple for uniform interface.
            args = (parameters,)
        elif isinstance(parameters, tuple):
            # Mixed-type array, e.g. ["foo", 5, -2, "bar"]
            args = parameters
        else:
            raise ValueError("Do things right.")

        @functools.wraps(cls, updated=())
        class ConcreteArray(Array):
            tvars = args

        q = ", ".join([_type.__name__ for _type in args])
        ConcreteArray.__qualname__ = f"{cls.__qualname__}[{q}]"

        return ConcreteArray

    def __iter__(self):
        return iter(self.tvars)

    def __len__(self):
        return len(self.tvars)

    def __getitem__(self, idx: int):
        return self.tvars[idx]


def is_arb_type(__type) -> bool:
    return __type is ArbitraryArray
