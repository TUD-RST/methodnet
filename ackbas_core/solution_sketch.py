from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Union, Optional, List, Tuple
from ackbas_core.knowledge_graph import RTTypeDefinition, RTMethod, RTGraph, \
    RTEnumValue, RTParamPlaceholder, RTMethodInput, RTParamUnset, HashableDict
import itertools

"""
The basis for the path finding algorithm is a so called “candidate graph”.
Nodes in this graph (CandidateNode) correspond to partial solution procedures. Each node
is uniquely identified by the set of available types. Edges in the graph (CandidateEdge)
represent adding a single method call with specific types used as input (RTMethodApplication).
"""


@dataclass(eq=True, frozen=True)
class RTMethodApplication:
    """
    TODO: Docstring
    """
    method: RTMethod
    inputs: HashableDict[str, Optional[RTTypeInstance]]

    def resulting_types(self) -> List[RTTypeInstance]:
        """
        Returns a list of all types that are the result of applying this method with the input types
        as specified in `inputs`.
        """
        output_type_instances = []

        for output_name, output_def in self.method.outputs.items():
            output_def = self.method.outputs[output_name]
            output_type = output_def.type
            output_type_params = {}

            # copy parameters from matching input object if it exists
            for input_name, input_type_instance in self.inputs.items():
                if input_name == output_name:
                    for param_name, param_val in input_type_instance.param_values.items():
                        output_type_params[param_name] = param_val
                    break

            # set output object parameters based on literals or input object parameters
            for param_name, param_statement in output_def.param_statements.items():
                if isinstance(param_statement, int) or isinstance(param_statement, RTEnumValue):
                    # output param is literal value, just set it
                    output_type_params[param_name] = param_statement
                elif isinstance(param_statement, RTParamPlaceholder):
                    # search inputs for matching placeholder
                    for input_name, input_def in self.method.inputs.items():
                        for in_param_name, param_constraint in input_def.param_constraints.items():
                            if isinstance(param_constraint,
                                          RTParamPlaceholder) and param_constraint.name == param_statement.name:
                                # we found the matching placeholder
                                # now find the input object
                                if input_name not in self.inputs:
                                    continue
                                input_obj = self.inputs[input_name]
                                assert input_obj is not None, "Cannot infer parameter " + param_name + " for " + output_name + " because input " + input_name + " is not connected"
                                # copy value from input object if param is set there
                                if in_param_name in input_obj.param_values:
                                    output_type_params[param_name] = input_obj.param_values[in_param_name]
                                    # now we need to break out of these loops
                                    break
                        else:
                            continue
                        break

            output_type_instances.append(RTTypeInstance(output_type, HashableDict(output_type_params)))

        return output_type_instances


@dataclass(eq=True, frozen=True)
class RTTypeInstance:
    """
    A type *definition* looks like
    TypeOne:
        params:
          ValueOne:
            type: Int
    The type instance then fills some or all of these parameters with values. In this case:
    TypeOne:
        params:
          ValueOne: 3
    """
    type_def: RTTypeDefinition
    param_values: HashableDict[str, Union[int, RTEnumValue]]

    def fits_input_description(self, input_description: RTMethodInput):
        """
        Returns true if this type instance fits the input description of a method.
        """
        if input_description.type != self.type_def:
            return False

        for param_name, constraint in input_description.param_constraints.items():
            if isinstance(constraint, RTParamPlaceholder):
                continue
            elif isinstance(constraint, RTParamUnset):
                if param_name in self.param_values:
                    return False
            else:
                if param_name not in self.param_values:
                    return False
                elif self.param_values[param_name] != constraint:
                    return False

        return True


@dataclass
class CandidateEdge:
    """
    Edge in the candidate graph. Corresponds to the application of a method to a set of input types.
    """
    from_node: CandidateNode
    via_method: RTMethodApplication


