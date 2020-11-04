from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Optional, List
from ackbas_core.knowledge_graph import RTTypeDefinition, RTMethod, RTGraph, \
    RTEnumValue, RTParamPlaceholder, RTMethodInput
import itertools


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
            if input_obj is not None and input_obj.output_of is not None:
                input_obj.output_of.propagate()

        for option_name, output_option in self.outputs.items():
            for output_name, output_obj in output_option.items():
                if output_obj is None:
                    continue

                output_def = self.method.outputs[option_name][output_name]
                output_obj.type = output_def.type

                # copy parameters from matching input object if it exists
                for input_name, input_obj in self.inputs.items():
                    if input_name == output_name:
                        for param_name, param_val in input_obj.param_values.items():
                            output_obj.param_values[param_name] = param_val
                        break

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


def brute_force_solution(graph: RTGraph, start_objects: Dict[str, RTObjectInstance], end_spec: RTMethodInput):
    # define two lists, "potential connections", "tried connections"
    # fill "potential connections" with every connection that fits and that isn't yet in "tried connections"
    # for every "potential connection" pop it, add it to "tried connections", and if it results in a new object, add it to the graph, exit if new object fits end_spec
    # repeat with new "potential connections", exit if no exist
    potential_connections = []
    tried_connections = []

    object_instances = start_objects.copy()
    method_instances = []

    found_target_obj = False
    exhausted_every_connection = False

    auto_id = 0

    while not found_target_obj and not exhausted_every_connection:
        for method_name, method_def in graph.methods.items():
            dict_of_input_lists = {input_name: [obj_name for obj_name, obj in object_instances.items() if object_matches_input_spec(obj, input_spec)] for input_name, input_spec in method_def.inputs.items()}
            list_of_input_connections = dict_cartesian(dict_of_input_lists)

            for input_connection in list_of_input_connections:
                input_connection_with_method = {
                    'method': method_name,
                    'inputs': input_connection
                }
                if input_connection_with_method not in tried_connections:
                    potential_connections.append(input_connection_with_method)

        if not potential_connections:
            exhausted_every_connection = True

        while potential_connections:
            new_connection = potential_connections.pop()
            tried_connections.append(new_connection)

            method_def = graph.methods[new_connection['method']]
            inputs = {input_name: object_instances[new_connection['inputs'][input_name]] for input_name in method_def.inputs.keys()}
            outputs = {
                option_name: {
                    output_name: RTObjectInstance("o" + str(auto_id := auto_id + 1), output_def.type, {}, None) for output_name, output_def in output_option.items()
                } for option_name, output_option in method_def.outputs.items()
            }
            new_method_instance = RTMethodInstance(method_def, inputs, outputs)
            new_method_instance.propagate()

            method_adds_new_object = False
            for option_name in outputs:
                for output_name in outputs[option_name].keys():
                    output_obj = new_method_instance.outputs[option_name][output_name]
                    output_obj.output_of = new_method_instance

                    for old_obj in object_instances.values():
                        if not new_object_is_redundant(old_obj, output_obj):
                            method_adds_new_object = True

            if method_adds_new_object:
                method_instances.append(new_method_instance)
                for option_name in outputs:
                    for output_name in outputs[option_name].keys():
                        output_obj = new_method_instance.outputs[option_name][output_name]
                        object_instances[output_obj.name] = output_obj

                        if object_matches_input_spec(output_obj, end_spec):
                            found_target_obj = True

    return object_instances, method_instances


def object_matches_input_spec(o: RTObjectInstance, input_spec: RTMethodInput):
    if o.type != input_spec.type:
        return False

    for param_name, constraint in input_spec.param_constraints.items():
        if param_name not in o.param_values:
            return False
        if (isinstance(constraint, int) or isinstance(constraint, RTEnumValue)) and o.param_values[param_name] != constraint:
            return False
    return True


def new_object_is_redundant(old_object: RTObjectInstance, new_object: RTObjectInstance):
    if old_object.type != new_object.type:
        return False
    for param_name, param_val in new_object.param_values.items():
        if param_name not in old_object.param_values or old_object.param_values[param_name] != param_val:
            return False
    return True


def dict_cartesian(dict_of_lists: Dict[str, List]):
    """
    Example: {'a': [1, 2], 'b': [3, 4, 5]} results in
    [{'a': 1, 'b': 3}, {'a': 1, 'b': 4}, ..., {'a': 2, 'b': 5}]
    """
    return [
        {
            key: combination_tuple[i_key]
            for i_key, key in enumerate(dict_of_lists.keys())
        } for combination_tuple in itertools.product(*dict_of_lists.values())
    ]


if __name__ == '__main__':
    graph = RTGraph('../minimal.yml')

    start_ao_spec = {
        'start': {
            'type': 'TypEins',
            'params': {
                'WertEins': 42
            }
        }
    }

    call_spec = [
        {
            'method': 'Konvertiere',
            'inputs': {
                'in': 'start'
            },
            'outputs': {
                'optionEins': {
                    'out': 'konvertiert'
                }
            }
        },
        {
            'method': 'Teste',
            'inputs': {
                'objektZwei': 'konvertiert'
            },
            'outputs': {
                'optionGut': {
                    'objektZwei': 'gut'
                },
                'optionSchlecht': {
                    'objektZwei': 'schlecht'
                }
            }
        },
        {
            'method': 'Kombiniere',
            'inputs': {
                'objektEins': 'start',
                'objektZwei': 'gut'
            },
            'outputs': {
                'optionEins': {
                    'objektDrei': 'loesung1'
                }
            }
        },
        {
            'method': 'Korrigiere',
            'inputs': {
                'objektZwei': 'schlecht'
            },
            'outputs': {
                'optionEins': {
                    'objektZwei': 'korrigiert'
                }
            }
        },
        {
            'method': 'Kombiniere',
            'inputs': {
                'objektEins': 'start',
                'objektZwei': 'korrigiert'
            },
            'outputs': {
                'optionEins': {
                    'objektDrei': 'loesung2'
                }
            }
        }
    ]

    # object_instances, method_instances = build_solution(graph, start_ao_spec, call_spec)
    # object_instances['loesung1'].output_of.propagate()
    # object_instances['loesung2'].output_of.propagate()
    # print(object_instances['loesung1'])

    start_object = RTObjectInstance('start', graph.types['TypEins'], {
        'WertEins': 42
    }, None)

    end_spec = RTMethodInput(graph.types['TypDrei'], {'WertDrei': 42})

    object_instances, method_instances = brute_force_solution(graph, {'start': start_object}, end_spec)
