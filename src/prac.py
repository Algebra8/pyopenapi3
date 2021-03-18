# from __future__ import annotations
from typing import Tuple, get_type_hints, Union, List, Any, Dict

from collections import deque

from pyopenapi3.utils import (
    ObjectToDTSchema,
    format_description,
    build_mediatype_schema_from_content,
    create_schema
)
from pyopenapi3.objects import (
    Int64,
    String,
    Response,
    RequestBody,
    Op,
    JSONMediaType
)
from pyopenapi3.schemas import (
    ObjectsDTSchema,
    RequestBodyObject,
    ResponseObject,
    OperationObject,
    ParameterObject,
    PathItemObject,
    PathsObject
)


class Bus:

    def __init__(self, topic):
        self.topic = topic
        self.cache = None

    def __getitem__(self, item):
        return self.cache[item]

    def __setitem__(self, key, value):
        if self.cache is None:
            self.cache = {key: deque()}
        if key not in self.cache:
            self.cache[key] = deque()
        self.cache[key].appendleft(value)


class BuilderBus:

    request_bodies = Bus('request_bodies')
    responses = Bus('responses')
    operations = Bus('operations')
    parameters = Bus('parameters')
    path_items = Bus('path_items')
    paths = Bus('paths')


class RequestBodyBuilder:

    schema = RequestBodyObject

    def __init__(self, sub=None):
        self.sub = sub

    def __call__(
            self,
            rqbody: Union[RequestBody, Dict[str, Any], Any],
            sub=None
    ) -> None:
        if rqbody is Ellipsis:
            return

        if isinstance(rqbody, RequestBody):
            rqbody = rqbody.as_dict()

        content = build_mediatype_schema_from_content(rqbody['content'])
        description = rqbody['description']
        required = rqbody['required']

        BuilderBus.request_bodies[sub] = RequestBodyObject(
            content=content,
            description=description,
            required=required
        )


class ResponseBuilder:

    def __init__(self, sub=None):
        self.sub = sub

    def __call__(self, responses: List[Response], sub):
        for response in responses:
            if isinstance(response, Response):
                _response = response.as_dict()
            else:
                _response = response
            content = build_mediatype_schema_from_content(_response['content'])
            _response['content'] = content

            BuilderBus.responses[sub] = (
                _response['status'],
                ResponseObject(**_response)
            )


class OperationBuilder:

    def __init__(self, sub=None, context=None):
        self.sub = sub
        self.context = context

        self._rqbody_bldr = RequestBodyBuilder()
        self._resp_bldr = ResponseBuilder()

        self.builds = {}

    def __call__(self, method):

        if method.__name__ in self.builds:
            raise ValueError("Can't have more than one GET per path.")

        op = get_type_hints(method, localns=self.context)['return']

        request_body = op.request_body
        responses = op.responses

        self._rqbody_bldr(request_body, method)
        self._resp_bldr(responses, method)

        builds = {
            'responses': {},
            'request_body': None
        }

        responses = BuilderBus.responses[method]
        rqbody = BuilderBus.request_bodies[method]

        while responses:
            status, resp = responses.popleft()
            builds['responses'][status] = resp

        if rqbody:
            # There should only be one request_body.
            builds['request_body'] = rqbody.popleft()

        BuilderBus.operations[method] = OperationObject(**builds)


class PathItemBuilder:

    def __init__(self, sub=None, context=None):
        self.sub = sub
        self.context = context

        self._op_bldr = OperationBuilder(context=context)

        self.builds = {}

    def __call__(self, cls, methods):
        attrs = {}
        for name, method in methods.items():
            self._op_bldr(method)
            ops = BuilderBus.operations[method]

            if ops:
                op = ops.popleft()
                attrs[name] = op
        BuilderBus.path_items[cls] = PathItemObject(**attrs)


class ParamBuilder:

    def __init__(self, __in):
        self.__in = __in

    def __call__(self, **kwargs):
        if 'schema' in kwargs:
            schema = kwargs.pop('schema')
            kwargs['schema'] = create_schema(schema)
        elif 'content' in kwargs:
            content = kwargs.pop('content')
            kwargs['content'] = build_mediatype_schema_from_content(content)

        def wrapper(f):
            BuilderBus.parameters[f] = ParameterObject(
                in_field=self.__in, **kwargs)
            return f

        return wrapper


class PathsBuilder:

    paths = {}

    _methods = {
        'get', 'post', 'put', 'patch',
        'delete', 'head', 'options',
        'trace'
    }

    def __init__(self):
        self.query_param = ParamBuilder('query')
        self.header_param = ParamBuilder('header')
        self.cookie_param = ParamBuilder('cookie')

        self._pathitem_bldr = PathItemBuilder()

        self.build = None

    def __call__(self, cls):

        self.paths[cls.path] = {}

        methods = {
            func_name: func for func_name, func in cls.__dict__.items()
            if func_name in self._methods
        }

        self._pathitem_bldr(cls, methods)

        path_items = BuilderBus.path_items[cls]

        if path_items:
            path_item = path_items.popleft()
            if self.build is None:
                self.build = PathsObject(
                    paths={cls.path: path_item}
                )
            else:
                self.build.paths[cls.path] = path_item

        return cls


class OpenApiBuilder:

    def __init__(self):
        self.path = PathsBuilder()


open_bldr = OpenApiBuilder()


@open_bldr.path
class Path1:

    path = '/users'

    responses = [
        Response(status=200, description="ok"),
        Response(status=404, description="not found")
    ]
    request_body = RequestBody(
        description="A request body",
        content=[JSONMediaType(Int64)]
    )

    @open_bldr.path.query_param(name='id', schema=Int64, required=True)
    def get(self) -> Op[request_body, responses]:
        """Get request for path."""


@open_bldr.path
class Path2:

    path = '/pets'

    responses = [
        Response(status=200, description="ok for pets"),
        Response(status=404, description="not found for pets")
    ]
    request_body = RequestBody(
        description="A request body for pets",
        content=[JSONMediaType(Int64)]
    )

    @open_bldr.path.query_param(name='pet_id', schema=String, required=True)
    def get(self) -> Op[request_body, responses]:
        """Get request for path."""


paths = open_bldr.path

