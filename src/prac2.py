from typing import Tuple, NewType, List

from pyopenapi3.builder import ParamBuilder
from pyopenapi3.fields import Int64, Email
from pydantic import BaseModel
from pyopenapi3.utils import get_name_and_type

class Response:

    def __init__(
            self, status, description="",
            # content is None or list of media type and schema tuples.
            # If a
            content=None
    ):
        self.status = status
        self.description = description
        self.content = content

    def as_dict(self):
        d = {}
        if self.content is not None:
            for con in self.content:
                media, schema = con
                d.update({
                    media: {'schema': schema}
                })

        return {
            str(self.status): {
                'description': self.description,
                'content': d
            }
        }


MediaType = NewType('MediaType', str)
Schema = NewType('Schema', str)


class RequestBody:

    description: str
    required: bool
    content: List[Tuple[MediaType, Schema]]

    def __init__(self, description, required, content):
        self.description = description
        self.required = required
        self.content = content

    def as_dict(self):
        d = {}
        if self.content is not None:
            for con in self.content:
                media, schema = con
                d.update({
                    media: {'schema': schema}
                })

        return {
            'description': self.description,
            'required': self.required,
            'content': d
        }


class Users:

    # `id` should be automatically placed in
    # each method's parameter as "in: path".
    # TODO Figure out how to yank `id` out of formatted str `path`.
    path = '/users/{id:Int64}'

    get_response_200 = Response(
        200, "a list of users",
        [("application/json", "string"), ("application/xml", "int")]
    )
    get_response_404 = Response(
        404, "an error",
        [("application/json", "string")]
    )
    get_responses = [get_response_200, get_response_404]
    get_body = RequestBody(
        'Some request body',
        True,
        [("application/json", "string"), ("application/xml", "int")]
    )

    # Idea: Make return a tuple of requestBody and Response
    # and make any method param a query param.
    # The latter can be done by demanding annotations for
    # the param. Then it can be retrieved with get.__annotations__.
    # The param would also have to be a subtype of Field.
    # @open_bldr.path.param()
    # @open_bldr.path()
    def get(self) -> (get_body, get_responses):
        """Get all users"""

    def post(self) -> path:
        ...

    @classmethod
    def as_dict(cls):
        d = {cls.path: {}}
        for i, j in cls.__dict__.items():
            if i == 'get':
                d[cls.path]['get'] = {}
                req, resp = j.__annotations__['return']
                d[cls.path]['get']['requestBody'] = req.as_dict()
                d[cls.path]['get']['responses'] = {}
                for response in resp:
                    d[cls.path]['get']['responses'].update(response.as_dict())
                d[cls.path]['get']['summary'] = "Some summary"

        return d


query_param = ParamBuilder("query")


class A:

    @query_param(name='some query', schema_type=Email)
    @query_param(name='some query', schema_type=Int64)
    def s(self) -> int:
        ...

z = '{a:Int64}{b:String}{c:Email}'


for i in get_name_and_type(z):
    print(i)