class CandidateNode:
    """
    Node in the candidate graph. Uniquely identified by the set of available input types.
    """
    def __init__(self):
        self.resulting_from: Optional[CandidateEdge] = None  # updated in relax step of Dijkstra's algorithm
        self.available_types: Tuple[RTTypeInstance] = ()  # is set after initialization

    def cum_dist(self) -> int:
        if self.resulting_from:
            # Return distance from start node. Each edge adds a distance corresponding to the number of method outputs + 1.
            return self.resulting_from.from_node.cum_dist() + len(self.resulting_from.via_method.method.outputs) + 1
        else:
            return 0

    def __eq__(self, other):
        # Two nodes are equal if their available types contain the same elements
        if not isinstance(other, CandidateNode):
            return False
        return set(self.available_types) == set(other.available_types)


def dijkstra(knowledge_graph: RTGraph, start_types: Tuple[RTTypeInstance], target_definition: RTMethodInput):
    start_node = CandidateNode()
    start_node.available_types = start_types

    # Wikipedia entry for Dijkstra's algorithm:
    # https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

    visited_candidates = []
    unvisited_candidates = []

    current_node = start_node

    while True:
        visited_candidates.append(current_node)

        feasible_edges = get_feasible_edges(knowledge_graph, current_node)

        for edge in feasible_edges:
            new_node = CandidateNode()
            resulting_types = edge.via_method.resulting_types()
            new_available_types = list(current_node.available_types)

            # check that we get at least one new type from this method application
            # also remove redundant types from new_available_types
            atleast_one_new_type = False
            for ti in resulting_types:
                for old_ti in new_available_types:
                    if does_type_a_make_type_b_redundant(old_ti, ti):
                        # This new type is redundant
                        break
                    elif does_type_a_make_type_b_redundant(ti, old_ti):
                        # This old type is redundant and should be replaced by the new type
                        new_available_types.remove(old_ti)
                        new_available_types.append(ti)
                        atleast_one_new_type = True
                        break
                else:
                    # This new type is not redundant
                    new_available_types.append(ti)
                    atleast_one_new_type = True

            if not atleast_one_new_type:
                continue

            new_node.available_types = tuple(new_available_types)
            new_node.resulting_from = edge

            # find if there already exists a node with the same available types
            existing_node = None
            for visited_node in visited_candidates:
                if visited_node == new_node:
                    existing_node = visited_node
                    break
            for unvisited_node in unvisited_candidates:
                if unvisited_node == new_node:
                    existing_node = unvisited_node
                    break

            if existing_node:
                # Relax the edge if the new cum_dist is shorter
                if new_node.cum_dist() < existing_node.cum_dist():
                    existing_node.resulting_from = edge
            else:
                unvisited_candidates.append(new_node)

        if any(ti.fits_input_description(target_definition) for ti in current_node.available_types) or not unvisited_candidates:
            break

        # Pop the next unvisited node with the smallest cum_dist
        unvisited_candidates.sort(key=lambda x: x.cum_dist())
        current_node = unvisited_candidates.pop(0)

    if any(ti.fits_input_description(target_definition) for ti in current_node.available_types):
        return current_node
    else:
        return None


def get_feasible_edges(knowledge_graph: RTGraph, from_node: CandidateNode) -> List[CandidateEdge]:
    candidate_edges = []

    for method_name, method in knowledge_graph.methods.items():
        input_possibilies = {}
        for input_name, input_type in method.inputs.items():
            if not input_type.tune:
                input_possibilies[input_name] = [ti for ti in from_node.available_types if ti.fits_input_description(input_type)]

        list_of_dicts = dict_cartesian(input_possibilies)
        for input_combination in list_of_dicts:
            candidate_edge = CandidateEdge(from_node, RTMethodApplication(method, HashableDict(input_combination)))
            candidate_edges.append(candidate_edge)

    return candidate_edges


def does_type_a_make_type_b_redundant(type_a: RTTypeInstance, type_b: RTTypeInstance):
    if type_a.type_def != type_b.type_def:
        return False
    for param_name, param_val in type_b.param_values.items():
        if param_name not in type_a.param_values or type_a.param_values[param_name] != param_val:
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

    # instantiate a type TypeOne with ValueOne set to 3
    type_one = RTTypeInstance(graph.types['TypeOne'], HashableDict({'ValueOne': 3}))

    start_types = (type_one,)

    # Target spec is a TypeThree instance
    target_spec = RTMethodInput(graph.types['TypeThree'], HashableDict({}))

    # Find a path from start types to target_spec
    end_node = dijkstra(graph, start_types, target_spec)

    print(end_node)
