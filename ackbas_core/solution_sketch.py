from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Optional, List
from ackbas_core.knowledge_graph import RTTypeDefinition, RTMethod, RTGraph, \
    RTEnumValue, RTParamPlaceholder, RTMethodInput, RTParamUnset
import itertools


RTChoiceSpace = Dict[str, str]


class RTSolutionGraph:
    def __init__(self, target_spec: RTMethodInput):
        self.target_spec = target_spec
        self.method_instances: Dict[str, RTMethodInstance] = {}
        self.object_instances: Dict[str, RTObjectInstance] = {}

        self._auto_id = 1

    def get_objects_in_choice_space(self, choice_space: RTChoiceSpace):
        return [o for o in self.object_instances.values() if o.in_choice_space(choice_space)]

    def next_id(self):
        self._auto_id += 1
        return self._auto_id - 1


@dataclass
class RTObjectInstance:
    name: str
    type: RTTypeDefinition
    choice_space: RTChoiceSpace  # method instance name -> output option
    param_values: Dict[str, Union[int, RTEnumValue]]
    output_of: Optional[RTMethodInstance]

    def in_choice_space(self, other_choice_space: RTChoiceSpace):
        for method_name, option in self.choice_space.items():
            if method_name not in other_choice_space or other_choice_space[method_name] != option:
                return False

        return True


@dataclass
class RTMethodInstance:
    method: RTMethod
    name: str
    inputs: Dict[str, Optional[RTObjectInstance]]
    outputs: Dict[str, Dict[str, Optional[RTObjectInstance]]]

    def propagate(self):
        # TODO: maybe this should automatically be done when instantiating the method? or at least automatically create
        # the output objects

        # propagate parameters to objects connected to inputs
        for input_obj in self.inputs.values():
            if input_obj is not None and input_obj.output_of is not None:
                input_obj.output_of.propagate()

        # calculate the common choice space
        # all common keys in the inputs need to match, then just collect all choices over all inputs
        common_choice_space: RTChoiceSpace = {}
        for input_obj in self.inputs.values():
            if input_obj is None:
                continue

            for method_name, option in input_obj.choice_space.items():
                if method_name in common_choice_space:
                    assert common_choice_space[method_name] == option, "Input choice spaces incompatible"
                else:
                    common_choice_space[method_name] = option

        for option_name, output_option in self.outputs.items():
            # the choice space for all output objects on this branch
            new_choice_space = common_choice_space.copy()
            if len(self.outputs) > 1:
                # only narrow choice space if there was actually a choice
                new_choice_space[self.name] = option_name

            for output_name, output_obj in output_option.items():
                if output_obj is None:
                    continue

                output_def = self.method.outputs[option_name][output_name]
                output_obj.type = output_def.type
                output_obj.choice_space = new_choice_space

                # copy parameters from matching input object if it exists
                for input_name, input_obj in self.inputs.items():
                    if input_name == output_name:
                        for param_name, param_val in input_obj.param_values.items():
                            output_obj.param_values[param_name] = param_val
                        break

                # set output object parameters based on literals or input object parameters
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


