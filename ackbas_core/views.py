from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse
from django.utils.safestring import SafeString

import ackbas_core.knowledge_graph as kg

import json

from typing import List


class LandingPageView(View):

    # noinspection PyMethodMayBeStatic
    def get(self, request):

        context = {"title": "Landing Page"}

        return TemplateResponse(request, "ackbas_core/landing.html", context)


class TestGraphView(View):
    def get(self, request):
        graph_data = {
            'methods': [],
            'concreteTypes': [],
            'abstractTypes': [],
            'edges': []
        }

        included_type_bindings: List[kg.RTTypeBinding] = []

        rtgraph = kg.RTGraph('new_types.yml')
        edge_id = 1
        for method in rtgraph.methods.values():
            graph_data['methods'].append({
                'id': method.id,
                'name': method.name,
                'description': method.description
            })

            all_connected_bindings = method.inputs + sum(method.outputs, [])
            for type_binding in all_connected_bindings:
                if type_binding not in included_type_bindings:
                    type_yaml = {
                        'id': type_binding.id,
                        'name': type_binding.type_def.name + ("[" + ", ".join(type_binding.param_values) + "]" if type_binding.param_values else ""),
                        'description': type_binding.type_def.description
                    }
                    included_type_bindings.append(type_binding)
                    if type_binding.is_concrete:
                        graph_data['concreteTypes'].append(type_yaml)
                    else:
                        graph_data['abstractTypes'].append(type_yaml)

            for type_binding in method.inputs:
                graph_data['edges'].append({
                    'id': edge_id,
                    'fromId': type_binding.id,
                    'toId': method.id
                })
                edge_id += 1

            for output_option in method.outputs:
                assert len(output_option) == 1, 'Output options with multiple types not supported yet'
                type_binding = output_option[0]
                graph_data['edges'].append({
                    'id': edge_id,
                    'fromId': method.id,
                    'toId': type_binding.id
                })
                edge_id += 1

        # !!!! this is O(n^2) !!!!
        for type_binding in included_type_bindings:
            for other_type_binding in included_type_bindings:
                if type_binding is other_type_binding:
                    continue

                if type_binding.is_subsumed_by(other_type_binding):
                    graph_data['edges'].append({
                        'id': edge_id,
                        'fromId': type_binding.id,
                        'toId': other_type_binding.id
                    })
                    edge_id += 1

        graph_data_json = json.dumps(graph_data)

        context = {'graph_data': SafeString(graph_data_json)}

        return TemplateResponse(request, "ackbas_core/testgraph.html", context)
