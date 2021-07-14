from django.test import TestCase

from ackbas_core.knowledge_graph import RTGraph, RTEnumType, RTParamPlaceholder, RTParamUnset, RTEnumValue


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
