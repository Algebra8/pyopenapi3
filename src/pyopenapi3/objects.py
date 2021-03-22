from typing import Any, Optional, List, Union
from dataclasses import dataclass, asdict

from .types import MediaTypeEnum

__all__ = (
    "JSONMediaType",
    "XMLMediaType",
    "PDFMediaType",
    "URLEncodedMediaType",
    "MultiPartMediaType",
    "TextPlainMediaType",
    "HTMLMediaType",
    "PNGMediaType",
    "Response",
    "RequestBody",
    "Op"
)


class OpenApiObject:
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


class Op:

    request_body = None
    responses = None

    def __repr__(self):
        return f"Op[{self.request_body}, {self.responses}]"

    def __class_getitem__(cls, parameters):

        request_body, responses = parameters
        return type("Op", (), {'request_body': request_body,
                               'responses': responses})

