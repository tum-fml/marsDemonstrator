import unittest
import pathlib
import numpy as np

from marsDemonstrator.designMethods.en_13001_3_3 import EN_input


class En_test(unittest.TestCase):

    def setUp(self):
        self.config = "m1"
        self.direction = 1
        parent_path = pathlib.Path(__file__).parent.absolute()
        input_file = parent_path  / "test" / "testdata"  / "test_inputparameters_m1_l.xlsx"
        self.my_input = EN_input()
        self.my_input.load_material_input_check(input_file, "rail_materials", "wheel_materials")
        self.my_input.load_gp_input(input_file, "configuration")
        self.my_input.load_parameter_input(input_file, "Input_variables")
        self.my_input.recompute_gp_data("m1")
        self.my_input.set_materials_and_geometry()
        self.my_input.parameters.compute_contact_and_f_1()
        self.my_input.parameters.compute_f_f3()

    def test_material_parameters(self):
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["E_rail"]), list(self.my_input.parameters.materials["rail"]["E"])) 
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["E_rail"]), list(self.my_input.parameters.materials["rail"]["E"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_y_rail"]), list(self.my_input.parameters.materials["rail"]["f_y"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["HB_rail"]), list(self.my_input.parameters.materials["rail"]["HB"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["z_rail_material"]), list(self.my_input.parameters.materials["rail"]["z"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["v_rail"]), list(self.my_input.parameters.materials["rail"]["v"]))

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["E_wheel"]), list(self.my_input.parameters.materials["wheel"]["E"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_y_wheel"]), list(self.my_input.parameters.materials["wheel"]["f_y"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["HB_wheel"]), list(self.my_input.parameters.materials["wheel"]["HB"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["z_wheel_material"]), list(self.my_input.parameters.materials["wheel"]["z"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["v_wheel"]), list(self.my_input.parameters.materials["wheel"]["v"]))

    def test_computed_geometry(self):
        # np.testing.assert_almost_equal(list(self.my_input.parameters.data["E_m_test"]), list(self.my_input.parameters.data["E_m"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["b_min_test"]), list(self.my_input.parameters.data["b_min"]))
        self.assertEqual(list(self.my_input.parameters.data["contact_out"]), list(self.my_input.parameters.data["contact"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_1_test"]), list(self.my_input.parameters.data["f_1"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["r_k_b_min_test"]), list(self.my_input.parameters.data["r_k_b_min"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["r_k_b_min_test"]), list(self.my_input.parameters.data["r_k_b_min"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_f3"]), list(self.my_input.parameters.data["f_ff3_test"]))


if __name__ == "__main_":
    unittest.main()
