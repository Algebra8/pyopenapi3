from typing import TypedDict, Optional, Any, Dict


class OpenApiSchema(TypedDict):

    type: str
    description: str


SchemaMap = Dict[str, OpenApiSchema]


class PrimitiveSchema(OpenApiSchema, total=False):

    format: str
    example: Optional[Any]
    readOnly: Optional[bool]


class ArraySchema(OpenApiSchema, total=False):

    items: Any


class ObjectSchema(OpenApiSchema):

    properties: SchemaMap


class OpenApiObject:
    ...
