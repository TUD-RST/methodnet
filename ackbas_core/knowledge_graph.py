import yaml
from typing import List


class RTType:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.supertypes: List[RTType] = []

    def isa(self, other_type):
        if self.name == other_type.name:
            return True
        elif not self.supertypes:
            return False
        else:
            return any(my_super.isa(other_type) for my_super in self.supertypes)


class RTMethod:
    def __init__(self, name, inputs, outputs, nr, description=""):
        self.name: str = name
        self.description = description
        self.input_ports = [RTPort(self, input, i) for i, input in enumerate(inputs)]
        self.output_ports = [RTPort(self, output, i) for i, output in enumerate(outputs)]
        self.nr: int = nr
        self.search_relevant = False
        self.is_origin = False
        self.is_target = False


class RTPort:
    def __init__(self, method, type, nr):
        self.method: RTMethod = method
        self.type: RTType = type
        self.nr: int = nr
        self.connections: List[RTConnection] = []


class RTConnection:
    def __init__(self, output_port, input_port):
        self.output_port: RTPort = output_port
        self.input_port: RTPort = input_port
        self.search_relevant = False


def load_yaml(yml_path):
    methods = {}
    types = {}

    with open(yml_path, 'r', encoding='utf8') as f:
        yaml_content = yaml.load(f, Loader=yaml.BaseLoader)

    # --- Load types ---
    for type_name, type_yaml in yaml_content['types'].items():
        types[type_name] = RTType(type_name, description=type_yaml['description'])

    for type_name, type_instance in types.items():
        for super_type_name in yaml_content['types'][type_name]['super']:
            type_instance.supertypes.append(types[super_type_name])

    # --- Load methods ---
    for method_name in yaml_content['methods'].keys():
        method_yaml = yaml_content['methods'][method_name]
        input_types = [types[input_name] for input_name in method_yaml['inputs']]
        output_types = [types[output_name] for output_name in method_yaml['outputs']]
        new_method = RTMethod(method_name, input_types, output_types, len(methods), description=method_yaml['description'])
        methods[method_name] = new_method

    # --- Connect methods ---
    for _, m1 in methods.items():
        for output in m1.output_ports:
            for _, m2 in methods.items():
                for input in m2.input_ports:
                    if output.type.isa(input.type):
                        con = RTConnection(output, input)
                        output.connections.append(con)
                        input.connections.append(con)

    return methods, types


def color_graph(methods, types, origin_type_name, target_type_name):
    uncolor_graph(methods)

    # --- Search ---
    origin_type = types[origin_type_name]
    target_type = types[target_type_name]

    to_be_visited = []
    visited_and_judged = []
    visited_and_not_judged = []

    for _, m in methods.items():
        if any(origin_type.isa(input.type) for input in m.input_ports):
            m.is_origin = True
            to_be_visited.append(m)

        if any(output.type.isa(target_type) for output in m.output_ports):
            m.is_target = True

    some_movement = True
    while some_movement:
        some_movement = False

        while to_be_visited:
            n = to_be_visited.pop()

            next_methods = []
            for out in n.output_ports:
                for con in out.connections:
                    m = con.input_port.method
                    if m not in next_methods:
                        next_methods.append(m)

            if n.is_target:
                n.search_relevant = True
                visited_and_judged.append(n)
            elif not next_methods:
                n.search_relevant = False
                visited_and_judged.append(n)
            else:
                visited_and_not_judged.append(n)

            for m in next_methods:
                if m not in to_be_visited and m not in visited_and_judged and m not in visited_and_not_judged:
                    to_be_visited.append(m)

            some_movement = True

        for n in visited_and_not_judged:
            for out in n.output_ports:
                for c in out.connections:
                    m = c.input_port.method
                    if m.search_relevant and m in visited_and_judged:
                        n.search_relevant = True
                        visited_and_not_judged.remove(n)
                        visited_and_judged.append(n)
                        some_movement = True
                        break
                else:  # Weird construct to break out of outer loop if inner loop is broken
                    continue
                break

    for _, m in methods.items():
        for o in m.output_ports:
            for c in o.connections:
                if c.input_port.method.search_relevant and c.output_port.method.search_relevant:
                    c.search_relevant = True


def uncolor_graph(methods):
    # --- Reset methods and connections ---
    for m in methods.values():
        m.is_origin = False
        m.is_target = False
        m.search_relevant = False

        for port in m.input_ports + m.output_ports:
            for c in port.connections:
                c.search_relevant = False
