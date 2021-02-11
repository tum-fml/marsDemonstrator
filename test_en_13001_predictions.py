import unittest
import pathlib
import numpy as np

from marsDemonstrator.designMethods.en_13001_3_3 import EN_input
from marsDemonstrator.designMethods.en_13001_3_3 import Computed_data


class En_test(unittest.TestCase):
    def setUp(self):
        self.config = "m1"
        self.direction = 1
        self.parent_path = pathlib.Path(__file__).parent.absolute()
        self.my_input = EN_input()
        self.computed_data = Computed_data()
        self.input_file = self.parent_path  / "test" / "testdata"  / "test_inputparameters_m1_l.xlsx"

    def test_predicted_data(self):
        self.my_input.load_gp_input(self.input_file, "configuration")
        self.my_input.load_parameter_input(self.input_file, "Input_variables")
        self.my_input.recompute_gp_data("m1")        
        gp_configs = {"m1": {1: "m1l", -1: "m1l"}, "m2": {1: "m2"}}
        gp_config = gp_configs[self.config][self.direction]
        parts = ["wf", "wr", "r"]
        self.computed_data.get_gps_kc(gp_config, parts)
        self.computed_data.predict_kc(self.my_input.gp_input.norm)
        self.computed_data.compute_F_sd_f_all(self.my_input.gp_input.raw, self.config, self.direction)
        self.computed_data.predict_travelled_dist(self.my_input.parameters.data)
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_rail_preds"]), list(self.computed_data.load_collective["r"]["k_c"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_rail_upper"]), list(self.computed_data.load_collective["r"]["k_c"]["upper"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wf_preds"]), list(self.computed_data.load_collective["wf"]["k_c"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wf_upper"]), list(self.computed_data.load_collective["wf"]["k_c"]["upper"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wr_preds"]), list(self.computed_data.load_collective["wr"]["k_c"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wr_upper"]), list(self.computed_data.load_collective["wr"]["k_c"]["upper"]))

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_sd_f_r_test"]), list(self.computed_data.load_collective["r"]["f_sd_f"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_sd_f_wr_test"]), list(self.computed_data.load_collective["wr"]["f_sd_f"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_sd_f_wf_test"]), list(self.computed_data.load_collective["wf"]["f_sd_f"]))


if __name__ == "__main_":
    unittest.main()
