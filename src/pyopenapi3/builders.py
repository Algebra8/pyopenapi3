from __future__ import annotations
from typing import get_type_hints, Union, List, Any, Dict, Optional
from collections import deque
import re

from pyopenapi3.utils import (
    build_mediatype_schema_from_content,
    create_schema,
    format_description,
    parse_name_and_type_from_fmt_str,
    inject_component
)
from pyopenapi3.objects import (
    Response,
    RequestBody,
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
    ComponentsObject,
    ObjectsDTSchema,
    TagObject,
    ExternalDocObject
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

    _field_keys = RequestBodyObject.__fields__.keys()

    def __call__(
            self, cls=None, /, *,
            request_body: Optional[
                Union[RequestBody, Dict[str, Any], Any]
            ] = None,
            sub: Optional[Any] = None
    ) -> None:
        if cls is not None:
            rqbody_attrs = {name: attr for name, attr in cls.__dict__.items()
                            if name in self._field_keys}
            self.__call__(request_body=rqbody_attrs, sub=cls)
            return cls

        if request_body in [..., None]:
            return

        if isinstance(request_body, RequestBody):
            request_body = request_body.as_dict()

        content = build_mediatype_schema_from_content(request_body['content'])
        description = request_body.get('description')
        required = request_body.get('required')

        BuilderBus.request_bodies[sub] = RequestBodyObject(
            content=content,
            description=description,
            required=required
        )


class ResponseBuilder:

    _field_keys = ResponseObject.__fields__.keys()

    def __call__(
            self, cls=None, /, *,
            responses: Optional[List[Union[Response, Dict[str, Any]]]] = None,
            sub: Optional[Any] = None
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

        self._rqbody_bldr(request_body=request_body, sub=method)
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

        # Response interface and builds.
        self.response = self._responses
        self._response_builds = {}
        self._resp_bldr = ResponseBuilder()

        # Schema interface and builds.
        self.schema = self.__call__
        self._schema_builds = {}
        self.schema_field = self._field
        self._field_builds = {}

        # Parameter builds
        self._parameter_builds = {}

        # Example builds
        self._examples_builds = {}

        # Request Bodies interface and builds.
        self.request_body = self._request_bodies
        self._request_bodies_builds = {}
        self._rqbody_bldr = RequestBodyBuilder()

        # Headers builds
        self._headers_builds = {}

        # Security schemes builds
        self._security_schemes_builds = {}

        # Links builds
        self._links_builds = {}

        # Callbacks builds
        self._callbacks_builds = {}

        self._build = None

    def __call__(self, cls):
        properties = {}
        for _f, props in self._field_builds.items():
            _type = get_type_hints(_f, localns=cls.__dict__)['return']
            schema = create_schema(
                _type, description=format_description(_f.__doc__),
                **props
            )
            properties[_f.__name__] = schema

        self._schema_builds[cls.__name__] = ObjectsDTSchema(
            properties=properties
        )

        injected_comp_cls = inject_component(cls)
        return injected_comp_cls

    def _field(self, func=None, /, **kwargs):
        if func is not None:
            self._field_builds[func] = {}
            return func

        def wrapper(_f):
            self._field_builds[_f] = kwargs
            return _f

        return wrapper

    @property
    def build(self):
        if self._build is None:
            self._build = ComponentsObject(
                schemas=self._schema_builds,
                responses=self._response_builds,
                parameters=self._parameter_builds,
                examples=self._examples_builds,
                request_bodies=self._request_bodies_builds,
                headers=self._headers_builds,
                security_schemes=self._security_schemes_builds,
                links=self._links_builds,
                callbacks=self._callbacks_builds
            )
        return self._build

    def _responses(self, cls):
        self._resp_bldr(cls)
        responses = BuilderBus.responses[cls]
        while responses:
            _, response = responses.popleft()
            self._response_builds[cls.__name__] = response

    def _request_bodies(self, cls):
        self._rqbody_bldr(cls)
        rqbodies = BuilderBus.request_bodies[cls]
        while rqbodies:
            rqbody = rqbodies.popleft()
            self._request_bodies_builds[cls.__name__] = rqbody


# TODO Security Requirement Object.
class SecurityBuilder:

    @property
    def build(self):
        return None


class TagBuilder:

    schema = TagObject
    _field_keys = TagObject.__fields__.keys()

    def __init__(self):
        self._builds = []

    def __call__(self, cls):
        tag_object = self.schema(
            **{k: v for k, v in cls.__dict__.items()
               if k in self._field_keys}
        )
        self._builds.append(tag_object)

        return cls

    @property
    def build(self):
        return self._builds or None


class ExternalDocBuilder:

    schema = ExternalDocObject
    _field_keys = ExternalDocObject.__fields__.keys()

    def __init__(self):
        self._build = None

    def __call__(self, cls):
        exdoc = self.schema(
            **{k: v for k, v in cls.__dict__.items()
               if k in self._field_keys}
        )
        self._build = exdoc

    @property
    def build(self):
        return self._build


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
        if self._build is None:
            self._build = self.schema(
                openapi=self.version,
                info=self.info.build,
                servers=self.server.build,
                paths=self.path.build,
                components=self.component.build,
                security=self.security.build,
                tags=self.tag.build,
                external_docs=self.external_doc.build
            )

        return self._build
