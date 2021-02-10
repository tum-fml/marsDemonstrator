import unittest
import pathlib
from itertools import chain

from marsDemonstrator.designMethods.en_13001_3_3 import EN_input


class En_test(unittest.TestCase):
    def setUp(self):
        self.config = "m1"
        self.direction = 1
        parent_path = pathlib.Path(__file__).parent.absolute()
        self.input_file = parent_path  / "test" / "testdata"  / "test_check_inputparameters.xlsx"
        self.my_input = EN_input()
        self.my_input.load_parameter_input(self.input_file, "Input_variables")
        self.my_input.load_gp_input(self.input_file, "configuration")

    def test_error_material_errors(self):
        self.my_input.materials.read(self.input_file, "rail_materials", "wheel_materials")
        _, error_mats = self.my_input.materials.get_errors()
        expected_result = ["GE-300", "S235"]
        result = error_mats
        self.assertEqual(result, expected_result)

    def test_gp_type_errors(self):
        self.my_input.gp_input.parse_type_check_data()
        self.my_input.gp_input.error_check.check_types()
        error_report, _ = self.my_input.gp_input.error_check.get_error_reports()
        result = error_report
        expected_result = ["type error in configuration no. 3; error variable: Traverse-Masse-Gesamt[kg]; expected type: number"]
        self.assertEqual(result, expected_result)

    def test_input_type_errors(self):
        self.my_input.materials.read(self.input_file, "rail_materials", "wheel_materials")
        self.my_input.parameters.parse_check_data(self.my_input.materials)
        self.my_input.parameters.error_check.check_types()
        expected_results = [
            "type error in configuration no. 1; error variable: b_r; expected type: number", 
            "type error in configuration no. 1; error variable: material_wheel; expected type: string",
            "type error in configuration no. 3; error variable: contact; expected type: string"
        ]

        results, _ = self.my_input.parameters.error_check.get_error_reports()
        for result, expected_result in zip(results, expected_results):
            self.assertEqual(result, expected_result)

    def test_input_value_errors(self):
        self.my_input.materials.read(self.input_file, "rail_materials", "wheel_materials")
        self.my_input.parameters.parse_check_data(self.my_input.materials)
        self.my_input.parameters.error_check.check_values()

        expected_results = [
            "value error in configuration no. 1; error variable: material_wheel; " 
                + "expected value from: ['GE-300', 'EN-GJS600-3', 'EN-GJS700-2', '25CrMo4', '34CrMo4', '42CrMo4', '33NiCrMoV14-5', '42CrMo4-hardened']",
            "value error in configuration no. 3; error variable: material_wheel; "
                + "expected value from: ['GE-300', 'EN-GJS600-3', 'EN-GJS700-2', '25CrMo4', '34CrMo4', '42CrMo4', '33NiCrMoV14-5', '42CrMo4-hardened']",
            "value error in configuration no. 3; error variable: contact; expected value from: ['point', 'line']"
        ]

        results, _ = self.my_input.parameters.error_check.get_error_reports()
        for result, expected_result in zip(results, expected_results):
            self.assertEqual(result, expected_result)

    def test_drop_error_configs(self):
        self.my_input.load_material_input_check(self.input_file, "rail_materials", "wheel_materials")
        self.my_input.perform_error_checks()
        result = list(set(chain(*self.my_input.error_configs)))
        expected_result = [0, 2, 4]
        self.assertEqual(result, expected_result)

    def test_gp_value_errors(self):
        self.my_input.load_material_input_check(self.input_file, "rail_materials", "wheel_materials")
        self.my_input.perform_error_checks()
        self.my_input.drop_error_configs()
        expected_result = 2
        result = len(self.my_input.parameters.data)
        self.assertEqual(result, expected_result)
        result = len(self.my_input.gp_input.raw)
        self.assertEqual(result, expected_result)
        result = len(self.my_input.gp_input.raw_out)
        self.assertEqual(result, expected_result)

        self.my_input.gp_input.recompute("m1")
        self.my_input.gp_input.modify_input_scales()
        self.my_input.gp_input.parse_value_check_data()
        self.my_input.gp_input.error_check.check_values()
        error_report, error_config =  self.my_input.gp_input.error_check.get_error_reports()
        
if __name__ == "__main_":
    unittest.main()
