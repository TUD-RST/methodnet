from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse
from django.utils.safestring import SafeString

import ackbas_core.knowledge_graph as kg

import json

from typing import List, Literal, Union, Dict

from ackbas_core.solution_sketch import build_solution, AbstractObject


class LandingPageView(View):

    # noinspection PyMethodMayBeStatic
    def get(self, request):

        context = {"title": "Landing Page"}

        return TemplateResponse(request, "ackbas_core/landing.html", context)


class GraphEditorView(View):
    def get(self, request, graph):
        graph_data = {
            'methods': [],
            'objects': [],
            'connections': [],
            'nextId': 0
        }

        rtgraph = kg.RTGraph('new_types.yml')

        start_ao_spec = {
            'dgl': {
                'type': 'DGL',
                'params': {
                    'Linear': 'NichtLinear'
                }
            }
        }

        call_spec = [
            {
                'method': 'DGLzuSS',
                'inputs': {
                    'dgl': 'dgl'
                },
                'outputs': [
                    {
                        'ss': 'ssnonlin'
                    }
                ]
            },
            {
                'method': 'TesteSteuerbarkeitNichtlinear',
                'inputs': {
                    'ss': 'ssnonlin'
                },
                'outputs': [
                    {
                        'ss': 'ssnonlincontr'
                    },
                    {
                        'ss': 'ssnonlinnotcontr'
                    },
                    {
                        #'ss': 'ssnonlinunknowncontr'
                    },
                ]
            },
            {
                'method': 'Trajektorienplanung',
                'inputs': {
                    'ss': 'ssnonlincontr'
                },
                'outputs': [
                    {
                        'xtraj': 'xtraj',
                        'utraj': 'utraj'
                    }
                ]
            },
            {
                'method': 'LinearisierungAnTrajektorie',
                'inputs': {
                    'ss': 'ssnonlin',
                    'xtraj': 'xtraj',
                    'utraj': 'utraj'
                },
                'outputs': [
                    {
                        'ssltv': 'ssltv'
                    }
                ]
            },
            {
                'method': 'LTVLQREntwurf',
                'inputs': {
                    'ssltv': 'ssltv'
                },
                'outputs': [
                    {
                        'k': 'k'
                    }
                ]
            },
            {
                'method': 'BaueTrajektorienfolgeregler',
                'inputs': {
                    'xtraj': 'xtraj',
                    'utraj': 'utraj',
                    'k': 'k',
                    'obs': 'obs'
                },
                'outputs': [
                    {
                        'controller': 'controller'
                    }
                ]
            },
            {
                'method': 'TesteBeobachtbarkeitNichtlinear',
                'inputs': {
                    'ss': 'ssnonlin'
                },
                'outputs': [
                    {
                        'ss': 'ssnonlinobs'
                    },
                    {},
                    {}
                ]
            },
            {
                'method': 'ZeitdiskreterEKFEntwurf',
                'inputs': {
                    'ss': 'ssnonlinobs'
                },
                'outputs': [
                    {
                        'obs': 'obs'
                    }
                ]
            }
        ]

        abstract_objects, method_calls = build_solution(rtgraph, start_ao_spec, call_spec)
        method_calls[0].propagate()

        id = 1
        ao_name_to_id: Dict[str, int] = {}

        for ao in abstract_objects.values():
            graph_data['objects'].append({
                "id": id,
                "type": ao.type.name,
                "name": ao.name,
                "params": {
                    param_def.name: param_val for param_def, param_val in ao.param_values.items()
                }
            })
            ao_name_to_id[ao.name] = id
            id += 1

        for mc in method_calls:
            inputs = []
            for port in mc.method.inputs.values():
                port_dict = {
                    'id': id,
                    'name': port.name,
                    'constraints': {
                        param_def.name: param_val for param_def, param_val in port.constraints.items()
                    }
                }
                if port in mc.inputs:
                    ao = mc.inputs[port]
                    graph_data['connections'].append({
                        'fromId': ao_name_to_id[ao.name],
                        'toId': id
                    })

                id += 1
                inputs.append(port_dict)

            outputs = []
            for out_option in mc.method.outputs:
                out_option_ports = []
                for port in out_option.values():
                    port_dict = {
                        'id': id,
                        'name': port.name,
                        'constraints': {
                            param_def.name: param_val for param_def, param_val in port.constraints.items()
                        }
                    }
                    if port in mc.outputs:
                        ao = mc.outputs[port]

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
                'outputs': outputs
            })
            id += 1

        graph_data['nextId'] = id

        graph_data_json = json.dumps(graph_data)

        context = {'graph_data': SafeString(graph_data_json)}

        return TemplateResponse(request, "ackbas_core/graph_editor.html", context)
