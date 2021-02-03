import yaml
import yamlpyowl as ypo

# noinspection PyPackageRequirements, PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()


base_ontology_path = "orm_draft_part1.owl.yml"


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


# noinspection PyShadowingNames
def get_input_types(raw_dict: dict) -> list:
    res = []
    for key, inner_dict in raw_dict.items():
        res.append(inner_dict["type"])
    return res


# noinspection PyShadowingNames
def get_output_types(raw_dict: dict) -> list:
    res = []
    # outputs are organized as follows:
    """
    outputs:
      teilerfremd:          # output option
        tf:                 # output name
          type: ÜTF
          # ...
      nichtTeilerfremd:     # output option
        tf:                 # output name
          type: ÜTF
          # ...
    """
    for outputoption, inner_dict1 in raw_dict.items():
        for outputname, inner_dict2 in inner_dict1.items():
            res.append(inner_dict2["type"])

    # make output types unique
    res = list(set(res))
    return res


onto_src_part1 = load_txt(base_ontology_path)

mn_types_methods_yaml_dict = load_yaml("../new_types.yml")


types_dict = mn_types_methods_yaml_dict.get("types")
methods_dict = mn_types_methods_yaml_dict.get("methods")

# this list will hold the final ontology (2nd part)

nl = "\n"
separator = {"annotation": f"{nl*1}{'#'*5}{nl*1}"}

onto_list = []

# temporarily store information about inputs and outputs
input_facts = []
output_facts = []

MN_Type = "TypeEntity"
MN_Method = "MethodEntity"

# handle types
for mn_type, inner_dict in types_dict.items():
    onto_list.append({"owl_individual":
                          {f"i_{mn_type}": {"types": [MN_Type]}}})

onto_list.append(separator)

# handle methods
for mn_method, inner_dict in methods_dict.items():

    idv_name = f"i_{mn_method}"

    onto_list.append({"owl_individual":
                          {idv_name: {"types": [MN_Method]}}})

    input_dict = inner_dict["inputs"]
    outputs_dict = inner_dict["outputs"]

    input_types = get_input_types(input_dict)
    for it in input_types:
        input_facts.append({idv_name: f"i_{it}"})

    output_types = get_output_types(outputs_dict)
    for ot in output_types:
        output_facts.append({idv_name: f"i_{ot}"})

onto_list.append({"property_facts": {"hasForInput": {"Facts": input_facts}}})
onto_list.append({"property_facts": {"hasForOutput": {"Facts": output_facts}}})


onto_src_part2 = yaml.dump(onto_list, allow_unicode=True)

result_path = "orm_draft.owl.yml"
write_txt(result_path, f"{onto_src_part1}{separator['annotation']}{onto_src_part2}")

om = ypo.OntologyManager(result_path)
