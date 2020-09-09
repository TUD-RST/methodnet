from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse
from django.utils.safestring import SafeString

from ackbas_core.fancy_format import parse_file, write_as_yaml
from ackbas_core.knowledge_graph import load_yaml

import json


class LandingPageView(View):

    # noinspection PyMethodMayBeStatic
    def get(self, request):

        context = {"title": "Landing Page"}

        return TemplateResponse(request, "ackbas_core/landing.html", context)


class TestGraphView(View):
    def get(self, request):
        ff_types, ff_methods = parse_file('content.rh')
        write_as_yaml('content.yml', ff_types, ff_methods)
        methods, types = load_yaml('content.yml')

        graph_data = {}
        graph_data['types'] = list(types.keys())
        graph_data['methods'] = list(methods.keys())

        flow_edges = []
        for method_name, method in methods.items():
            for port in method.input_ports:
                flow_edges.append((port.type.name, method_name))
            for port in method.output_ports:
                flow_edges.append((method_name, port.type.name))
        graph_data['flowEdges'] = flow_edges

        derive_edges = []
        for type_name, type in types.items():
            for super_type in type.supertypes:
                derive_edges.append((type_name, super_type.name))
        graph_data['deriveEdges'] = derive_edges

        graph_data_json = json.dumps(graph_data)

        context = {'graph_data': SafeString(graph_data_json)}

        return TemplateResponse(request, "ackbas_core/testgraph.html", context)
