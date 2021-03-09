from typing import Dict, Any, Optional, List, Union, Type
import yaml
import inspect
from collections import OrderedDict

from pydantic import ValidationError  # type: ignore

from .utils import (
    build_property_schema_from_func,
    mark_component_and_attach_schema,
    get_name_and_type,
    create_schema,
    inject_component
)

from .objects import Field, Component
from .schemas import (
    InfoSchema,
    ServerSchema,
    Response,
    RequestBody,
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

    # If you are wondering why we only need ServerObject attrs and
    # not ServerVariableObject attrs, it is because the client should
    # interface with the ServerObject.
    #
    # Any ServerVariableObject will be a concrete attr attached to
    # the class representing the Server object:
    #
    #     class SomeServer:
    #         url = '/path/to/thing'
    #         description = 'Some server'
    #         variables = [{'default': 'a'}, {'default': 'b'}]
    #
    # So, once we pull out the `ServerObject`'s attrs, pydantic
    # will do all the heavy lifting.
    _schema = ServerSchema
    _field_keys = ServerSchema.__fields__.keys()

    def __init__(self):
        # The servers section can contain one or more Server Objects.
        self._builds: List[ServerSchema] = []

    @property
    def builds(self):
        if not self._builds:
            # servers have not been provided, a default
            # server with a url value of '/' will be provided.
            return self._schema(
                url='/', description="Default server"
            )
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
        return {"servers": self.builds.dict()}


class ParamBuilder:

    defn = '__OPENAPIDEF__PARAM__'

    def __init__(self, __in: str):
        # What type of param is being built.
        # Can be a path, query, header, or cookie parameter.
        self.__in = __in

    def __call__(
            self, *, name: str,
            schema_type: Union[Type[Field], Type[Component]],
            required: bool = False,
            allow_reserved: bool = False
    ):
        param = self.build_param(
            name=name, schema_type=schema_type,
            required=required, allow_reserved=allow_reserved
        )

        def wrapper(method):
            if not hasattr(method, self.defn):
                setattr(method, self.defn, [param])
            else:
                getattr(method, self.defn).append(param)
            return method

        return wrapper

    @classmethod
    def get_params_from_method(cls, method):
        return getattr(method, cls.defn)

    def build_param(
            self, *, name: str,
            schema_type: Union[Type[Field], Component],
            required: bool = False,
            allow_reserved: bool = False
    ):
        param = {
            'in': self.__in,
            'name': name,
            'schema': create_schema(schema_type)
        }

        if required:
            param['required'] = True
        if allow_reserved:
            param['allowReserved'] = True

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

    method_defn = '__OPENAPIDEF__METHOD__'

    def __init__(self):
        self.query_param = ParamBuilder('query')
        self.header_param = ParamBuilder('header')
        self.cookie_param = ParamBuilder('cookie')

        # `paths` can be multiple paths, so they are
        # represented as an array.
        self.builds = []

    def __call__(
            self, *,
            tags: Optional[List[str]] = None,
            summary: Optional[str] = None,
            operation_id: Optional[str] = None,
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

                path_params = []
                for path_name, schema_type in get_name_and_type(_cls.path):
                    path_param = ParamBuilder('path').build_param(
                        name=path_name,
                        schema_type=schema_type,
                        required=True
                    )
                    path_params.append(path_param)

                schema = {}
                for name, val in _cls.__dict__.items():
                    if name.lower() in self._methods:
                        method_name = name.lower()
                        schema[method_name] = getattr(val, self.method_defn)
                        # Here we finally append the path param.
                        schema[method_name]['parameters'].append(path_params)

                self.builds.append(schema)
            else:
                _f = f_or_cls

                schema = {}
                if tags is not None:
                    schema['tags'] = tags
                if summary is not None:
                    schema['summary'] = summary
                if operation_id is not None:
                    schema['operationId'] = operation_id
                if _f.__doc__ is not None:
                    schema['description'] = _f.__doc__

                # Get any type of param except for the path.
                # The path param is retrieved from `path` set on the
                # clients class, which won't be reached until we run
                # through the class itself. Notice that there is no
                # cls.path_param, but there are other types of params.
                schema['parameters'] = ParamBuilder.get_params_from_method(_f)

                # Parse the responses and request body from the annots
                # and then validate them.
                # Once they are validated they can be attached to the
                # given method.
                method_annots = _f.__annotations__['return']
                request_body: Union[RequestBody, Dict[str, Any]]
                responses: List[Union[Response, Dict[str, Any]]]
                if hasattr(method_annots, '_name'):
                    # typing.Tuple
                    request_body, responses = method_annots.__args__
                else:
                    request_body, responses = method_annots

                _validated_request_body: Dict[str, Any]
                _validated_responses: List[Dict[str, Any]] = []
                if not isinstance(request_body, RequestBody):
                    # Need to validate the attrs.
                    try:
                        RequestBody(**request_body)
                    except ValidationError as e:
                        # TODO better error handling
                        print(e.json())
                        return
                    else:
                        _validated_request_body = request_body
                else:
                    _validated_request_body = request_body.dict()

                for response in responses:
                    if not isinstance(response, Response):
                        try:
                            Response(**response)
                        except ValidationError as e:
                            # TODO better error handling
                            print(e.json())
                            return
                        else:
                            _validated_responses.append(response)
                    else:
                        _validated_responses.append(response.dict())

                schema['requestBody'] = _validated_request_body
                schema['responses'] = _validated_responses

                setattr(_f, self.method_defn, schema)

            return f_or_cls

        return wrapper

    # @staticmethod
    # def _create_param(name, _type):
    #     schema = {
    #         'name': None,
    #         'in': None,
    #         'description': None,
    #         'required':
    #     }
    #
    #     return name


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
