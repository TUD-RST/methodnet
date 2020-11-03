from __future__ import annotations

import yaml
from typing import List, Dict, Union
import os
from dataclasses import dataclass, field
import jsonschema
import json


class RTLoadError(Exception):
    pass


@dataclass
class RTParamType:  # e.g. Int, Steuerbarkeit, MatrixRolle
    name: str


@dataclass
class RTParamPlaceholder:
    name: str


@dataclass
class RTEnumType(RTParamType):
    values: List[str]


@dataclass
class RTEnumValue:
    type: RTEnumType
    val: int


@dataclass
class RTParamDefinition:
    name: str
    type: RTParamType


@dataclass
class RTTypeDefinition:
    name: str
    params: Dict[str, RTParamDefinition]


@dataclass
class RTMethodInput:
    type: RTTypeDefinition
    param_constraints: Dict[str, Union[int, RTEnumValue, RTParamPlaceholder]]


@dataclass
class RTMethodOutput:
    type: RTTypeDefinition
    param_statements: Dict[str, Union[int, RTEnumValue, RTParamPlaceholder]]  # does not support integer expressions


@dataclass
class RTMethod:
    name: str
    inputs: Dict[str, RTMethodInput]
    outputs: Dict[str, Dict[str, RTMethodOutput]]


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
            self.param_types[enum_name] = RTEnumType(enum_name, enum_items)

        self.types: Dict[str, RTTypeDefinition] = {}
        for type_name, type_yaml in yaml_content['types'].items():
            type_params = {}

            if 'params' in type_yaml:
                for param_name, param_yaml in type_yaml['params'].items():
                    param_type_name = param_yaml['type']
                    if param_type_name not in self.param_types:
                        raise RTLoadError(f"{param_type_name} is not a valid param type")
                    param_type = self.param_types[param_type_name]
                    type_params[param_name] = RTParamDefinition(param_name, param_type)

            self.types[type_name] = RTTypeDefinition(type_name, type_params)

        self.methods: Dict[str, RTMethod] = {}
        for method_name, method_yaml in yaml_content['methods'].items():
            inputs: Dict[str, RTMethodInput] = {}
            for input_name, input_yaml in method_yaml['inputs'].items():
                type_def = self.types[input_yaml['type']]
                param_constraints = {}
                if 'params' in input_yaml:
                    for param_name, param_val in input_yaml['params'].items():
                        # the following matching should actually be done based on the expected type
                        if isinstance(param_val, int):  # integer constant
                            param_constraints[param_name] = param_val
                        elif isinstance(param_val, str):
                            if param_val[0].isupper():  # Enum literal
                                enum_type: RTEnumType = type_def.params[param_name].type
                                for i, enum_val in enumerate(enum_type.values):
                                    if param_val == enum_val:
                                        param_constraints[param_name] = RTEnumValue(enum_type, i)
                                        break
                                else:
                                    raise RTLoadError(param_val + " is not valid for enum " + enum_type.name)
                            else:  # placeholder
                                param_constraints[param_name] = RTParamPlaceholder(param_val)
                        else:
                            raise RTLoadError(param_val + " of type " + type(param_val) + " is not a valid constraint")

                inputs[input_name] = RTMethodInput(type_def, param_constraints)

            outputs: Dict[str, Dict[str, RTMethodOutput]] = {}
            for output_option, option_yaml in method_yaml['outputs'].items():
                option_dict = {}
                for output_name, output_yaml in option_yaml.items():
                    type_def = self.types[output_yaml['type']]
                    param_statements = {}
                    if 'params' in output_yaml:
                        for param_name, param_val in output_yaml['params'].items():
                            # the following matching should actually be done based on the expected type
                            if isinstance(param_val, int):  # integer constant
                                param_statements[param_name] = param_val
                            elif isinstance(param_val, str):
                                if param_val[0].isupper():  # Enum literal
                                    enum_type: RTEnumType = type_def.params[param_name].type
                                    for i, enum_val in enumerate(enum_type.values):
                                        if param_val == enum_val:
                                            param_statements[param_name] = RTEnumValue(enum_type, i)
                                            break
                                    else:
                                        raise RTLoadError(param_val + " is not valid for enum " + enum_type.name)
                                else:  # placeholder
                                    param_statements[param_name] = RTParamPlaceholder(param_val)
                            else:
                                raise RTLoadError(param_val + " of type " + type(param_val) + " is not a valid constraint")

                    option_dict[output_name] = RTMethodOutput(type_def, param_statements)
                outputs[output_option] = option_dict

            self.methods[method_name] = RTMethod(method_name, inputs, outputs)

    def next_id(self):
        self.node_id += 1
        return self.node_id - 1


if __name__ == '__main__':
    graph = RTGraph('../minimal.yml')
    print(graph.methods)
