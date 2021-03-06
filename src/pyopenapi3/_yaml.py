import contextlib
import importlib
from collections import OrderedDict

import yaml


# Stuff for yaml ###################################
# This will let us create Open API 3.0.0 references,
# i.e. $ref: ...
class Ref(tuple):

    def __repr__(self):
        p, d = self
        return f"$ref: '{p}/{d}'"


def ref_presenter(dumper, data):
    # Data should be a Tuple, containing the
    # path of where the component lives and
    # the component name.
    p, d = data
    return dumper.represent_dict(
        {'$ref': f"{p}/{d}"}
    )


def represent_ordereddict(dumper, data):
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)


@contextlib.contextmanager
def make_yaml_accept_references(__yaml):
    __yaml.add_representer(Ref, ref_presenter)
    __yaml.add_representer(OrderedDict, represent_ordereddict)

    try:
        yield __yaml
    finally:
        # Erase any modifications made
        # to the `yaml` singleton.
        importlib.reload(__yaml)
