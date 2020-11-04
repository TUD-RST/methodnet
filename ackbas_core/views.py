from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse
from django.utils.safestring import SafeString

import ackbas_core.knowledge_graph as kg

import json

from typing import Dict

from ackbas_core.solution_sketch import build_solution, RTObjectInstance


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

        rtgraph = kg.RTGraph('minimal.yml')

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

        object_instances, method_instances = build_solution(rtgraph, start_ao_spec, call_spec)
        object_instances['loesung1'].output_of.propagate()
        object_instances['loesung2'].output_of.propagate()

        id = 1
        ao_name_to_id: Dict[str, int] = {}

        for ao in object_instances.values():
            graph_data['objects'].append({
                "id": id,
                "type": ao.type.name,
                "name": ao.name,
                "params": {
                    param_name: str(param_val) for param_name, param_val in ao.param_values.items()
                }
            })
            ao_name_to_id[ao.name] = id
            id += 1

        for mc in method_instances:
            inputs = []
            for port_name, port in mc.method.inputs.items():
                port_dict = {
                    'id': id,
                    'name': port_name,
                    'constraints': {
                        param_name: str(param_val) for param_name, param_val in port.param_constraints.items()
                    }
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
                'outputs': outputs
            })
            id += 1

        graph_data['nextId'] = id

        graph_data_json = json.dumps(graph_data)

        context = {'graph_data': SafeString(graph_data_json)}

        return TemplateResponse(request, "ackbas_core/graph_editor.html", context)
