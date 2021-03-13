from typing import Dict, Any, Optional, List, Union, Type
import yaml
import inspect
from collections import OrderedDict
import re

from pydantic import ValidationError  # type: ignore

from .utils import (
    build_property_schema_from_func,
    mark_component_and_attach_schema,
    parse_name_and_type_from_fmt_str,
    create_schema,
    inject_component,
    _format_description,
    map_field_to_schema,
    build_content_schema_from_content
)

from .objects import Field, Component, RequestBody, Response
from .schemas import (
    InfoSchema,
    ServerSchema,
    ResponseSchema,
    RequestBodySchema,
    ParamSchema,
    PathMappingSchema,
    HttpMethodSchema,
    SchemaMapping,
    HttpMethodMappingSchema,
)
from ._yaml import make_yaml_ordered


class ComponentBuilder:

    def __init__(self):
        self.builds: Dict[str, Any] = {}

    def __call__(
            self, *,
            read_only: bool = False,
            example: Optional[Any] = None,
    ):
        def wrapper(f_or_cls):

            if inspect.isclass(f_or_cls):
                # Classes will get decorated **after** their methods.
                # This leaves us with the opportunity to collect all
                # the necessary builds and neatly package it in `builds`
                # for the OpenApiObject.
                _cls = inject_component(f_or_cls)

                self.builds[_cls.__name__] = create_schema(
                    _cls, description=_cls.__doc__,
                    # This is the only place we would build the
                    # actual object, everywhere else would use
                    # a reference.
                    is_reference=False
                )

                # The 'injected' class should be returned
                # so that other classes that use this class
                # as a property will be able to find it.
                f_or_cls = _cls
            else:
                # A wrapped method.
                _f = f_or_cls

                # Build the property for the given custom Component
                # object, e.g. {'id': {'type': 'integer'}}
                component_schema = build_property_schema_from_func(
                    _f, read_only=read_only, example=example
                )

                # This will be used by other utils to find
                # schemas and build them.
                mark_component_and_attach_schema(
                    _f,
                    {_f.__name__: component_schema}
                )

                f_or_cls = _f

            return f_or_cls

        return wrapper

    def dump(self, *a, **kw):
        return self, a, kw

    def as_yaml(self, filename):
        with make_yaml_ordered(yaml) as _yaml:
            with open(filename, 'w') as f:
                _yaml.dump(self.builds, f, allow_unicode=True)

    def as_dict(self):
        schemas = {
            name: schema.dict()
            for name, schema in self.builds.items()
        }
        return {
            'components': {
                'schemas': schemas
            }
        }


class InfoObjectBuilder:
    """The Open API 3.0.0 Info Object builder.

    Provides metadata about the API.
    """

    _schema = InfoSchema
    _field_keys = InfoSchema.__fields__.keys()

    def __init__(self):
        self.builds = None  # type: InfoSchema

    def __call__(self, cls):
        try:
            info_object = self._schema(
                **{k: v for k, v in cls.__dict__.items()
                   if k in self._field_keys}
            )
        except ValidationError as e:
            # TODO Better error handling
            print(e.json())
        else:
            # Pydantic *should* maintain ordering since
            # we made sure to use type annotations to
            # all fields.
            # See:
            # https://pydantic-docs.helpmanual.io/usage/models/#required-fields
            self.builds = info_object

    def as_dict(self):
        return {'info': self.builds.dict()}


# TODO Nullable values should not be included with regards to pydantic objects.

