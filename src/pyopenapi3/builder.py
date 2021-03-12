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
    map_field_to_schema
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


"""
We should wind up with something like,

definitions:
    Customer:
        ...
    Store:
        ...
    ...

Or

components:
    schemas:
        Customer:
            ...
        Store:
            ...


Here, the path gets built up to a URI. 
In the first case, we would have '#/definitions/Customer' and 
in the second we would have '#/components/schemas/Customer'.

Since the path is a variable, it should be built up or included upon
initialization for the Builder.

Builder(path='definitions')
Or
Builder(path='components/schemas')

This seems like a good place to begin describing different types
of builders.

The paths described above are directly related to building a schema.

Therefore, what is called `Builder` now should probably be changed to 
`SchemaBuilder`.

This frees conceptual resources to create other builders such as 

`PathBuilder`, for api paths
`TagBuilder`, for tags
`ServerBuilder`, for everything related to the server, such as "HTTPS Scheme"
`InfoObjectBuilder`
`ComponentBuilder`
`SecurityBuilder`
`BuilderBuilder`, this is a poor name but should be what the client sees 
and uses to build their template.
"""


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


class ParamBuilder:

    defn = '__OPENAPIDEF_PARAM__'
    _schema = ParamSchema

    def __init__(self, __in: str, subscriber=None):
        # What type of param is being built.
        # Can be a path, query, header, or cookie parameter.
        self.__in = __in
        self.subscriber = subscriber

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

        # The params are per method. E.g. `get` can have multiple
        # query parameters or `post` can have header parameters, etc.
        # Therefore, params are attached as a `list` on the methods
        # themselves.
        def wrapper(method):
            self.subscriber.update(
                publisher=self, method=method.__name__, data=param
            )
            return method

        return wrapper

    @classmethod
    def get_params_from_method(cls, method) -> Any:
        if hasattr(method, cls.defn):
            return getattr(method, cls.defn)

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

    method_defn = '__OPENAPIDEF_METHOD__'

    def __init__(self):
        self.query_param = ParamBuilder('query', self)
        self.header_param = ParamBuilder('header', self)
        self.cookie_param = ParamBuilder('cookie', self)

        self._method_params = None

        # There can be multiple `paths`, so they are
        # represented as an array.
        self.builds = None  # type: PathMappingSchema

    def update(self, publisher, method, data):
        if isinstance(publisher, ParamBuilder):
            if self._method_params is None:
                self._method_params = {}
            if method not in self._method_params:
                self._method_params = {method: [data]}
            else:
                self._method_params[method].append(data)



    def __call__(
            self, *,
            tags: Optional[List[str]] = None,
            summary: Optional[str] = None,
            operation_id: Optional[str] = None,
            # TODO external docs
            external_docs: Any = None
    ):
        # Get path and any formatted path params.
        #   - Create the parameter using the schema provided.
        # Go through each method and weed out the HTTP methods,
        # such as `get`, `post`, etc.
        #   - Get requestBody and Responses from return annotations
        #   - Get query params from method params annotations
        #   - Build the request body
        #   - Build the responses
        #   - Build the query params

        # iterate over methods
        def wrapper(f_or_cls):
            if inspect.isclass(f_or_cls):
                _cls = f_or_cls

                # Build the `path` param, e.g. `path = '/users/{id:Int64}'`,
                # then each method should include an "in: path" param with
                # the type schema provided in the formatted string.

                # Here we extract any formatted string parameters.
                # Note there could be multiple for a single `path`.
                path = _cls.path
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
                        _cls.path
                    )

                # Here we do two things:
                #   - get the schemas from each method, e.g. `get`, `post`.
                #   - bake in the path param extracted above, if there is one.
                http_mapping = {}
                for name, val in _cls.__dict__.items():
                    if name.lower() not in self._methods:
                        continue

                    method_name = name.lower()
                    if not hasattr(val, self.method_defn):
                        # TODO error handling, error message
                        raise ValueError(
                            f'Http method {name} declared without any tags.'
                        )
                    method_schema: HttpMethodSchema
                    method_schema = getattr(val, self.method_defn)
                    if method_schema is None:
                        # TODO error message.
                        raise ValueError(
                            f"HTTP method {method_name} must at least "
                            f"contain a response"
                        )

                    # parameters should be none here.
                    # Can have path params and other params.
                    method_params = path_params
                    if self._method_params is not None:
                        method_params += self._method_params.get(method_name, [])
                    # Don't need to validate since path param
                    # was already validated.
                    method_schema.parameters = method_params
                    # if method_schema.parameters is None:
                    #     method_schema.parameters = path_params
                    #     if self._method_params is not None:
                    #
                    # else:
                    #     method_schema.parameters += path_params
                    http_mapping[method_name] = method_schema

                try:
                    http_mapping_schema = \
                        HttpMethodMappingSchema(**http_mapping)
                except ValidationError as e:
                    # TODO error handling.
                    raise ValueError(f"nooo\n{e.json()}")
                finally:
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
            else:
                _f = f_or_cls

                # Parse the responses and request body from the annots
                # and then validate them.
                #
                # The request, responses could look like this:
                # `def get(self) -> (RequestBody(...), [Responses(...)]): ...`,
                # or they could be wrapped in a typing.Tuple.
                #
                # Once they are validated they can be attached to the
                # given method.
                request_body: Union[RequestBody, Dict[str, Any]]
                responses: List[Union[Response, Dict[str, Any]]]

                method_annots = _f.__annotations__['return']
                if hasattr(method_annots, '_name'):
                    # typing.Tuple
                    request_body, responses = method_annots.__args__
                else:
                    request_body, responses = method_annots

                # Request body schema building.
                if isinstance(request_body, RequestBody):
                    # Need to validate the attrs.
                    request_body = request_body.as_dict()
                # TODO error handling
                if 'content' not in request_body:
                    raise ValueError(
                        "'content' has not been provided "
                        f"in the request body for {_f.__name__}"
                    )
                # Need to find out what kind of schema the content is,
                # if there is one.
                request_schema_tp = RequestBodySchema
                content = {}
                for media_type, field_type in request_body['content']:
                    field_schema_tp = map_field_to_schema(
                        field_type, is_reference=True
                    )
                    content[media_type] = SchemaMapping[field_schema_tp](
                        schema=create_schema(field_type, is_reference=True)
                    )
                try:
                    request_body_schema = request_schema_tp(
                        description=request_body.get('description'),
                        required=request_body.get('required'),
                        content=content
                    )
                except ValidationError as e:
                    # TODO error handling
                    raise ValueError(f"Uh oh:\n{e.json()}") from None

                # Response schema building.
                response_schemas = {}
                for response in responses:
                    # description is not optional,
                    # content is.
                    if isinstance(response, Response):
                        # Need to validate the attrs.
                        response = response.as_dict()

                    # If content is empty, then don't need to specify
                    # generic schema type.
                    response_schema_tp = ResponseSchema
                    content = {}  # if not empty, will be used in schema
                    response_content = response.get('content')
                    if response_content is not None:
                        for media_type, field_type in response_content:
                            field_schema_tp = map_field_to_schema(
                                field_type, is_reference=True
                            )
                            content[media_type] = \
                                SchemaMapping[field_schema_tp](
                                    schema=create_schema(
                                        field_type,
                                        is_reference=True
                                    )
                                )
                    try:
                        response_schema = response_schema_tp(
                            # description is a required field.
                            description=response['description'],
                            content=(content or None),
                        )
                    except ValidationError as e:
                        # TODO Error handling
                        raise ValueError(f"OOOPS:\n{e.json()}")

                    # status is a required field for the `Response` object
                    # and is needed to map `HttpMethodSchema.responses`
                    # to a `ResponseSchema`.
                    response_schemas[response['status']] = response_schema

                # Here we can build the rest of the HttpMethodSchema.
                method_schema = HttpMethodSchema(
                    tags=tags, summary=summary, operation_id=operation_id,
                    description=_format_description(_f.__doc__),
                    # Get any type of param except for the path.
                    # The path param is retrieved from `path` set on the
                    # clients class, which won't be reached until we run
                    # through the class itself.
                    parameters=ParamBuilder.get_params_from_method(_f),
                    responses=response_schemas,
                    request_body=request_body_schema
                    # TODO don't ignore external docs
                )

                setattr(_f, self.method_defn, method_schema)

            return f_or_cls

        return wrapper

    def flush(self):
        self._method_params = None


class OpenApiBuilder:
    """Super builder for Open API 3.0.0 document.

    The client interfaces with this builder and this builder
    has other builders embedded within it, which should be
    accessed by the client to build those parts.
    """
    component = ComponentBuilder
    info = InfoObjectBuilder

    def __init__(self):
        self.component = ComponentBuilder()
        self.info = InfoObjectBuilder()
        self.server = ServerBuilder()
        self.path = PathBuilder()

        self.builds = {}

    def as_dict(self):
        info = self.info.as_dict()
        servers = self.server.as_dict()
        comp = self.component.as_dict()
        self.builds = OrderedDict([
            ("info", info["info"]),
            ("servers", servers["servers"]),
            ("components", comp["components"])
        ])
        return self.builds

    def as_yaml(self, filename):
        with make_yaml_ordered(yaml) as _yaml:
            with open(filename, 'w') as f:
                _yaml.dump(self.as_dict(), f, allow_unicode=True)
