import unittest
import pathlib
import numpy as np

from marsDemonstrator.designMethods.en_13001_3_3 import EN_input


class En_test(unittest.TestCase):

    def setUp(self):
        self.config = "m1"
        self.direction = 1
        parent_path = pathlib.Path(__file__).parent.parent.absolute()
        input_file = parent_path  / "testdata"  / "test_geometry_material_input.xlsx"
        self.my_input = EN_input()
        self.my_input.load_material_input_check(input_file, "rail_materials", "wheel_materials")
        self.my_input.load_geometry_input_check(input_file, "rail_geometries", "wheel_geometries")
        self.my_input.read_input_df(input_file)
        self.my_input.load_parameter_input("General Input")
        self.my_input.set_materials_and_geometry()
        self.my_input.parameters.compute_contact_and_f_1()
        self.my_input.parameters.compute_f_f3()

        # load results
        self.expected_results_geometry = self.my_input.input_df.loc["Results Geometry", :].copy()
        self.expected_results_geometry.index = self.expected_results_geometry.iloc[:, 0]
        self.expected_results_geometry = self.expected_results_geometry.drop(self.expected_results_geometry.columns[0], axis=1)
        self.expected_results_geometry = self.expected_results_geometry.transpose()
        self.expected_results_geometry.index = range(len(self.expected_results_geometry))

        self.expected_results_materials = self.my_input.input_df.loc["Results Material", :].copy()
        self.expected_results_materials.index = self.expected_results_materials.iloc[:, 0]
        self.expected_results_materials = self.expected_results_materials.drop(self.expected_results_materials.columns[0], axis=1)
        self.expected_results_materials = self.expected_results_materials.transpose()
        self.expected_results_materials.index = range(len(self.expected_results_materials))

    def test_material_parameters(self):
        np.testing.assert_almost_equal(list(self.expected_results_materials["E_r"]), list(self.my_input.parameters.materials["rail"]["E"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["f_y_r"]), list(self.my_input.parameters.materials["rail"]["f_y"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["HB_r"]), list(self.my_input.parameters.materials["rail"]["HB"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["z_r"]), list(self.my_input.parameters.materials["rail"]["z"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["v_r"]), list(self.my_input.parameters.materials["rail"]["v"]))

        np.testing.assert_almost_equal(list(self.expected_results_materials["E_w"]), list(self.my_input.parameters.materials["wheel"]["E"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["f_y_w"]), list(self.my_input.parameters.materials["wheel"]["f_y"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["HB_w"]), list(self.my_input.parameters.materials["wheel"]["HB"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["z_w"]), list(self.my_input.parameters.materials["wheel"]["z"]))
        np.testing.assert_almost_equal(list(self.expected_results_materials["v_w"]), list(self.my_input.parameters.materials["wheel"]["v"]))

    def test_computed_geometry(self):
        # np.testing.assert_almost_equal(list(self.my_input.parameters.data["E_m_test"]), list(self.my_input.parameters.data["E_m"]))
        np.testing.assert_almost_equal(list(self.expected_results_geometry["b_min"]), list(self.my_input.parameters.data["b_min"]))
        self.assertEqual(list(self.expected_results_geometry["contact"]), list(self.my_input.parameters.data["contact"]))
        np.testing.assert_almost_equal(list(self.expected_results_geometry["f_1"]), list(self.my_input.parameters.data["f_1"]))
        np.testing.assert_almost_equal(list(self.expected_results_geometry["r_k"]), list(self.my_input.parameters.data["r_k"]))
        np.testing.assert_almost_equal(list(self.expected_results_geometry["f_f3"]), list(self.my_input.parameters.data["f_f3"]))


if __name__ == "__main_":
    unittest.main()
