from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse
from django.utils.safestring import SafeString

import ackbas_core.knowledge_graph as kg

import json

from typing import List, Literal, Union


class LandingPageView(View):

    # noinspection PyMethodMayBeStatic
    def get(self, request):

        context = {"title": "Landing Page"}

        return TemplateResponse(request, "ackbas_core/landing.html", context)


class TestGraphView(View):
    @staticmethod
    def edge_dict(method: kg.RTMethod, type_binding: kg.RTTypeBinding, direction: Literal['input', 'output']):
        if direction == 'input':
            from_id = type_binding.type_def.id
            to_id = method.id
        else:
            from_id = method.id
            to_id = type_binding.type_def.id

        concrete_param_value_string = ", ".join(f"{param_name}={param_value}" for param_name, param_value in type_binding.param_values.items() if param_value[0].isupper())

        return {
            'fromId': from_id,
            'toId': to_id,
            'label': concrete_param_value_string,
            'tooltip': ''
        }

    def get(self, request):
        graph_data = {
            'methods': [],
            'types': [],
            'demuxes': [],
            'edges': []
        }

        rtgraph = kg.RTGraph('new_types.yml')

        for type in rtgraph.types.values():
            graph_data['types'].append({
                'id': type.id,
                'name': type.name,
                'description': type.description
            })

        for method in rtgraph.methods.values():
            graph_data['methods'].append({
                'id': method.id,
                'name': method.name,
                'description': method.description
            })

            for type_binding in method.inputs:
                graph_data['edges'].append(self.edge_dict(method, type_binding, 'input'))

            for output_option in method.outputs:
                if len(output_option) > 1:
                    # we need a demux
                    demux_id = rtgraph.next_id()
                    graph_data['demuxes'].append({
                        'id': demux_id
                    })

                    graph_data['edges'].append({
                        'fromId': method.id,
                        'toId': demux_id,
                        'label': '',
                        'tooltip': ''
                    })

                    for type_binding in output_option:
                        graph_data['edges'].append({
                            'fromId': demux_id,
                            'toId': type_binding.type_def.id,
                            'label': '',
                            'tooltip': ''
                        })
                else:
                    type_binding = output_option[0]
                    graph_data['edges'].append(self.edge_dict(method, type_binding, 'output'))

        graph_data_json = json.dumps(graph_data)

        context = {'graph_data': SafeString(graph_data_json)}

        return TemplateResponse(request, "ackbas_core/testgraph.html", context)
