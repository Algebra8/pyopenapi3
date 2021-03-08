from typing import Type, Optional
import functools


class Schema(str):
    ...


class PrimitiveSchema(Schema):
    ...


class ArraySchema(Schema):
    ...


class ComponentSchema(Schema):
    ...


class ReferenceSchema(ComponentSchema):
    ...


class OpenApiObject:
    ...


class Field(OpenApiObject):
    ...


class Primitive(Field):
    ...


class Array(Field):
    ...


class Component(OpenApiObject):
    ...


class Reference(OpenApiObject):
    ...


def create_schema(
        __type: Type[OpenApiObject],
        *args,
        is_reference: Optional[bool] = None,
        **kwargs
) -> Schema:
    # if __type is a Primitive -> return PrimitiveSchema
    if issubclass(__type, Primitive):
        convert_primitive_to_schema(__type)
    # if __type is an Array -> return ArraySchema
    if issubclass(__type, Array):
        return convert_array_to_schema(__type)
    # if __type is a Component -> return ComponentSchema
    if issubclass(__type, Component):
        return convert_component_to_schema(__type, is_reference)


def convert_primitive_to_schema(primitive: Type[Primitive]) -> PrimitiveSchema:
    return PrimitiveSchema(f"Primitive Schema {primitive}")


def convert_array_to_schema(array: Type[Array]) -> ArraySchema:
    return ArraySchema(f"ArraySchema {array}")


def convert_component_to_schema(
        component: Type[Component],
        is_reference: bool
) -> ComponentSchema:
    assert is_reference is not None

    if is_reference:
        return ReferenceSchema(f"ReferenceSchema {component}")
    else:
        return ComponentSchema(f"ComponentSchema {component}")


# TODO Use this for marking something as a component type.
def inject_component(cls):
    if issubclass(cls, Component):
        return cls
    else:
        class Injected(cls, Component):
            ...
        Injected.__qualname__ = f'Component[{cls.__name__}]'
        Injected.__name__ = cls.__name__
        return Injected


@inject_component
class B:

    f = 'asd'

    def get_thing(self):
        return f'thing {self}'

