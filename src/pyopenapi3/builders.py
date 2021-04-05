from __future__ import annotations
from typing import get_type_hints, Union, List, Any, Dict, Optional
from collections import deque
import re

import yaml

from pyopenapi3.data_types import Component, Parameters, Schemas
from pyopenapi3.utils import (
    build_mediatype_schema_from_content,
    create_schema,
    format_description,
    parse_name_and_type_from_fmt_str,
    inject_component
)
from pyopenapi3.objects import (
    Response,
    RequestBody
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
    schema_fields = Bus('schema_fields')


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
            description=format_description(method.__doc__),
            **self._attrs[method],
        )


# Issue-75: Save any user defined Component schema so that it can
# be validated and potentially referenced by `PathItemBuilder`.
# See call to `parse_name_and_type_from_fmt_str` in `PathItemBuilder`.
_allowed_types: Dict[str, Component] = {}


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
        for name, _type in parse_name_and_type_from_fmt_str(
            path, allowed_types=_allowed_types
        ):
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

    _field_keys = set(ParameterObject.__fields__.keys())
    _field_keys.add('schema')
    _allowable_in_fields = {'path', 'query', 'header', 'cookie'}

    def __init__(self, __in):
        if __in not in self._allowable_in_fields:
            raise ValueError(
                f"{__in} is not an acceptable `in-field`. "
                f"Choices are {list(self._allowable_in_fields)}"
            )
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
            # If the schema is a reference, then return
            # the reference.
            if type(schema) == type:
                if issubclass(schema, Component):
                    return kwargs['schema']
        elif 'content' in kwargs:
            content = kwargs.pop('content')
            kwargs['content'] = build_mediatype_schema_from_content(content)
        return ParameterObject(in_field=self.__in, **kwargs)

    @classmethod
    def build_param_from_cls(cls, _cls):
        kwargs = {k: v for k, v in _cls.__dict__.items()
                  if k in cls._field_keys}
        if 'in_field' not in kwargs:
            raise ValueError(
                f"Need to include `in_field` on Parameter "
                f"class {_cls.__name__}."
            )
        return cls(kwargs.pop('in_field')).build_param(**kwargs)


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
        # A set of functions that were marked as fields for an
        # ObjectSchema that will be used to build the properties
        # of said ObjectSchema.
        self._fields_used = set()

        # Parameter builds
        self.parameter = self._parameters
        self._parameter_builds = {}

        # Example builds
        # TODO example building for Comps
        self._examples_builds = {}

        # Request Bodies interface and builds.
        self.request_body = self._request_bodies
        self._request_bodies_builds = {}
        self._rqbody_bldr = RequestBodyBuilder()

        # Headers builds
        # TODO headers building for Comps
        self._headers_builds = {}

        # Security schemes builds
        # TODO sec schemes building for Comps
        self._security_schemes_builds = {}

        # Links builds
        # TODO links building for Comps
        self._links_builds = {}

        # Callbacks builds
        # TODO callbacks building for Comps
        self._callbacks_builds = {}

        self._build = None

    def __call__(self, cls):
        # Proeprty level attrs.
        properties = {}

        # Object level attrs. See issue-76.
        # For now we specifically handle `required` because it is the only
        # field that is clearly object-level.
        # If there are any other object-level attrs, more general logic
        # should be incorporated.
        required = []

        for _f in self._fields_used:
            props = BuilderBus.schema_fields[_f].popleft()
            is_required = props.pop("required", False)
            if is_required:
                required.append(_f.__name__)
            _type = get_type_hints(_f, localns=cls.__dict__)['return']
            schema = create_schema(
                _type, description=format_description(_f.__doc__),
                **props
            )
            properties[_f.__name__] = schema

        # Flush the fields used.
        self._fields_used = set()

        self._schema_builds[cls.__name__] = ObjectsDTSchema(
            properties=properties, required=required or None
        )

        # Flush functions that were used to build this ObjectSchema.
        self._field_builds = {}

        return inject_component(cls, cmp_type=Schemas)

    def _parameters(self, cls=None, /, *, as_dict=None):
        if cls is not None:
            self._parameter_builds[cls.__name__] = \
                ParamBuilder.build_param_from_cls(cls)

            injected_comp_cls = inject_component(cls, cmp_type=Parameters)
            # Allow `cls` to be a valid reference in formatted `path`
            # on `PathItemBuilder`
            _allowed_types[cls.__name__] = injected_comp_cls
            return injected_comp_cls
        if as_dict is None:
            raise ValueError(
                "When not using the Components' parameter builder as a "
                "decorator, pass in a dict for the `as_dict` argument."
            )
        for param in as_dict:
            param_attrs = as_dict[param]
            if 'in_field' not in param_attrs:
                raise ValueError(
                    "Each parameter object must contain an `in_field` key "
                    "that is equivalent to Open API's 'in' property for "
                    "parameters."
                )
            in_field = param_attrs.pop('in_field')
            self._parameter_builds[param] = \
                ParamBuilder(in_field).build_param(**param_attrs)

    @property
    def build(self):
        # TODO allow returning None
        if self._build is None:
            self._build = ComponentsObject(
                schemas=self._schema_builds or None,
                responses=self._response_builds or None,
                parameters=self._parameter_builds or None,
                examples=self._examples_builds or None,
                request_bodies=self._request_bodies_builds or None,
                headers=self._headers_builds or None,
                security_schemes=self._security_schemes_builds or None,
                links=self._links_builds or None,
                callbacks=self._callbacks_builds or None
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

    def _field(self, func=None, /, **kwargs):

        if func is not None:
            BuilderBus.schema_fields[func] = {}
            self._fields_used.add(func)
            return func

        # Note, there is no good reason for why we can't just dump
        # the functions and any attrs (i.e. {} or kwargs), into a
        # dict hosted by ComponentsBuilder, and flushing the dict
        # after using it (note this is important, or else fields on
        # older components will be used for the current iteration).
        #
        # However, by using BuilderBus, we can try to piece out some
        # patterns to generalize this methodology. It may also read
        # easier for any other dev since it does match the pattern we've
        # been using thus far.

        def wrapper(_f):
            BuilderBus.schema_fields[_f] = kwargs
            self._fields_used.add(_f)
            return _f

        return wrapper


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

    def dict(self):
        return self.build.dict()

    def json(self, *args, **kwargs):
        return self.build.json(*args, **kwargs)

    def yaml(self):
        d = self.build.dict()
        # dump the dictionary in its current order.
        return yaml.dump(d, default_flow_style=False, sort_keys=False)
