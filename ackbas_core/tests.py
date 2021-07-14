from django.test import TestCase

from ackbas_core.knowledge_graph import RTGraph, RTEnumType, RTParamPlaceholder, RTParamUnset, RTEnumValue
from ackbas_core.solution_sketch import RTObjectInstance
from ackbas_core.views import GetSolutionGraphView


class KnowledgeGraphTest(TestCase):
    def test_load_from_yml(self):
        graph = RTGraph('minimal.yml')
        self.assertEqual(len(graph.types), 4)
        self.assertEqual(len(graph.methods), 5)

        self.assertEqual(len(graph.types["TypeWithoutParams"].params), 0)
        self.assertEqual(len(graph.types["TypeTwo"].params), 2)
        self.assertEqual(graph.types["TypeTwo"].params["ValueEnum"].type.name, "MyEnum")

        self.assertEqual(len(graph.param_types), 2)  # Int and MyEnum
        self.assertIsInstance(graph.param_types["MyEnum"], RTEnumType)
        self.assertListEqual(graph.param_types["MyEnum"].values, ["One", "Two"])

        self.assertIsInstance(graph.methods["Convert"].inputs["in"].param_constraints["ValueOne"], RTParamPlaceholder)
        self.assertEqual(graph.methods["Convert"].inputs["in"].param_constraints["ValueOne"].name, "n")
        self.assertIsInstance(graph.methods["Convert"].outputs["optionOne"]["out"].param_statements["ValueTwo"], RTParamPlaceholder)

        self.assertIsInstance(graph.methods["TestProperty"].inputs["objectTwo"].param_constraints["ValueEnum"], RTParamUnset)
        self.assertIsInstance(graph.methods["TestProperty"].outputs["optionGood"]["objectTwo"].param_statements["ValueEnum"], RTEnumValue)
        self.assertEqual(graph.methods["TestProperty"].outputs["optionGood"]["objectTwo"].param_statements["ValueEnum"].val, 0)


class SolutionSketchTest(TestCase):
    def test_solution(self):
        start_dict = {
            "start": {
                "type": "TypeOne",
                "params": {
                    "ValueOne": "123456"
                }
            }
        }

        target_dict = {
            "target": {
                "type": "TypeThree"
            }
        }

        sol = GetSolutionGraphView.get_solution("minimal", start_dict, target_dict)

        def constructable_from_start_objects(obj_id):
            obj = [obj for obj in sol["objects"] if obj["id"] == obj_id][0]
            if obj["is_start"]:
                return True

            preceeding_method_id = [con["fromId"] for con in sol["connections"] if con["toId"] == obj_id][0]
            preceeding_object_ids = [con["fromId"] for con in sol["connections"] if con["toId"] == preceeding_method_id]

            return all(constructable_from_start_objects(other_obj_id) for other_obj_id in preceeding_object_ids)

        self.assertTrue(all(constructable_from_start_objects(obj["id"]) for obj in sol["objects"] if obj["is_end"]))
