import yaml
import yamlpyowl as ypo

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

# this list will hold the final ontology (2nd part)

nl = "\n"
separator = {"annotation": f"{nl*1}{'#'*5}{nl*1}"}

onto_list = []

MN_Type = "TypeEntity"
MN_Method = "MethodEntity"

for mn_type, inner_dict in types_dict.items():
    onto_list.append({"owl_individual":
                          {f"iMN_{mn_type}": {"types": [MN_Type]}}})

onto_list.append(separator)

for mn_method, inner_dict in methods_dict.items():
    onto_list.append({"owl_individual":
                          {f"iMN_{mn_method}": {"types": [MN_Method]}}})


onto_src_part2 = yaml.dump(onto_list, allow_unicode=True)

result_path = "mn-onto.owl.yml"
write_txt(result_path, f"{onto_src_part1}{separator['annotation']}{onto_src_part2}")

om = ypo.OntologyManager(result_path)

IPS()