class ServerBuilder:
    """Server builder for Open API 3.0.0 document.

    As per the Open API 3.0.0 spec, the ServerBuilder will build
    an array of `ServerObject`s.

    If the servers property is not provided, or is an empty array,
    the default value would be an Open API Server Object with a url
    value of /.
    """

    # If you are wondering why we only need ServerSchema and
    # not ServerVariableSchema, it is because the client should
    # only interface with the ServerSchema.
    #
    # Any `ServerVariableSchema` will be a concrete `dict` attached to
    # the class representing the Server object:
    #
    #     class SomeServer:
    #         url = '/path/to/thing'
    #         description = 'Some server'
    #         variables = [{'default': 'a'}, {'default': 'b'}]
    #
    # So, once we pull out the `ServerSchema`'s attrs, pydantic
    # should do all the heavy lifting.
    _schema = ServerSchema
    _field_keys = ServerSchema.__fields__.keys()

    def __init__(self):
        # The servers section can contain one or more Server objects.
        self._builds: List[ServerSchema] = []

    @property
    def builds(self) -> List[ServerSchema]:
        if not self._builds:
            # servers have not been provided, a default
            # server with a url value of '/' will be provided.
            return [
                self._schema(url='/', description="Default server")
            ]
        return self._builds

    def __call__(self, cls):
        try:
            server_object = self._schema(
                **{k: v for k, v in cls.__dict__.items()
                   if k in self._field_keys}
            )
        except ValidationError as e:
            # TODO Error handling; if returned don't forget
            #  to remove the else block
            print(vars(e))
            print(e.json())
        else:
            self._builds.append(server_object)

    def as_dict(self):
        return {"servers": [schema.dict() for schema in self.builds]}


class Event:

    method: str
    data: Any


class ParamBuilder:

    _schema = ParamSchema

    def __init__(self, __in: str, subscriber_callback=None):
        # What type of param is being built.
        # Can be a path, query, header, or cookie parameter.
        self.__in = __in

        # Subscriber will be updated with the params during
        # wrapping with __call__.
        # Otherwise, they can get the build directly through
        # `build_param`.
        self.subscriber_callback = subscriber_callback

    def __call__(
            self, *, name: str,
            # `field` may seem like a misnomer since `Component`
            # is not a type of `Field`, but lower-cased `field`
            # should not be confused with the `Field` type.
            field: Union[Type[Field], Type[Component]],
            required: bool = False,
            allow_reserved: bool = False,
            description: Optional[str] = None
    ):
        param = self.build_param(
            name=name, field=field, required=required,
            allow_reserved=allow_reserved,
            description=description
        )

        def wrapper(method):
            e = Event()
            e.method = method.__name__
            e.data = param
            self.subscriber_callback(e)
            return method

        return wrapper

    def build_param(
            self, *, name: str,
            field: Union[Type[Field], Component],
            required: bool = False,
            allow_reserved: bool = False,
            description: Optional[str] = None
    ) -> ParamSchema:
        try:
            param = self._schema(
                name=name, in_field=self.__in,
                description=description, required=required,
                allow_reserved=allow_reserved,
                schema=create_schema(field)
            )
        except ValidationError as e:
            # TODO Error handling
            print(e.json())
            raise ValueError(f"Something didn't work: {e.json()}") from None

        return param


class RequestBodyBuilder:

    def __init__(self, subscriber_callback=None):
        self.subscriber_callback = subscriber_callback

    def build_from_request_body(
            self,
            method_name: str,
            request_body: Union[Dict[str, Any], RequestBody]
    ) -> Optional[RequestBodySchema]:
        if request_body is Ellipsis:
            return

        if method_name == 'get':
            raise ValueError("GET operations cannot have a request body.")

        if isinstance(request_body, RequestBody):
            request_body = request_body.as_dict()

        if 'content' not in request_body:
            raise ValueError(
                "'content' has not been provided "
                f"in the request body for {method_name}"
            )

        content = build_content_schema_from_content(request_body['content'])

        try:
            request_body_schema = RequestBodySchema(
                description=request_body.get('description'),
                required=request_body.get('required'),
                content=content
            )
        except ValidationError as e:
            # TODO error handling
            raise ValueError(f"Uh oh:\n{e.json()}") from None

        if self.subscriber_callback is not None:
            e = Event()
            e.method = method_name
            e.data = request_body_schema
            self.subscriber_callback(e)
        else:
            return request_body_schema


