from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Optional
from ackbas_core.knowledge_graph import RTTypeDefinition, RTMethod, RTGraph, \
    RTEnumValue, RTParamPlaceholder


@dataclass
class RTObjectInstance:
    name: str
    type: RTTypeDefinition
    param_values: Dict[str, Union[int, RTEnumValue]]
    output_of: Optional[RTMethodInstance]


@dataclass
class RTMethodInstance:
    method: RTMethod
    inputs: Dict[str, Optional[RTObjectInstance]]
    outputs: Dict[str, Dict[str, Optional[RTObjectInstance]]]

    def propagate(self):  # bäh
        # propagate parameters to objects connected to inputs
        for input_obj in self.inputs.values():
            if input_obj is not None:
                input_obj.output_of.propagate()

        for option_name, output_option in self.outputs.items():
            for output_name, output_obj in output_option.items():
                if output_obj is None:
                    continue

                output_def = self.method.outputs[option_name][output_name]
                output_obj.type = output_def.type

                for param_name, param_statement in output_def.param_statements.items():
                    if isinstance(param_statement, int) or isinstance(param_statement, RTEnumValue):
                        # output param is literal value, just set it
                        output_obj.param_values[param_name] = param_statement
                    elif isinstance(param_statement, RTParamPlaceholder):
                        # search inputs for matching placeholder
                        for input_name, input_def in self.method.inputs.items():
                            for in_param_name, param_constraint in input_def.param_constraints.items():
                                if isinstance(param_constraint, RTParamPlaceholder) and param_constraint.name == param_statement.name:
                                    # we found the matching placeholder
                                    # now find the input object
                                    input_obj = self.inputs[input_name]
                                    assert input_obj is not None, "Cannot infer parameter " + param_name + " for " + output_obj.name + " because input " + input_name + " is not connected"
                                    output_obj.param_values[param_name] = input_obj.param_values[in_param_name]
                                    # now we need to break out of these loops
                                    break
                            else:
                                continue
                            break


def build_solution(graph, start_ao_spec, call_spec):
    abstract_objects: Dict[str, RTObjectInstance] = {}
    method_calls = []

    def get_ao(name):
        if name not in abstract_objects:
            abstract_objects[name] = RTObjectInstance(name, None, {}, None)

        return abstract_objects[name]

    for ao_name, ao_spec in start_ao_spec.items():
        ao = get_ao(ao_name)
        ao.type = graph.types[ao_spec['type']]

        for param_name, param_val in ao_spec['params'].items():
            ao.param_values[param_name] = graph.instantiate_param(ao.type.params[param_name].type, param_val)

    for method_call_descr in call_spec:
        method_def = graph.methods[method_call_descr['method']]

        inputs = {}
        for port_name, ao_name in method_call_descr['inputs'].items():
            inputs[port_name] = get_ao(ao_name)

        outputs = {}
        for option_name, output_option in method_call_descr['outputs'].items():
            for port_name, ao_name in output_option.items():
                if option_name not in outputs:
                    outputs[option_name] = {}

                output_obj = get_ao(ao_name)
                outputs[option_name][port_name] = output_obj

        method_call = RTMethodInstance(method_def, inputs, outputs)

        for output_option in method_call.outputs.values():
            for output_obj in output_option.values():
                output_obj.output_of = method_call

        method_calls.append(method_call)

    return abstract_objects, method_calls


if __name__ == '__main__':
    graph = RTGraph('../new_types.yml')

    start_ao_spec = {
        'tf': {
            'type': 'ÜTF',
            'params': {
                'Ordnung': 3,
                'Proper': 'Proper'
            }
        }
    }

    call_spec = [
        {
            'method': 'ÜTFzuSS',
            'inputs': {
                'tf': 'tf'
            },
            'outputs': [
                {
                    'ltiss': 'ss'
                }
            ]
        }
    ]

    abstract_objects, method_calls = build_solution(graph, start_ao_spec, call_spec)
    method_calls[0].propagate()
    print(abstract_objects['ss'])
