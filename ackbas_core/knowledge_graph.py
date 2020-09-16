from __future__ import annotations

import yaml
from typing import List, Dict
from dataclasses import dataclass



@dataclass
class RTEnum:
    name: str
    values: List[str]


@dataclass
class RTParamDefinition:
    name: str
    enum: RTEnum


@dataclass
class RTTypeDefinition:
    name: str
    description: str
    params: List[RTParamDefinition]


@dataclass
class RTTypeBinding:
    id: int
    type_def: RTTypeDefinition
    param_values: List[str]

    @property
    def is_concrete(self):
        return all(val[0].isupper() for val in self.param_values)

    def is_subsumed_by(self, other: RTTypeBinding):
        if self.type_def != other.type_def:
            return False

        for my_val, other_val in zip(self.param_values, other.param_values):
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
        with open(yml_path, 'r', encoding='utf8') as f:
            yaml_content = yaml.load(f, Loader=yaml.SafeLoader)

        self.enums: Dict[str, RTEnum] = {}
        for enum_name, enum_items in yaml_content['enums'].items():
            self.enums[enum_name] = RTEnum(enum_name, enum_items)

        self.types: Dict[str, RTTypeDefinition] = {}
        for type_name, type_yaml in yaml_content['types'].items():
            description = type_yaml['description']
            type_params = [RTParamDefinition(param_yaml['name'], self.enums[param_yaml['enum']]) for param_yaml in type_yaml['params']]

            self.types[type_name] = RTTypeDefinition(type_name, description, type_params)

        self.node_id = 1
        concrete_type_bindings: List[RTTypeBinding] = []

        def get_type_binding_instance(type_name: str, param_values: List[str]):
            type_def = self.types[type_name]
            new_binding_instance = RTTypeBinding(self.node_id, type_def, param_values)
            self.node_id += 1

            for binding in concrete_type_bindings:
                if binding.type_def == new_binding_instance.type_def and all(b_val == nb_val for b_val, nb_val in zip(binding.param_values, new_binding_instance.param_values)):
                    self.node_id -= 1  # reset node id to not have gaps
                    return binding
            else:
                concrete_type_bindings.append(new_binding_instance)
                return new_binding_instance

        self.methods: Dict[str, RTMethod] = {}
        for method_name, method_yaml in yaml_content['methods'].items():
            description = method_yaml['description']
            inputs = [get_type_binding_instance(input_type_name, param_values) for input_type_name, param_values in method_yaml['inputs'].items()]
            outputs = [[get_type_binding_instance(output_type_name, param_values) for output_type_name, param_values in
                      output_option_dict.items()] for output_option_dict in method_yaml['outputs']]

            self.methods[method_name] = RTMethod(self.node_id, method_name, description, inputs, outputs)
            self.node_id += 1


if __name__ == '__main__':
    graph = RTGraph('../new_types.yml')