def flood_fill(solution_graph: RTSolutionGraph, knowledge_graph: RTGraph, choice_space: RTChoiceSpace, start_objects: List[RTObjectInstance]):
    # exhaust every combination while only using objects in the current choice space
    # like this: starting with set of 'fresh' (so far unused) objects, try all possible combinations that use these
    # objects in at least one input
    # when implementing a combination, flag all generated objects as 'fresh'
    # while doing that, remember all newly generated objects with more narrow choice space (future_objects)

    # if any generated object (in current choice space) matches the target spec, return

    # otherwise, at some point all combinations will have been exhausted
    # now it gets somewhat complicated
    # look at all future_objects and extract all methods with choices and the respective possible options
    # then, for each subsequent choice space run flood_fill
    # the 'fresh' objects to start with are all future_objects in the respective choice space
    print(choice_space)
    fresh_objects = start_objects
    new_fresh_objects = []
    future_objects = []

    while fresh_objects:
        for fresh_object in fresh_objects:
            for method_name, method_def in knowledge_graph.methods.items():
                for input_name, input_spec in method_def.inputs.items():
                    if object_matches_input_spec(fresh_object, input_spec):
                        # this input on this method would accept this fresh object
                        # now find all combinations of how the other inputs could be filled
                        dict_of_lists = {input_name: [fresh_object]}
                        for other_input_name, other_input_spec in method_def.inputs.items():
                            if other_input_name == input_name:
                                continue

                            dict_of_lists[other_input_name] = [obj
                                                               for obj
                                                               in solution_graph.get_objects_in_choice_space(choice_space)
                                                               if object_matches_input_spec(obj, other_input_spec)]

                        list_of_dicts = dict_cartesian(dict_of_lists)

                        for inputs in list_of_dicts:
                            # instantiate method and its output objects
                            outputs = {}
                            for option_name, output_option in method_def.outputs.items():
                                outputs[option_name] = {}
                                for output_name, output_def in output_option.items():
                                    outputs[option_name][output_name] = RTObjectInstance("o" + str(solution_graph.next_id()), output_def.type, {}, {}, None)
                            new_method_instance = RTMethodInstance(method_def, "m" + str(solution_graph.next_id()), inputs, outputs)
                            new_method_instance.propagate()

                            # test whether we actually gained anything new from this (and set output_of)
                            method_adds_new_object = False
                            for option_name in outputs:
                                for output_name in outputs[option_name]:
                                    output_obj = new_method_instance.outputs[option_name][output_name]
                                    output_obj.output_of = new_method_instance

                                    for old_obj in solution_graph.get_objects_in_choice_space(choice_space):
                                        if not new_object_is_redundant(old_obj, output_obj):
                                            method_adds_new_object = True

                            if method_adds_new_object:
                                # add new method and objects to graph
                                solution_graph.method_instances[new_method_instance.name] = new_method_instance
                                for option_name in outputs:
                                    for output_name in outputs[option_name].keys():
                                        output_obj = new_method_instance.outputs[option_name][output_name]
                                        solution_graph.object_instances[output_obj.name] = output_obj

                                        if output_obj.in_choice_space(choice_space):
                                            new_fresh_objects.append(output_obj)
                                        else:
                                            if object_matches_input_spec(output_obj, solution_graph.target_spec):
                                                return
                                            future_objects.append(output_obj)

        fresh_objects = new_fresh_objects
        new_fresh_objects = []

    if not future_objects:
        return

    choice_space_of_lists = {}
    for obj in future_objects:
        for method_name, option in obj.choice_space.items():
            if method_name not in choice_space_of_lists:
                choice_space_of_lists[method_name] = []
            choice_space_of_lists[method_name].append(option)

    subsequent_choice_spaces = dict_cartesian(choice_space_of_lists)
    for subsequent_choice_space in subsequent_choice_spaces:
        subsequent_start_objects = [obj for obj in future_objects if obj.in_choice_space(subsequent_choice_space)]
        flood_fill(solution_graph, knowledge_graph, subsequent_choice_space, subsequent_start_objects)


def object_matches_input_spec(o: RTObjectInstance, input_spec: RTMethodInput):
    if o.type != input_spec.type:
        return False

    for param_name, constraint in input_spec.param_constraints.items():
        if isinstance(constraint, RTParamUnset):
            if param_name in o.param_values:
                return False
        else:
            if param_name not in o.param_values:
                return False
            elif (isinstance(constraint, int) or isinstance(constraint, RTEnumValue)) and o.param_values[param_name] != constraint:
                return False
    return True


def new_object_is_redundant(old_object: RTObjectInstance, new_object: RTObjectInstance):
    if old_object.type != new_object.type:
        return False
    if not old_object.in_choice_space(new_object.choice_space):
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


def dict_diff(a, b):
    result = {}
    for key in a:
        if key not in b:
            result[key] = a[key]

    return result


if __name__ == '__main__':
    graph = RTGraph('../minimal.yml')

    start_object = RTObjectInstance('start', graph.types['TypEins'], {}, {
        'WertEins': 42
    }, None)

    end_spec = RTMethodInput(graph.types['TypDrei'], {'WertDrei': 42})

    solution_graph = RTSolutionGraph(end_spec)
    solution_graph.object_instances['start'] = start_object
    flood_fill(solution_graph, graph, {}, [start_object])