class ResponseBuilder:

    def __init__(self, subscriber_callback=None):
        self.subscriber_callback = subscriber_callback

    @staticmethod
    def build_from_response(
            response: Union[Dict[str, Any], Response]
    ) -> Dict[str, ResponseSchema]:
        if isinstance(response, Response):
            response = response.as_dict()

        content = build_content_schema_from_content(response.get('content'))

        try:
            response_schema = ResponseSchema(
                # description is a required field.
                description=response['description'],
                content=(content or None),
            )
        except ValidationError as e:
            # TODO Error handling
            raise ValueError(f"OOOPS:\n{e.json()}")

        return {response['status']: response_schema}

    def build_from_responses(
            self,
            method_name: str,
            responses: List[Union[Dict[str, Any], Response]]
    ) -> Optional[Dict[str, ResponseSchema]]:
        response_schemas_per_method = {}
        for response in responses:
            response_schemas_per_method.update(
                self.build_from_response(response)
            )

        if self.subscriber_callback is not None:
            e = Event()
            e.method = method_name
            e.data = response_schemas_per_method
            self.subscriber_callback(e)
        else:
            return response_schemas_per_method


class MethodMetaDataBuilder:

    def __init__(self, subscriber_callback=None):
        self.subscriber_callback = subscriber_callback

    def __call__(
            self, *,
            tags: Optional[List[str]] = None,
            summary: Optional[str] = None,
            operation_id: Optional[str] = None,
            # TODO external docs
            external_docs: Any = None
    ):
        data = {
            'tags': tags,
            'summary': summary,
            'operation_id': operation_id,
        }

        def wrapper(method):
            e = Event()
            e.method = method.__name__
            e.data = data
            self.subscriber_callback(e)
            return method
        return wrapper


