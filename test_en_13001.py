import unittest
import pathlib
import numpy as np
from marsDemonstrator.designMethods.en_13001_3_3 import User_input
# from designMethods.en_13001_3_3 import User_input
from marsDemonstrator.designMethods.en_13001_3_3 import Computed_data
from marsDemonstrator.designMethods.en_13001_3_3 import Computation


class En_test(unittest.TestCase):
    def setUp(self):
        self.config = "m1"
        self.direction = 1
        parent_path = pathlib.Path(__file__).parent.absolute()
        # input_file = "C://Dokumente//MARS//design-methods//inputparameters.xlsx"
        input_file = parent_path / "test" / "testdata"  / "test_inputparameters_m1_l.xlsx"
        self.my_input = User_input()
        self.my_input.load_gp_input(input_file, "configuration", "m1")
        self.my_input.load_parameter_input(input_file, "Input_variables")
        self.my_input.load_material_input(input_file, "rail_materials", "wheel_materials")
        self.my_input.set_materials_and_geometry()
        self.my_input.parameters.compute_f_f3()
        self.my_input.parameters.compute_contact_and_f_1()
        self.en_computation = None
        self.computed_data = Computed_data()

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

    def test_predicted_data(self):
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

    def test_recomputed_data(self):
        # self.computed_data.predict_kc(self.my_input.gp_input.norm)
        self.computed_data.compute_F_sd_f_all(self.my_input.gp_input.raw, self.config, self.direction)
        self.load_k_c()
        if any(self.my_input.parameters.data["F_sd_f_w"] > 0):
            # print("recompute wheels")
            self.computed_data.recompute_kc(self.my_input.parameters.data["F_sd_f_w"], "wf")
            self.computed_data.recompute_kc(self.my_input.parameters.data["F_sd_f_w"], "wr")

        if any(self.my_input.parameters.data["F_sd_f_r"] > 0):
            # print("recompute rail")
            self.computed_data.recompute_kc(self.my_input.parameters.data["F_sd_f_r"], "r")

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_rail_preds_new"]), list(self.computed_data.load_collective["r"]["k_c"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_rail_upper_new"]), list(self.computed_data.load_collective["r"]["k_c"]["upper"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wf_preds_new"]), list(self.computed_data.load_collective["wf"]["k_c"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wf_upper_new"]), list(self.computed_data.load_collective["wf"]["k_c"]["upper"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wr_preds_new"]), list(self.computed_data.load_collective["wr"]["k_c"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["k_c_wr_upper_new"]), list(self.computed_data.load_collective["wr"]["k_c"]["upper"]))

    def test_computed_proofs(self):
        self.computed_data.predict_travelled_dist(self.my_input.parameters.data)
        self.load_load_collective()

        self.en_computation = Computation(self.my_input, self.computed_data)
        self.en_computation.compute_pre_F_rd_all()

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["z_r"]), list(self.en_computation.rail.z))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["z_w"]), list(self.en_computation.wheel_f.z))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["z_w"]), list(self.en_computation.wheel_r.z))

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_rd_s_r"]), list(self.en_computation.rail.F_rd["F_rd_s"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_rd_s_w"]), list(self.en_computation.wheel_f.F_rd["F_rd_s"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_rd_s_w"]), list(self.en_computation.wheel_r.F_rd["F_rd_s"]))

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_u_r"]), list(self.en_computation.rail.F_rd["F_u"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_u_w"]), list(self.en_computation.wheel_f.F_rd["F_u"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_u_w"]), list(self.en_computation.wheel_r.F_rd["F_u"]))

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_ff_rail"]), list(self.en_computation.rail.factors["f_ff"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_ff_wheel"]), list(self.en_computation.wheel_f.factors["f_ff"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["f_ff_wheel"]), list(self.en_computation.wheel_r.factors["f_ff"]))

        np.testing.assert_almost_equal(list(self.my_input.parameters.data["v_c_rail"]), list(self.en_computation.rail.load_collective["v_c"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["v_c_wheel"]), list(self.en_computation.wheel_f.load_collective["v_c"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["v_c_wheel"]), list(self.en_computation.wheel_r.load_collective["v_c"]))

        self.load_F_u_ff_v_c()
        self.en_computation.des_params["E_m"] = self.my_input.parameters.data["E_m"]
        self.en_computation.compute_F_rd_all()
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_rd_f_r"]), list(self.en_computation.rail.F_rd["F_rd_f"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_rd_f_wf"]), list(self.en_computation.wheel_f.F_rd["F_rd_f"]["preds"]))
        np.testing.assert_almost_equal(list(self.my_input.parameters.data["F_rd_f_wr"]), list(self.en_computation.wheel_r.F_rd["F_rd_f"]["preds"]))

    def load_k_c(self):
        self.computed_data.load_collective["r"]["k_c"]["preds"] = self.my_input.parameters.data["k_c_rail_preds"]
        self.computed_data.load_collective["r"]["k_c"]["upper"] = self.my_input.parameters.data["k_c_rail_upper"]
        self.computed_data.load_collective["wf"]["k_c"]["preds"] = self.my_input.parameters.data["k_c_wf_preds"]
        self.computed_data.load_collective["wf"]["k_c"]["upper"] = self.my_input.parameters.data["k_c_wf_upper"]
        self.computed_data.load_collective["wr"]["k_c"]["preds"] = self.my_input.parameters.data["k_c_wr_preds"]
        self.computed_data.load_collective["wr"]["k_c"]["upper"] = self.my_input.parameters.data["k_c_wr_upper"]

    def load_load_collective(self):
        self.computed_data.load_collective["r"]["k_c"]["preds"] = self.my_input.parameters.data["k_c_rail_preds_new"]
        self.computed_data.load_collective["r"]["k_c"]["upper"] = self.my_input.parameters.data["k_c_rail_upper_new"]
        self.computed_data.load_collective["wf"]["k_c"]["preds"] = self.my_input.parameters.data["k_c_wf_preds_new"]
        self.computed_data.load_collective["wf"]["k_c"]["upper"] = self.my_input.parameters.data["k_c_wf_upper_new"]
        self.computed_data.load_collective["wr"]["k_c"]["preds"] = self.my_input.parameters.data["k_c_wr_preds_new"]
        self.computed_data.load_collective["wr"]["k_c"]["upper"] = self.my_input.parameters.data["k_c_wr_upper_new"]

        self.computed_data.load_collective["r"]["f_sd_f"] = self.my_input.parameters.data["F_sd_f_r"]
        self.computed_data.load_collective["wf"]["f_sd_f"] = self.my_input.parameters.data["F_sd_f_w"]
        self.computed_data.load_collective["wr"]["f_sd_f"] = self.my_input.parameters.data["F_sd_f_w"]

    def load_F_u_ff_v_c(self):
        self.en_computation.rail.F_rd["F_u"] = self.my_input.parameters.data["F_u_r"]
        self.en_computation.wheel_f.F_rd["F_u"] = self.my_input.parameters.data["F_u_w"]
        self.en_computation.wheel_f.F_rd["F_u"] = self.my_input.parameters.data["F_u_w"]

        self.en_computation.rail.factors["f_ff"] = self.my_input.parameters.data["f_ff_rail"]
        self.en_computation.wheel_f.factors["f_ff"] = self.my_input.parameters.data["f_ff_wheel"]
        self.en_computation.wheel_r.factors["f_ff"] = self.my_input.parameters.data["f_ff_wheel"]

        self.en_computation.rail.load_collective["v_c"] = self.my_input.parameters.data["v_c_rail"]
        self.en_computation.wheel_f.load_collective["v_c"] = self.my_input.parameters.data["v_c_wheel"]
        self.en_computation.wheel_r.load_collective["v_c"] = self.my_input.parameters.data["v_c_wheel"]




if __name__ == "__main_":
    unittest.main()
