import json
from typing import Dict

import yaml
from django.http import JsonResponse, HttpResponseServerError
from django.template.response import TemplateResponse
from django.views import View

import ackbas_core.knowledge_graph as kg
from ackbas_core.solution_sketch import RTObjectInstance, RTSolutionGraph, flood_fill


class LandingPageView(View):
    @staticmethod
    def get(request):
        context = {"title": "Landing Page"}

        return TemplateResponse(request, "ackbas_core/landing.html", context)


class GraphEditorView(View):
    @staticmethod
    def get(request, graph):
        context = {}

        return TemplateResponse(request, "ackbas_core/graph_editor.html", context)


class GetSolutionGraphView(View):
    @staticmethod
    def post(request):
        """
        Return solution graph for knowledge graph and query specified in json
        """
        try:
            request_json = json.loads(request.body)
            graph_name = request_json['graph_name']
            start_dict = yaml.safe_load(request_json['start'])
            target_dict = yaml.safe_load(request_json['target'])

            response_dict = GetSolutionGraphView.get_solution(graph_name, start_dict, target_dict)

            return JsonResponse(response_dict)
        except Exception as e:
            return HttpResponseServerError(str(e))

    @staticmethod
    def get_solution(graph_name: str, start_dict: Dict, target_dict: Dict) -> Dict:

        graph_data = {
            'methods': [],
            'objects': [],
            'connections': [],
            'nextId': 0
        }

        rtgraph = kg.RTGraph(graph_name + '.yml')  # load knowledge graph from disk

        # instantiate and validate start objects from yaml
        start_objects = []
        for obj_name, obj_dict in start_dict.items():
            assert 'type' in obj_dict, "Start object spec must contain 'type'"
            obj_type = rtgraph.types[obj_dict['type']]
            obj_params = {}
            for param_name, param_val in obj_dict.get('params', {}).items():
                assert param_name in obj_type.params, f"{obj_type.name} has no param {param_name}"
                param_type = obj_type.params[param_name].type
                param_instance = rtgraph.instantiate_param(param_type, param_val)
                obj_params[param_name] = param_instance

            obj = RTObjectInstance(obj_name, obj_type, {}, obj_params, None)
            start_objects.append(obj)

        # instantiate and validate target objects
        assert "target" in target_dict, "Target spec must contain 'target'"
        target_dict = target_dict['target']
        assert "type" in target_dict, "Target spec must contain 'type'"
        assert target_dict['type'] in rtgraph.types, f"Type {target_dict['type']} does not exist"
        target_type = rtgraph.types[target_dict['type']]
        target_params = {}
        for param_name, param_val in target_dict.get('params', {}).items():
            assert param_name in target_type.params, f"{target_type.name} has no param {param_name}"
            param_type = target_type.params[param_name].type
            param_instance = rtgraph.instantiate_param(param_type, param_val)
            target_params[param_name] = param_instance

        end_spec = kg.RTMethodInput(target_type, target_params)

        # instantiate solution graph
        solution_graph = RTSolutionGraph(start_objects, end_spec)
        # run search to find target object
        flood_fill(solution_graph, rtgraph, {}, start_objects)
        # prune all incomplete paths
        solution_graph.prune()

        # --- generate data structures for frontend ---
        object_instances = solution_graph.object_instances
        method_instances = solution_graph.method_instances

        id = 1  # running counter for next unique id
        ao_name_to_id: Dict[str, int] = {}  # map object names to unique id's

        for ao in object_instances.values():  # build object instances
            graph_data['objects'].append({
                "id": id,
                "type": ao.type.name,
                "name": ao.name,
                "is_start": ao.is_start,
                "is_end": ao.is_end,
                "distance_to_start": ao.distance_to_start,
                "on_solution_path": ao.on_solution_path,
                "params": {
                    param_name: str(param_val) for param_name, param_val in ao.param_values.items()
                }
            })
            ao_name_to_id[ao.name] = id
            id += 1

        for mc in method_instances.values():  # build method instances
            inputs = []
            for port_name, port in mc.method.inputs.items():
                port_dict = {
                    'id': id,
                    'name': port_name,
                    'constraints': {
                        param_name: str(param_val) for param_name, param_val in port.param_constraints.items()
                    },
                    'tune': port.tune
                }
                if port_name in mc.inputs:
                    ao = mc.inputs[port_name]
                    if ao is not None:
                        graph_data['connections'].append({
                            'fromId': ao_name_to_id[ao.name],
                            'toId': id
                        })

                id += 1
                inputs.append(port_dict)

            outputs = []
            for option_name, out_option in mc.method.outputs.items():
                out_option_ports = []
                for port_name, port in out_option.items():
                    port_dict = {
                        'id': id,
                        'name': port_name,
                        'constraints': {
                            param_name: str(param_val) for param_name, param_val in port.param_statements.items()
                        }
                    }
                    if port_name in mc.outputs[option_name]:
                        ao = mc.outputs[option_name][port_name]

                        if ao is not None:
                            graph_data['connections'].append({
                                'fromId': id,
                                'toId': ao_name_to_id[ao.name]
                            })

                    id += 1
                    out_option_ports.append(port_dict)
                outputs.append(out_option_ports)

            graph_data['methods'].append({
                'id': id,
                'name': mc.method.name,
                'inputs': inputs,
                'outputs': outputs,
                'description': mc.method.description
            })
            id += 1

        graph_data['nextId'] = id

        return graph_data


class GetKnowledgeGraphView(View):
    @staticmethod
    def get(request, graph_name):
        """
        Return knowledge graph data for specified file name
        """
        rtgraph = kg.RTGraph(graph_name + '.yml')

        # build type instances
        types = [{
            'name': type_def.name,
            'yaml': type_def.yaml
        } for type_def in rtgraph.types.values()]

        # build method instances
        methods = [{
            'name': method_def.name,
            'description': method_def.description,
            'yaml': method_def.yaml
        } for method_def in rtgraph.methods.values()]

        # create connections between methods and types that use eachother
        connections = []
        for type_name, type_def in rtgraph.types.items():
            for method_name, method_def in rtgraph.methods.items():
                # check connections type -> method
                for input_def in method_def.inputs.values():
                    if input_def.type == type_def:
                        connections.append((type_name, method_name))
                        break

                # check connections method -> type
                for outputs in method_def.outputs.values():
                    for output_def in outputs.values():
                        if output_def.type == type_def:
                            connections.append((method_name, type_name))
                            break
                    else:
                        continue
                    break

        return JsonResponse({
            'types': types,
            'methods': methods,
            'connections': connections
        })