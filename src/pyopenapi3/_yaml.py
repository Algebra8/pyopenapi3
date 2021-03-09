import contextlib
import importlib
from collections import OrderedDict

import yaml


def represent_ordereddict(dumper, data):
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)


@contextlib.contextmanager
def make_yaml_accept_references(__yaml):
    __yaml.add_representer(OrderedDict, represent_ordereddict)

    try:
        yield __yaml
    finally:
        # Erase any modifications made
        # to the `yaml` singleton.
        importlib.reload(__yaml)
