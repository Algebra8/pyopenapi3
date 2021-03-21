from typing import Iterable, Any, Optional, Dict, List, Tuple, Union, Type
import functools
from dataclasses import dataclass, asdict

from .types import MediaTypeEnum


class OpenApiObject:
    ...


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

    def __iter__(self):
        return iter(self.tvars)

    def __len__(self):
        return len(self.tvars)

    def __getitem__(self, idx: int):
        return self.tvars[idx]


def is_arb_type(__type) -> bool:
    return __type.__name__ == AnyTypeArray


# Components (Custom defined objects)
class Component(OpenApiObject):
    ...


# TODO This might not make sense.
class Reference(Component):
    ...


class MediaType(OpenApiObject):

    def __init__(
            self,
            __name=None,
            __field=None,
            /, *,
            example=None,
            examples=None,
            encoding=None
    ):
        self.name = __name
        self.field = __field
        self.example = example
        self.examples = examples
        self.encoding = encoding

    def __iter__(self):
        return iter(
            (self.name, self.field, self.example,
             self.examples, self.encoding)
        )

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.field.__qualname__})"


class JSONMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.JSON, __field, **kwargs)


class XMLMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.XML, __field, **kwargs)


class PDFMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.PDF, __field, **kwargs)


class URLEncodedMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.URL_ENCODED, __field, **kwargs)


class MultiPartMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.MULTIPART, __field, **kwargs)


class TextPlainMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.PLAIN, __field, **kwargs)


class HTMLMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.HTML, __field, **kwargs)


class PNGMediaType(MediaType):

    def __init__(self, __field, **kwargs):
        super().__init__(MediaTypeEnum.PNG, __field, **kwargs)


@dataclass
class Response(OpenApiObject):

    status: int
    description: str
    content: Optional[List[Union[MediaType, Any]]] = None
    headers: Optional[Any] = None
    links: Optional[Any] = None

    def as_dict(self):
        return asdict(self)


@dataclass
class RequestBody(OpenApiObject):

    content: List[Union[MediaType, Any]]
    description: Optional[str] = None
    required: bool = False

    def as_dict(self):
        return asdict(self)


class Op(Field):

    request_body = None
    responses = None

    def __repr__(self):
        return f"Op[{self.request_body}, {self.responses}]"

    def __class_getitem__(cls, parameters):

        request_body, responses = parameters
        return type("Op", (), {'request_body': request_body,
                               'responses': responses})

