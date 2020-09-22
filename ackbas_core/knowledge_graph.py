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
class RTEnum:
    name: str
    values: List[str] = field(compare=False)


@dataclass(frozen=True)
class RTParamDefinition:
    name: str
    longname: str
    enum: RTEnum


@dataclass(frozen=True)
class RTTypeDefinition:
    id: int
    name: str
    description: str
    params: Dict[str, RTParamDefinition] = field(compare=False)


@dataclass(frozen=True)
class RTTypeBinding:
    id: int
    type_def: RTTypeDefinition
    param_values: Dict[RTParamDefinition, str]

    @property
    def is_concrete(self):
        return all(val[0].isupper() for val in self.param_values.values())

    def is_subsumed_by(self, other: RTTypeBinding):
        if self.type_def != other.type_def:
            return False

        for param_name in self.param_values.keys():
            my_val = self.param_values[param_name]
            other_val = other.param_values[param_name]

            if other_val[0].isupper() and my_val != other_val:
                return False

        return True


@dataclass
class RTMethod:
    id: int
    name: str
    description: str
    inputs: List[RTTypeBinding]
    outputs: List[List[RTTypeBinding]]


class RTGraph:
    def __init__(self, yml_path):
        self.node_id = 1

        with open(yml_path, 'r', encoding='utf8') as f:
            yaml_content = yaml.load(f, Loader=yaml.SafeLoader)

        schema_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.schema.json')

        with open(schema_path, 'r', encoding='utf8') as f:
            schema = json.load(f)

        jsonschema.validate(yaml_content, schema)

        self.enums: Dict[str, RTEnum] = {}
        for enum_name, enum_items in yaml_content['enums'].items():
            self.enums[enum_name] = RTEnum(enum_name, enum_items)

        self.types: Dict[str, RTTypeDefinition] = {}
        for type_name, type_yaml in yaml_content['types'].items():
            description = type_yaml['description']
            type_params = {}

            for param_name, param_yaml in type_yaml['params'].items():
                enum_name = param_yaml['enum']
                if enum_name not in self.enums:
                    raise RTLoadError(f"{enum_name} is not a valid enum")
                param_enum = self.enums[enum_name]
                type_params[param_name] = RTParamDefinition(param_name, param_yaml['longname'], param_enum)

            self.types[type_name] = RTTypeDefinition(self.next_id(), type_name, description, type_params)

        def get_type_binding_instance(type_name: str, param_yaml: Dict[str, str]):
            if type_name not in self.types:
                raise RTLoadError(f"{type_name} is not a valid type")

            type_def = self.types[type_name]
            param_values = {}
            for param_name, param_value in param_yaml.items():
                if param_name not in type_def.params:
                    raise RTLoadError(f"{type_name} has no parameter {param_name}")
                param_def = type_def.params[param_name]

                if param_value[0].isupper() and param_value not in param_def.enum.values:
                    raise RTLoadError(f"{param_value} is not a valid value for parameter {param_name} of type {type_name}")

                param_values[param_def] = param_value

            missing_params = [param_def for param_def in type_def.params.values() if param_def not in param_values]
            if missing_params:
                missing_params_str = ", ".join(param_def.name for param_def in missing_params)
                raise RTLoadError(f"Missing parameters {missing_params_str} for type {type_name} in method {method_name}")

            binding = RTTypeBinding(self.next_id(), type_def, param_values)
            return binding

        self.methods: Dict[str, RTMethod] = {}
        for method_name, method_yaml in yaml_content['methods'].items():
            description = method_yaml['description']
            inputs = [get_type_binding_instance(input_type_name, param_values) for input_type_name, param_values in method_yaml['inputs'].items()]
            outputs = [[get_type_binding_instance(output_type_name, param_values) for output_type_name, param_values in
                      output_option_dict.items()] for output_option_dict in method_yaml['outputs']]

            self.methods[method_name] = RTMethod(self.next_id(), method_name, description, inputs, outputs)

    def next_id(self):
        self.node_id += 1
        return self.node_id - 1


if __name__ == '__main__':
    graph = RTGraph('../new_types.yml')
