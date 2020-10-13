from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from ackbas_core.knowledge_graph import RTTypeDefinition, RTParamDefinition, RTMethod, RTMethodPort, RTGraph


@dataclass
class AbstractObject:
    name: str
    type: RTTypeDefinition
    param_values: Dict[RTParamDefinition, str]
    dependent_methods: List[MethodCall]


@dataclass
class MethodCall:
    method: RTMethod
    inputs: Dict[RTMethodPort, AbstractObject]
    outputs: Dict[RTMethodPort, AbstractObject]

    def propagate(self):
        for output, output_obj in self.outputs.items():
            output_obj.type = output.type

            for input, input_obj in self.inputs.items():
                if input.name == output.name:
                    output_obj.param_values = input_obj.param_values
                    break
            else:
                output_obj.param_values = {}

            for param_def, constraint_val in output.constraints.items():
                if constraint_val[0].isupper():
                    # Specific value, just set it
                    output_obj.param_values[param_def] = constraint_val
                else:
                    # search input ports for a constraint containing this value
                    for input, input_obj in self.inputs.items():
                        for input_param_def, input_constraint_val in input.constraints.items():
                            if input_constraint_val == constraint_val:
                                # then read the input objects parameter and set it for the output object
                                output_obj.param_values[param_def] = input_obj.param_values[input_param_def]

        for output_obj in self.outputs.values():
            for dependent_method in output_obj.dependent_methods:
                dependent_method.propagate()


def build_solution(graph, start_ao_spec, call_spec):
    abstract_objects: Dict[str, AbstractObject] = {}
    method_calls = []

    def get_ao(name):
        if name not in abstract_objects:
            abstract_objects[name] = AbstractObject(name, None, {}, [])

        return abstract_objects[name]

    for ao_name, ao_spec in start_ao_spec.items():
        ao = get_ao(ao_name)
        ao.type = graph.types[ao_spec['type']]

        for param_name, param_val in ao_spec['params'].items():
            ao.param_values[ao.type.params[param_name]] = param_val

        abstract_objects[ao_name] = ao

    for method_call_descr in call_spec:
        method_def = graph.methods[method_call_descr['method']]

        inputs = {}
        for port_name, ao_name in method_call_descr['inputs'].items():
            port_def = method_def.inputs[port_name]
            inputs[port_def] = get_ao(ao_name)

        outputs = {}
        for option_i, output_set in enumerate(method_call_descr['outputs']):
            for port_name, ao_name in output_set.items():
                port_def = method_def.outputs[option_i][port_name]
                outputs[port_def] = get_ao(ao_name)

        method_call = MethodCall(method_def, inputs, outputs)
        for ao in method_call.inputs.values():
            ao.dependent_methods.append(method_call)
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
