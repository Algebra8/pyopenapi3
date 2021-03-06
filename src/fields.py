from typing import Iterable, Any


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


_arb_type_enum = object()


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

    def __init__(self, __args):
        self._args = __args

    def __repr__(self):
        return f"Array{self._args}"

    def __class_getitem__(cls, parameters):
        args: Any

        if parameters == Ellipsis:
            # Arbitrary types
            args = (_arb_type_enum,)
        elif not isinstance(parameters, tuple):
            # Single type, e.g. [1, 2, 3] aka [int].
            # Still put in tuple for uniform interface.
            args = (parameters,)
        elif isinstance(parameters, tuple):
            # Mixed-type array, e.g. ["foo", 5, -2, "bar"]
            args = parameters
        else:
            raise ValueError("Do things right.")

        return Array(args)

    def __iter__(self):
        return iter(self._args)

    def __len__(self):
        return len(self._args)

    def __getitem__(self, idx: int):
        return self._args[idx]


def is_arb_type(__type) -> bool:
    return __type is _arb_type_enum
