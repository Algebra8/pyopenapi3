from pyopenapi3.utils import convert_primitive_to_schema
from pyopenapi3.objects import Int64


int64 = convert_primitive_to_schema(
    Int64, description="Some description",
    read_only=True, example=123
)

int2 = convert_primitive_to_schema(
    Int64, description=None, read_only=False, example=None
)





