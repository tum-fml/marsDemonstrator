import unittest
import pathlib
import numpy as np

from marsDemonstrator.designMethods.en_13001_3_3 import MARSInput # pylint: disable=import-error
from marsDemonstrator.designMethods.en_13001_3_3 import LoadCollectivePrediction # pylint: disable=import-error
from marsDemonstrator.designMethods.en_13001_3_3 import ENComputation # pylint: disable=import-error


class En_test(unittest.TestCase):

    def setUp(self):
        self.config = "m1"
        self.direction = 1
        parent_path = pathlib.Path(__file__).parent.parent.absolute()
        input_file = parent_path  / "testdata"  / "test_geometry_computation.xlsx"
        self.my_input = MARSInput()
        self.my_input.load_material_input_check(input_file, "rail_materials", "wheel_materials")
        self.my_input.load_geometry_input_check(input_file, "rail_geometries", "wheel_geometries")
        self.my_input.read_input_df(input_file)
        self.my_input.load_parameter_input("EN-13001-3-3")
        self.my_input.load_gp_input("Stacker Crane (SC) Configuration")
        self.my_input.set_materials_and_geometry()
        self.my_input.parameters.compute_contact_and_f_1()
        self.my_input.parameters.compute_f_f3()
        self.my_input.parameters.compute_contact_and_f_1()
        self.my_input.parameters.compute_f_f3()

        # load results for further computation
        self.design_params = self.my_input.input_df.loc["Design Params", :].copy()
        self.design_params.index = self.design_params.iloc[:, 0]
        self.design_params = self.design_params.drop(self.design_params.columns[0], axis=1)
        self.design_params = self.design_params.transpose()
        self.design_params.index = range(len(self.design_params))

        self.load_collective = self.my_input.input_df.loc["Load Collective", :].copy()
        self.load_collective.index = self.load_collective.iloc[:, 0]
        self.load_collective = self.load_collective.drop(self.load_collective.columns[0], axis=1)
        self.load_collective = self.load_collective.transpose()
        self.load_collective.index = range(len(self.load_collective))

        self.f_rd = self.my_input.input_df.loc["F_rd", :].copy()
        self.f_rd.index = self.f_rd.iloc[:, 0]
        self.f_rd = self.f_rd.drop(self.f_rd.columns[0], axis=1)
        self.f_rd = self.f_rd.transpose()
        self.f_rd.index = range(len(self.f_rd))

        # load expected results
        self.expected_results = self.my_input.input_df.loc["Expected Results", :].copy()
        self.expected_results.index = self.expected_results.iloc[:, 0]
        self.expected_results = self.expected_results.drop(self.expected_results.columns[0], axis=1)
        self.expected_results = self.expected_results.transpose()
        self.expected_results.index = range(len(self.expected_results))

        self.my_input.recompute_gp_data("m1")
        self.predicted_data = LoadCollectivePrediction()

        self.en_computation = None

    def test_repredicted_data(self):
        # self.predicted_data.predict_kc(self.my_input.gp_input.norm)
        self.predicted_data.compute_F_sd_f_all(self.my_input.gp_input.raw, self.config, self.direction)
        np.testing.assert_almost_equal(list(self.expected_results["F_sd_f_r"]), list(self.predicted_data.load_collective["r"]["f_sd_f"]))
        np.testing.assert_almost_equal(list(self.expected_results["F_sd_f_wf"]), list(self.predicted_data.load_collective["wf"]["f_sd_f"]))
        np.testing.assert_almost_equal(list(self.expected_results["F_sd_f_wr"]), list(self.predicted_data.load_collective["wr"]["f_sd_f"]))

        self.load_k_c()
        if any(self.my_input.parameters.gen_params["F_sd_f_w"] > 0):
            self.predicted_data.recompute_kc(self.my_input.parameters.gen_params["F_sd_f_w"], "wf")
            self.predicted_data.recompute_kc(self.my_input.parameters.gen_params["F_sd_f_w"], "wr")

        if any(self.my_input.parameters.gen_params["F_sd_f_r"] > 0):
            self.predicted_data.recompute_kc(self.my_input.parameters.gen_params["F_sd_f_r"], "r")

        np.testing.assert_almost_equal(list(self.expected_results["k_c_rail_preds_expected"]), list(self.predicted_data.load_collective["r"]["k_c"]["preds"] * 1e6))
        np.testing.assert_almost_equal(list(self.expected_results["k_c_rail_upper_expected"]), list(self.predicted_data.load_collective["r"]["k_c"]["upper"] * 1e6))
        np.testing.assert_almost_equal(list(self.expected_results["k_c_wf_preds_expected"]), list(self.predicted_data.load_collective["wf"]["k_c"]["preds"] * 1e6))
        np.testing.assert_almost_equal(list(self.expected_results["k_c_wf_upper_expected"]), list(self.predicted_data.load_collective["wf"]["k_c"]["upper"] * 1e6))
        np.testing.assert_almost_equal(list(self.expected_results["k_c_wr_preds_expected"]), list(self.predicted_data.load_collective["wr"]["k_c"]["preds"] * 1e6))
        np.testing.assert_almost_equal(list(self.expected_results["k_c_wr_upper_expected"]), list(self.predicted_data.load_collective["wr"]["k_c"]["upper"] * 1e6))

    def test_computed_proofs(self):
        self.predicted_data.predict_travelled_dist(self.my_input.gp_input.raw["cycle_mode"], self.my_input.gp_input.raw["num_cycles_wheel"], self.my_input.gp_input.raw["r_l"])
        self.load_load_collective()

        self.en_computation = ENComputation()
        self.en_computation.load_data(self.my_input, self.predicted_data)
        self.load_design_param()
        self.en_computation.compute_pre_F_rd_all()

        np.testing.assert_almost_equal(list(self.expected_results["z_r"]), list(self.en_computation.rail.z))
        np.testing.assert_almost_equal(list(self.expected_results["z_w"]), list(self.en_computation.wheel_f.z))
        np.testing.assert_almost_equal(list(self.expected_results["z_w"]), list(self.en_computation.wheel_r.z))

        np.testing.assert_almost_equal(list(self.expected_results["F_rd_s_r"]), list(self.en_computation.rail.F_rd["F_rd_s"]))
        np.testing.assert_almost_equal(list(self.expected_results["F_rd_s_w"]), list(self.en_computation.wheel_f.F_rd["F_rd_s"]))
        np.testing.assert_almost_equal(list(self.expected_results["F_rd_s_w"]), list(self.en_computation.wheel_r.F_rd["F_rd_s"]))

        np.testing.assert_almost_equal(list(self.expected_results["F_u_r"]), list(self.en_computation.rail.F_rd["F_u"]))
        np.testing.assert_almost_equal(list(self.expected_results["F_u_w"]), list(self.en_computation.wheel_f.F_rd["F_u"]))
        np.testing.assert_almost_equal(list(self.expected_results["F_u_w"]), list(self.en_computation.wheel_r.F_rd["F_u"]))

        np.testing.assert_almost_equal(list(self.expected_results["f_ff_rail"]), list(self.en_computation.rail.factors["f_ff"]))
        np.testing.assert_almost_equal(list(self.expected_results["f_ff_wheel"]), list(self.en_computation.wheel_f.factors["f_ff"]))
        np.testing.assert_almost_equal(list(self.expected_results["f_ff_wheel"]), list(self.en_computation.wheel_r.factors["f_ff"]))

        np.testing.assert_almost_equal(list(self.expected_results["v_c_rail"]), list(self.en_computation.rail.load_collective["v_c"]), decimal=4)
        np.testing.assert_almost_equal(list(self.expected_results["v_c_wheel"]), list(self.en_computation.wheel_f.load_collective["v_c"]), decimal=4)
        np.testing.assert_almost_equal(list(self.expected_results["v_c_wheel"]), list(self.en_computation.wheel_r.load_collective["v_c"]), decimal=4)

        self.load_F_u_ff_v_c()
        self.en_computation.des_params["E_m"] = self.design_params["E_m"]
        self.en_computation.compute_F_rd_all()
        np.testing.assert_almost_equal(list(self.expected_results["F_rd_f_r"]), list(self.en_computation.rail.F_rd["F_rd_f"]["preds"]), decimal=4)
        np.testing.assert_almost_equal(list(self.expected_results["F_rd_f_wf"]), list(self.en_computation.wheel_f.F_rd["F_rd_f"]["preds"]), decimal=4)
        np.testing.assert_almost_equal(list(self.expected_results["F_rd_f_wr"]), list(self.en_computation.wheel_r.F_rd["F_rd_f"]["preds"]), decimal=4)

    def load_k_c(self):
        self.predicted_data.load_collective["r"]["k_c"]["preds"] = self.load_collective["k_c_rail_preds"]
        self.predicted_data.load_collective["r"]["k_c"]["upper"] = self.load_collective["k_c_rail_upper"]
        self.predicted_data.load_collective["wf"]["k_c"]["preds"] = self.load_collective["k_c_wf_preds"]
        self.predicted_data.load_collective["wf"]["k_c"]["upper"] = self.load_collective["k_c_wf_upper"]
        self.predicted_data.load_collective["wr"]["k_c"]["preds"] = self.load_collective["k_c_wr_preds"]
        self.predicted_data.load_collective["wr"]["k_c"]["upper"] = self.load_collective["k_c_wr_upper"]

    def load_load_collective(self):
        self.predicted_data.load_collective["r"]["k_c"]["preds"] = self.expected_results["k_c_rail_preds_new"]
        self.predicted_data.load_collective["r"]["k_c"]["upper"] = self.expected_results["k_c_rail_upper_new"]
        self.predicted_data.load_collective["wf"]["k_c"]["preds"] = self.expected_results["k_c_wf_preds_new"]
        self.predicted_data.load_collective["wf"]["k_c"]["upper"] = self.expected_results["k_c_wf_upper_new"]
        self.predicted_data.load_collective["wr"]["k_c"]["preds"] = self.expected_results["k_c_wr_preds_new"]
        self.predicted_data.load_collective["wr"]["k_c"]["upper"] = self.expected_results["k_c_wr_upper_new"]

        self.predicted_data.load_collective["r"]["f_sd_f"] = self.load_collective["F_sd_f_r"]
        self.predicted_data.load_collective["wf"]["f_sd_f"] = self.load_collective["F_sd_f_w"]
        self.predicted_data.load_collective["wr"]["f_sd_f"] = self.load_collective["F_sd_f_w"]

    def load_F_u_ff_v_c(self):
        self.en_computation.rail.F_rd["F_u"] = self.f_rd["F_u_r"]
        self.en_computation.wheel_f.F_rd["F_u"] = self.f_rd["F_u_w"]
        self.en_computation.wheel_f.F_rd["F_u"] = self.f_rd["F_u_w"]

        self.en_computation.rail.factors["f_ff"] = self.f_rd["f_ff_rail"]
        self.en_computation.wheel_f.factors["f_ff"] = self.f_rd["f_ff_wheel"]
        self.en_computation.wheel_r.factors["f_ff"] = self.f_rd["f_ff_wheel"]

    def load_design_param(self):
        self.en_computation.des_params = self.design_params


if __name__ == "__main_":
    unittest.main()