class PathBuilder:
    """Path (aka endpoint), builder for Open API 3.0.0.

    The `PathBuilder` holds an array of paths and delegates
    the building of substructures, such as the Responses, to
    other builders.
    """

    _methods = {
        'get', 'post', 'put', 'patch',
        'delete', 'head', 'options',
        'trace'
    }

    def __init__(self):
        # Client facing builders/publishers for params
        # and http method metadata.
        self.query_param = ParamBuilder('query', self.update_params)
        self.header_param = ParamBuilder('header', self.update_params)
        self.cookie_param = ParamBuilder('cookie', self.update_params)
        self.meta = MethodMetaDataBuilder(self.update_http_meta)

        # Builders/publishers for request body and responses.
        self._reqbody_builder = RequestBodyBuilder(self.update_request_body)
        self._response_builder = ResponseBuilder(self.update_responses)

        # Containers for builds per class. Need to be `flush`ed
        # after every class wrapping.
        self._method_params = None
        self._reqbody_schemas = None
        self._response_schemas = None
        self._meta_info = None

        self.builds = None  # type: PathMappingSchema

    def update_params(self, e: Event):
        method, data = e.method, e.data
        if self._method_params is None:
            self._method_params = {}

        # We have several PathBuilder publishers.
        if method in self._method_params:
            self._method_params[method].append(data)
        else:
            self._method_params[method] = [data]

    def update_http_meta(self, e: Event):
        method, data = e.method, e.data
        if self._meta_info is None:
            self._meta_info = {}
        self._meta_info[method] = data

    def update_request_body(self, e: Event):
        method, data = e.method, e.data

        if self._reqbody_schemas is None:
            self._reqbody_schemas = {}
        self._reqbody_schemas[method] = data

    def update_responses(self, e: Event):
        method, data = e.method, e.data
        if self._response_schemas is None:
            self._response_schemas = {}
        self._response_schemas[method] = data

    def __call__(self, cls):
        # Get path and any formatted path params.
        #   - Create the parameter using the schema provided.
        # Go through each method and weed out the HTTP methods,
        # such as `get`, `post`, etc.
        #   - Get requestBody and Responses from return annotations
        #   - Get query params from method params annotations
        #   - Build the request body
        #   - Build the responses
        #   - Build the query params

        # Build the `path` param, e.g. `path = '/users/{id:Int64}'`,
        # then each method should include an "in: path" param with
        # the type schema provided in the formatted string.

        # Here we extract any formatted string parameters.
        # Note there could be multiple for a single `path`.
        path = cls.path
        path_params = []
        for name, _type in parse_name_and_type_from_fmt_str(path):
            path_param = ParamBuilder('path').build_param(
                name=name,
                field=_type,
                required=True
            )
            path_params.append(path_param)

        if path_params:
            # Open API doesn't want "{name:type}", just "{name}".
            path = re.sub(
                "{([^}]*)}",
                lambda mo: "{" + mo.group(1).split(':')[0] + "}",
                cls.path
            )

        # Here we do two things:
        #   - get the schemas from each method, e.g. `get`, `post`.
        #   - bake in the path params extracted above, if there are any.
        http_method_methods = {
            func_name.lower(): func for func_name, func in cls.__dict__.items()
            if func_name.lower() in self._methods
        }
        http_mapping = {}
        for method_name, method in http_method_methods:
            # Get a methods responses and requests: unlike the meta info
            # and params, responses and requests are parsed and built
            # from the class's methods directly.
            method_annots = method.__annotations__['return']
            if hasattr(method_annots, '_name'):
                # typing.Tuple
                request_body, responses = method_annots.__args__
            else:
                request_body, responses = method_annots

            self._reqbody_builder.build_from_request_body(
                method_name, request_body
            )
            self._response_builder.build_from_responses(
                method_name, responses
            )

            # Get schemas for this method.
            meta_info = (self._meta_info or {}).get(method_name, {})

            params_for_method = []
            if self._method_params is not None:
                params_for_method += self._method_params.get(method_name, [])
            params_for_method += path_params

            reqbody_for_method = (self._reqbody_schemas or {}).get(method_name)

            responses_for_method = self._response_schemas.get(method_name)
            if responses_for_method is None:
                raise ValueError(
                    "Must include at least one response per method."
                )

            # Here we can build the HttpMethodSchema...
            try:
                method_schema = HttpMethodSchema(
                    tags=meta_info.get('tags'),
                    summary=meta_info.get('summary'),
                    operation_id=meta_info.get('operation_id'),
                    description=_format_description(method.__doc__),
                    # Params are validated separately.
                    parameters=(params_for_method or None),
                    responses=responses_for_method,
                    request_body=reqbody_for_method
                    # TODO don't ignore external docs
                )
            except ValidationError as e:
                raise ValueError(f"oops:\n{e.json()}")

            # ..., and map it to the method.
            http_mapping[method_name] = method_schema

        try:
            http_mapping_schema = \
                HttpMethodMappingSchema(**http_mapping)
        except ValidationError as e:
            # TODO error handling.
            raise ValueError(f"nooo\n{e.json()}")
        finally:
            # TODO Maybe the client is ok with handling one of the paths
            #  breaking and this should stay in a finally block? Or does
            #  this send mixed signals?
            self.flush()

        if self.builds is None:
            try:
                self.builds = PathMappingSchema(
                    paths={path: http_mapping_schema}
                )
            except ValidationError as e:
                # TODO error handling.
                raise ValueError(f"oopsy:\n{e.json()}")
        else:
            # Not the first path, so `builds` can contain
            # other paths at this point, and we are inserting
            # a new one.
            z = self.builds.dict()
            z['paths'][path] = http_mapping_schema
            try:
                self.builds = PathMappingSchema(**z)
            except ValidationError as e:
                # TODO Error handling.
                raise ValueError(f"UUHuh:\n{e.json()}")

        return cls

    def flush(self):
        self._method_params = None
        self._reqbody_schemas = None
        self._response_schemas = None
        self._meta_info = None

    def as_dict(self):
        return self.builds.dict()


class OpenApiBuilder:
    """Super builder for Open API 3.0.0 document.

    The client interfaces with this builder and this builder
    has other builders embedded within it, which should be
    accessed by the client to build those parts.
    """
    component = ComponentBuilder
    info = InfoObjectBuilder

    def __init__(self, version: str = '3.0.0'):
        self.component = ComponentBuilder()
        self.info = InfoObjectBuilder()
        self.server = ServerBuilder()
        self.path = PathBuilder()

        self.version = {'openapi': version}

        self.builds = {}

    def as_dict(self):
        info = self.info.as_dict()
        servers = self.server.as_dict()
        comp = self.component.as_dict()
        paths = self.path.as_dict()
        self.builds = OrderedDict([
            ("openapi", self.version["openapi"]),
            ("info", info["info"]),
            ("servers", servers["servers"]),
            ("paths", paths['paths']),
            ("components", comp["components"])
        ])
        return self.builds

    def as_yaml(self, filename):
        with make_yaml_ordered(yaml) as _yaml:
            with open(filename, 'w') as f:
                _yaml.dump(self.as_dict(), f, allow_unicode=True)
