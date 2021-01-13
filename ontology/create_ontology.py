import yaml

# noinspection PyPackageRequirements
from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()


base_ontology_path = "control-systems-knowledge_draft_part1.owl.yml"


def load_yaml(path):
    with open(path, 'r', encoding='utf8') as f:
        yaml_content = yaml.load(f, Loader=yaml.SafeLoader)
        return yaml_content


def load_txt(path):
    with open(path, 'r', encoding='utf8') as f:
        txt = f.read()
    return txt


def write_as_yaml(path, yaml_content):
    with open(path, 'w', encoding='utf8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)


def write_txt(path, txt):
    with open(path, 'w', encoding='utf8') as f:
        f.write(txt)


onto_src_part1 = load_txt(base_ontology_path)

mn_types_methods_yaml_dict = load_yaml("../new_types.yml")


types_dict = mn_types_methods_yaml_dict.get("types")
methods_dict = mn_types_methods_yaml_dict.get("methods")

# this dict will hold the final ontology

type_classes = []
method_classes = []
nl = "\n"
separator = f"{nl*1}{'#'*5}{nl*1}"

onto_list = [{"multiple_owl_classes": type_classes}, separator, {"multiple_owl_classes": method_classes}]

MN_Type = "MN_Type"
MN_Method = "MN_Method"

for mn_type, inner_dict in types_dict.items():
    type_classes.append({f"MN_{mn_type}": {"SubClassOf": MN_Type}})

for mn_method, inner_dict in methods_dict.items():
    method_classes.append({f"MN_{mn_method}": {"SubClassOf": MN_Method}})


onto_src_part2 = yaml.dump(onto_list, allow_unicode=True)


write_txt("mn-onto.owl.yml", f"{onto_src_part1}{separator}{onto_src_part2}")


IPS()
