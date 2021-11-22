from __future__ import annotations

import yaml
from typing import List, Dict, Union, Optional, Tuple, cast
import os
from dataclasses import dataclass
import jsonschema
import json


class HashableDict(dict):
    """
    Convenience class that makes it possible to use dicts in hashable dataclasses.
    """
    def __hash__(self):
        return hash(frozenset(self.items()))

    # make dictionary access immutable
    def __setitem__(self, key, value):
        raise TypeError("HashableDict is immutable")


class RTLoadError(Exception):
    pass


@dataclass(eq=True, frozen=True)
class RTParamType:  # e.g. Int, Steuerbarkeit, MatrixRolle
    name: str


@dataclass
class RTParamPlaceholder:
    name: str

    def __repr__(self):
        return "$" + self.name


@dataclass
class RTParamUnset:
    pass


@dataclass(eq=True, frozen=True)
class RTEnumType(RTParamType):
    values: Tuple[str]


@dataclass(eq=True, frozen=True)
class RTEnumValue:
    type: RTEnumType
    val: int

    def __repr__(self):
        return self.type.name + "." + self.type.values[self.val]


@dataclass(eq=True, frozen=True)
class RTParamDefinition:
    name: str
    type: RTParamType


@dataclass(eq=True, frozen=True)
class RTTypeDefinition:
    name: str
    params: HashableDict[str, RTParamDefinition]
    yaml: str


# Values that can be used in method input or output parameter definitions.
# int and RTEnumValues are literals, RTParamPlaceholders are copied from input to output
# and RTParamUnset is used to indicate that the parameter is not set (constraint for input).
RTParamValue = Union[int, RTEnumValue, RTParamPlaceholder, RTParamUnset]


@dataclass(eq=True, frozen=True)
class RTMethodInput:
    """
    A description of a single method input, containing the input type and constraints that must be met.
    """
    type: RTTypeDefinition
    param_constraints: HashableDict[str, RTParamValue]
    tune: bool = False


@dataclass(eq=True, frozen=True)
class RTMethodOutput:
    """
    A description of a single method output, containing the output type and a description of how
    the output type parameter values follow from the input types.
    """
    type: RTTypeDefinition
    param_statements: HashableDict[str, RTParamValue]  # keys are output parameter names


@dataclass(eq=True, frozen=True)
class RTMethod:
    name: str
    inputs: HashableDict[str, RTMethodInput]
    outputs: HashableDict[str, RTMethodOutput]
    yaml: str
    description: Optional[str] = None


class RTGraph:
    """
    Core knowledge graph type
    """
    def __init__(self, yml_path):
        """
        Load knowledge graph from YML file
        """
        self.node_id = 1

        with open(yml_path, 'r', encoding='utf8') as f:
            yaml_content = yaml.load(f, Loader=yaml.SafeLoader)

        schema_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.schema.json')

        with open(schema_path, 'r', encoding='utf8') as f:
            schema = json.load(f)

        # Validate YML based on JSON schema
        jsonschema.validate(yaml_content, schema)

        # Instantiate objects to build graph in memory
        self.param_types: Dict[str, RTParamType] = {
            'Int': RTParamType('Int')
        }
        for enum_name, enum_items in yaml_content['enums'].items():
            self.param_types[enum_name] = RTEnumType(enum_name, tuple(enum_items))

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

            self.types[type_name] = RTTypeDefinition(type_name, HashableDict(type_params), yaml.dump(type_yaml, allow_unicode=True))

        self.methods: Dict[str, RTMethod] = {}
        for method_name, method_yaml in yaml_content['methods'].items():
            inputs: Dict[str, RTMethodInput] = {}
            for input_name, input_yaml in method_yaml['inputs'].items():
                type_def = self.types[input_yaml['type']]
                param_constraints = {}
                if 'params' in input_yaml:
                    for param_name, param_val in input_yaml['params'].items():
                        param_constraints[param_name] = self.instantiate_param(type_def.params[param_name].type, param_val)
                tune = input_yaml.get('tune', False)

                inputs[input_name] = RTMethodInput(type_def, HashableDict(param_constraints), tune=tune)

            outputs: Dict[str, RTMethodOutput] = {}
            for output_name, output_yaml in method_yaml['outputs'].items():
                type_def = self.types[output_yaml['type']]
                param_statements = {}
                if 'params' in output_yaml:
                    for param_name, param_val in output_yaml['params'].items():
                        param_statements[param_name] = self.instantiate_param(type_def.params[param_name].type, param_val)

                outputs[output_name] = RTMethodOutput(type_def, HashableDict(param_statements))

            description = method_yaml.get('description', None)

            self.methods[method_name] = RTMethod(method_name, HashableDict(inputs), HashableDict(outputs), yaml.dump(method_yaml, allow_unicode=True), description=description)

    def next_id(self):
        self.node_id += 1
        return self.node_id - 1

    @staticmethod
    def instantiate_param(param_type: RTParamType, literal_val: Union[int, str]) -> RTParamValue:
        # the following matching should actually be done based on the expected type
        if isinstance(literal_val, int):  # integer constant
            return literal_val
        elif isinstance(literal_val, str):
            if literal_val == 'unset':
                return RTParamUnset()
            elif literal_val[0].isupper():  # Enum literal
                enum_type: RTEnumType = cast(RTEnumType, param_type)
                for i, enum_val in enumerate(enum_type.values):
                    if literal_val == enum_val:
                        return RTEnumValue(enum_type, i)
                else:
                    raise RTLoadError(literal_val + " is not valid for enum " + enum_type.name)
            else:  # placeholder
                return RTParamPlaceholder(literal_val)
        else:
            raise RTLoadError(literal_val + " of type " + type(literal_val) + " is not a valid constraint")


if __name__ == '__main__':
    graph = RTGraph('../new_types.yml')
    print(graph.methods)
