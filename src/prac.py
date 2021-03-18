# from __future__ import annotations
from typing import Tuple, get_type_hints, Union, List, Any, Dict
from collections import deque

from pydantic import ValidationError

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
    OpenApiObject,
    InfoObject,
    ServerObject
)


_build_cache = {}


class Bus:

    def __init__(self, topic):
        global _build_cache
        _build_cache[topic] = {}

        self.cache = _build_cache
        self.topic = topic

    def __getitem__(self, item):
        return self.cache[self.topic].get(item, deque())

    def __setitem__(self, key, value):
        if self.topic not in self.cache:
            self.cache[self.topic] = {}
        if key not in self.cache[self.topic]:
            self.cache[self.topic][key] = deque()
        self.cache[self.topic][key].appendleft(value)


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
        if rqbody in [..., None]:
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

        method_name = method.__name__  # e.g. get

        if method_name in self.builds:
            raise ValueError("Can't have more than one GET per path.")

        op = get_type_hints(method, localns=self.context)['return']

        request_body = op.request_body
        responses = op.responses

        if method_name == 'get' and request_body not in [None, ...]:
            # TODO Error handling
            raise ValueError("GET operation cannot have a requestBody.")

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

        def wrapper(_f):
            BuilderBus.parameters[_f] = ParameterObject(
                in_field=self.__in, **kwargs)
            return _f

        return wrapper


class PathsBuilder:

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
        methods = {
            func_name: func for func_name, func in cls.__dict__.items()
            if func_name in self._methods
        }

        self._pathitem_bldr(cls, methods)

        path_items = BuilderBus.path_items[cls]

        if path_items:
            path_item = path_items.popleft()
            if self.build is None:
                self.build = {cls.path: path_item}
            else:
                self.build[cls.path] = path_item

        return cls


class InfoBuilder:

    schema = InfoObject
    _field_keys = InfoObject.__fields__.keys()

    def __init__(self):
        self._build = None   # type: InfoObject

    @property
    def build(self):
        return self._build

    def __call__(self, cls):
        info_object = self.schema(
            **{k: v for k, v in cls.__dict__.items()
               if k in self._field_keys}
        )
        self._build = info_object


class ServerBuilder:

    schema = ServerObject
    _field_keys = ServerObject.__fields__.keys()

    def __init__(self):
        self._builds: List[ServerObject] = []

    @property
    def build(self):
        if not self._builds:
            # servers have not been provided, a default
            # server with a url value of '/' will be provided.
            return [
                self.schema(
                    url='/', description="Default server"
                )
            ]
        return self._builds

    def __call__(self, cls):
        server_object = self.schema(
            **{k: v for k, v in cls.__dict__.items()
               if k in self._field_keys}
        )
        self._builds.append(server_object)


class OpenApiBuilder:

    schema = OpenApiObject

    def __init__(self, version: str = '3.0.0'):
        self.version = version

        self.info = InfoBuilder()
        self.server = ServerBuilder()
        self.path = PathsBuilder()

        self._build = None

    @property
    def build(self):
        if self._build is not None:
            return self._build

        build = self.schema(
            openapi=self.version,
            info=self.info.build,
            servers=self.server.build,
            paths=self.path.build
        )

        self._build = build
        return build


open_bldr = OpenApiBuilder()


@open_bldr.info
class Info:

    title = "Pet store api."
    version = "0.0.1"
    description = "A store for buying pets online."


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
    def get(self) -> Op[..., responses]:
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
    def get(self) -> Op[None, responses]:
        """Get request for path."""

    @open_bldr.path.query_param(name='pet_id', schema=String, required=True)
    def post(self) -> Op[request_body, responses]:
        """Get request for path."""



import ruamel.yaml as yaml

with open('something.yaml', 'w') as f:
    yaml.dump(
        open_bldr.build.dict(),
        f,
        Dumper=yaml.RoundTripDumper
    )

