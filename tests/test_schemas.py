from pyopenapi3.schemas import ObjectsDTSchema


def test_free_form_object():
    o = ObjectsDTSchema()

    assert o.dict() == {"type": "object"}
