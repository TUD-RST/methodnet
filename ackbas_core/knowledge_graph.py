from __future__ import annotations

import yaml
from typing import List, Dict
import os
from dataclasses import dataclass, field
import jsonschema
import json


class RTLoadError(Exception):
    pass


@dataclass(frozen=True)
class RTParamType:
    name: str


@dataclass(frozen=True)
class RTEnum(RTParamType):
    values: List[str] = field(compare=False)


@dataclass(frozen=True)
class RTParamDefinition:
    name: str
    type: RTParamType


@dataclass(frozen=True)
class RTTypeDefinition:
    name: str
    params: Dict[str, RTParamDefinition] = field(compare=False)


@dataclass(frozen=True)
class RTMethodPort:
    name: str
    type: RTTypeDefinition
    constraints: Dict[RTParamDefinition, str]


@dataclass
class RTMethod:
    name: str
    inputs: Dict[str, RTMethodPort]
    outputs: List[Dict[str, RTMethodPort]]


class RTGraph:
    def __init__(self, yml_path):
        self.node_id = 1

        with open(yml_path, 'r', encoding='utf8') as f:
            yaml_content = yaml.load(f, Loader=yaml.SafeLoader)

        schema_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.schema.json')

        with open(schema_path, 'r', encoding='utf8') as f:
            schema = json.load(f)

        jsonschema.validate(yaml_content, schema)

        self.param_types: Dict[str, RTParamType] = {
            'Int': RTParamType('Int')
        }
        for enum_name, enum_items in yaml_content['enums'].items():
            self.param_types[enum_name] = RTEnum(enum_name, enum_items)

        self.types: Dict[str, RTTypeDefinition] = {}
        for type_name, type_yaml in yaml_content['types'].items():
            type_params = {}

            for param_name, param_yaml in type_yaml['params'].items():
                param_type_name = param_yaml['type']
                if param_type_name not in self.param_types:
                    raise RTLoadError(f"{param_type_name} is not a valid param type")
                param_type = self.param_types[param_type_name]
                type_params[param_name] = RTParamDefinition(param_name, param_type)

            self.types[type_name] = RTTypeDefinition(type_name, type_params)

        self.methods: Dict[str, RTMethod] = {}
        for method_name, method_yaml in yaml_content['methods'].items():
            def make_method_port(port_name, port_yaml):
                type_def = self.types[port_yaml['type']]
                if 'params' in port_yaml:
                    constraints = {
                        type_def.params[param_name]: param_value for param_name, param_value in port_yaml['params'].items()
                    }
                else:
                    constraints = {}
                return RTMethodPort(port_name, type_def, constraints)

            inputs = {port_name: make_method_port(port_name, port_yaml) for port_name, port_yaml in method_yaml['inputs'].items()}
            outputs = [{port_name: make_method_port(port_name, port_yaml) for port_name, port_yaml in output_option_dict.items()} for output_option_dict in method_yaml['outputs']]

            self.methods[method_name] = RTMethod(method_name, inputs, outputs)

    def next_id(self):
        self.node_id += 1
        return self.node_id - 1


if __name__ == '__main__':
    graph = RTGraph('../new_types.yml')
    print(graph)
