from __future__ import annotations
from typing import get_type_hints, Union, List, Any, Dict, Optional
from collections import deque
import re

from pydantic import ValidationError

from pyopenapi3.utils import (
    build_mediatype_schema_from_content,
    create_schema,
    format_description,
    parse_name_and_type_from_fmt_str
)
from pyopenapi3.objects import (
    Int64,
    String,
    Email,
    Response,
    RequestBody,
    Op,
    JSONMediaType
)
from pyopenapi3.schemas import (
    RequestBodyObject,
    ResponseObject,
    OperationObject,
    ParameterObject,
    PathItemObject,
    OpenApiObject,
    InfoObject,
    ServerObject,
    ComponentsObject
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

    _field_keys = ResponseObject.__fields__.keys()

    def __call__(
            self, cls=None, /, *,
            responses: List[Union[Response, Dict[str, Any]]] = None,
            sub=None
    ):
        if cls is not None:
            # A single response class.
            resp_attrs = {name: attr for name, attr in cls.__dict__.items()
                          if name in self._field_keys}
            self.__call__(responses=[resp_attrs], sub=cls)
            return cls

        assert responses is not None
        assert sub is not None
        for response in responses:
            if isinstance(response, Response):
                _response = response.as_dict()
            else:
                _response = response
            content = build_mediatype_schema_from_content(
                _response.get('content')
            )
            _response['content'] = content

            BuilderBus.responses[sub] = (
                _response.get('status'),
                ResponseObject(**_response)
            )


class OperationBuilder:

    def __init__(self):
        self._rqbody_bldr = RequestBodyBuilder()
        self._resp_bldr = ResponseBuilder()

        self.query_param = ParamBuilder('query')
        self.cookie_param = ParamBuilder('cookie')
        self.header_param = ParamBuilder('header')

        self.builds = {}
        self._attrs = {}

    def __call__(self, method=None, /, context=None, **kwargs):

        # If the client called `OperationBuilder`, then we use
        # the `kwargs` passed in for every field on the `OperationObject`
        # other than responses, request body, and params.
        if method is None:

            def wrapper(_f):
                # Save the `kwags` in `_attrs` so that we can use
                # them when __call__ is called with `method is not None`,
                # i.e. when processing the path object at the class level.
                # Note that class methods will get decorated **before** a
                # class itself gets decorated, so we expect `_attrs` to
                # be non-empty (assuming `kwags` was not empty).
                self._attrs.update({_f: kwargs})
                return _f

            return wrapper

        method_name = method.__name__  # e.g. get

        if method_name in self.builds:
            raise ValueError("Can't have more than one GET per path.")

        op = get_type_hints(method, localns=context)['return']

        request_body = op.request_body
        responses = op.responses

        if method_name == 'get' and request_body not in [None, ...]:
            # TODO Error handling
            raise ValueError("GET operation cannot have a requestBody.")

        self._rqbody_bldr(request_body, method)
        self._resp_bldr(responses=responses, sub=method)

        builds = {
            'responses': {},
            'request_body': None,
            'parameters': None
        }

        responses = BuilderBus.responses[method]
        while responses:
            status, resp = responses.popleft()
            builds['responses'][status] = resp

        rqbody = BuilderBus.request_bodies[method]
        if rqbody:
            # There should only be one request_body.
            builds['request_body'] = rqbody.popleft()

        params = BuilderBus.parameters[method]
        if params:
            builds['parameters'] = list(params)

        if method in self._attrs:
            self._attrs[method].update(builds)
        else:
            self._attrs[method] = builds

        BuilderBus.operations[method] = OperationObject(
            **self._attrs[method],
        )


class PathItemBuilder:

    def __init__(self):
        self.op_bldr = OperationBuilder()

        self.builds = {}

    def __call__(self, cls, methods):
        attrs = {}

        # Operation object building.
        for name, method in methods.items():
            self.op_bldr(method, context=cls.__dict__)
            ops = BuilderBus.operations[method]
            if ops:
                op = ops.popleft()
                attrs[name] = op

        # Other info for `PathItemObject`.

        description = format_description(cls.__doc__)

        summary = None
        if hasattr(cls, 'summary'):
            summary = getattr(cls, 'summary')

        servers = None  # type: Optional[List[Any]]
        if hasattr(cls, 'servers'):
            servers = getattr(cls, 'servers')

        # Build any `PathItemObject` level parameters.
        parameters = []  # type: List[Any]
        if hasattr(cls, 'parameters'):
            parameters += getattr(cls, 'parameters')
        # The given path may also hold params, e.g. "/users/{id:Int64}"
        path = cls.path
        for name, _type in parse_name_and_type_from_fmt_str(path):
            parameters.append(
                ParamBuilder('path').build_param(
                    name=name, schema=_type, required=True
                )
            )

        extra_attrs = {
            'summary': summary,
            'parameters': parameters or None,
            'servers': servers,
            'description': description
        }

        BuilderBus.path_items[cls] = PathItemObject(**attrs, **extra_attrs)


class ParamBuilder:

    def __init__(self, __in):
        self.__in = __in

    def __call__(self, **kwargs):

        def wrapper(_f):
            BuilderBus.parameters[_f] = self.build_param(**kwargs)
            return _f
        return wrapper

    def build_param(self, **kwargs):
        if 'schema' in kwargs:
            schema = kwargs.pop('schema')
            kwargs['schema'] = create_schema(schema)
        elif 'content' in kwargs:
            content = kwargs.pop('content')
            kwargs['content'] = build_mediatype_schema_from_content(content)
        return ParameterObject(in_field=self.__in, **kwargs)


class PathsBuilder:

    _methods = {
        'get', 'post', 'put', 'patch',
        'delete', 'head', 'options',
        'trace'
    }

    def __init__(self):
        self._pathitem_bldr = PathItemBuilder()

        # Client interface for params and operations
        # object builders.
        self.op = self._pathitem_bldr.op_bldr
        self.query_param = self.op.query_param
        self.header_param = self.op.header_param
        self.cookie_param = self.op.cookie_param

        self.build = None

    def __call__(self, cls):
        methods = {
            func_name: func for func_name, func in cls.__dict__.items()
            if func_name in self._methods
        }

        self._pathitem_bldr(cls, methods)

        path_items = BuilderBus.path_items[cls]

        # In the case that cls's path contains formatted params,
        # such as "/users/{id:Int64}", we need to parse out the
        # acceptable parts: that is, Open API doesn't want "{name:type}",
        # just "{name}".
        path = re.sub(
            "{([^}]*)}",
            lambda mo: "{" + mo.group(1).split(':')[0] + "}",
            cls.path
        )

        if path_items:
            path_item = path_items.popleft()
            if self.build is None:
                self.build = {path: path_item}
            else:
                self.build[path] = path_item

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


class ComponentBuilder:

    schema = ComponentsObject

    def __init__(self):

        # Response builds
        self.response = self._responses
        self._response_builds = {}
        self._resp_bldr = ResponseBuilder()

        # Schema builds
        self._schema_builds = {}

        # Parameter builds
        self._parameter_builds = {}

        # Example builds
        self._examples_builds = {}

        # Request Bodies builds
        self._request_bodies_builds = {}

        # Headers builds
        self._headers_builds = {}

        # Security schemes builds
        self._security_schemes_builds = {}

        # Links builds
        self._links_builds = {}

        # Callbacks builds
        self._callbacks_builds = {}

        self._build = None

    @property
    def build(self):
        if self._build is None:
            self._build = ComponentsObject(
                **{
                    'schemas': self._schema_builds,
                    'responses': self._response_builds,
                    'parameters': self._parameter_builds,
                    'examples': self._examples_builds,
                    'request_bodies': self._request_bodies_builds,
                    'headers': self._headers_builds,
                    'security_schemes': self._security_schemes_builds,
                    'links': self._links_builds,
                    'callbacks': self._callbacks_builds
                }
            )
        return self._build

    def _responses(self, cls):
        self._resp_bldr(cls)
        responses = BuilderBus.responses[cls]
        while responses:
            _, response = responses.popleft()
            self._response_builds[cls.__name__] = response


class SecurityBuilder:

    @property
    def build(self):
        return None


class TagBuilder:

    @property
    def build(self):
        return None


class ExternalDocBuilder:

    @property
    def build(self):
        return None


class OpenApiBuilder:

    schema = OpenApiObject

    def __init__(self, version: str = '3.0.0'):
        self.version = version

        self.info = InfoBuilder()
        self.server = ServerBuilder()
        self.path = PathsBuilder()
        self.component = ComponentBuilder()
        self.security = SecurityBuilder()
        self.tag = TagBuilder()
        self.external_doc = ExternalDocBuilder()

        self._build = None

    @property
    def build(self):
        if self._build is not None:
            return self._build

        build = self.schema(
            openapi=self.version,
            info=self.info.build,
            servers=self.server.build,
            paths=self.path.build,
            components=self.component.build,
            security=self.security.build,
            tags=self.tag.build,
            external_docs=self.external_doc.build
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

    path = '/users/{id:Int64}'

    responses = [
        Response(status=200, description="ok"),
        Response(status=404, description="not found")
    ]
    request_body = RequestBody(
        description="A request body",
        content=[JSONMediaType(Int64)]
    )

    @open_bldr.path.op(summary="Some summary for the get")
    @open_bldr.path.query_param(name='email', schema=Email, required=True)
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


@open_bldr.component.response
class NotFound:

    description = "Entity not found"


@open_bldr.component.response
class IllegalInput:

    description = "Illegal input for operation"


@open_bldr.component.response
class GeneralError:

    description = "General Error"


import ruamel.yaml as yaml

with open('something.yaml', 'w') as f:
    yaml.dump(
        open_bldr.build.dict(),
        f,
        Dumper=yaml.RoundTripDumper
    )

