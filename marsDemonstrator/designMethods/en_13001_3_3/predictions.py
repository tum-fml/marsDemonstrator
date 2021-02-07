import pathlib

import gpytorch as gp
import joblib
import numpy as np
import pandas as pd

from .gpytorchModels import ExactGPModel

mypath = pathlib.Path(__file__).parent.absolute()


class Computed_data():

    def __init__(self):
        travelled_dist = pd.DataFrame()
        self.load_collective = {part: {"k_c": pd.DataFrame(), "f_sd_f": None} 
                                for part in ["wf", "wr", "r"]}
        self.travelled_dist = travelled_dist
        self.gps = None

    def predict_kc(self, input_data):
        parts = ["wf", "wr", "r"]
        for part in parts:
            self.load_collective[part]["k_c"]["preds"], self.load_collective[part]["k_c"]["lower"], self.load_collective[part]["k_c"]["upper"] = self.gps[part].predict(input_data)

    def recompute_kc(self, f_sd_f_new, part):
        idx = idx = np.where(f_sd_f_new != 0)[0]
        f_sd_compute = self.load_collective[part]["f_sd_f"].copy()
        f_sd_compute[idx] = f_sd_f_new[idx]
        for field in ["preds", "upper"]:
            k_c_new = self.load_collective[part]["k_c"][field] * (self.load_collective[part]["f_sd_f"] ** (10 / 3))
            self.load_collective[part]["k_c"][field] = k_c_new / (f_sd_compute ** (10 / 3))
        self.load_collective[part]["f_sd_f"] = f_sd_compute

    def predict_travelled_dist(self, input_data):
        self.travelled_dist = np.ones(len(input_data)) * 10000000

    def compute_F_sd_f_all(self, input_data, config, crane_direction):

        f_wf = np.zeros((4, len(input_data)))
        f_wr = f_wf.copy()
        crane_configuration = self.get_crane_configuration(input_data, config)

        f_wf[0, :], f_wr[0, :] = self.compute_F_sd_f(crane_configuration, input_data["w_a"], input_data["l_a"], crane_direction)
        f_wf[1, :], f_wr[1, :] = self.compute_F_sd_f(crane_configuration, -input_data["w_a"], input_data["l_a"], crane_direction)
        f_wf[2, :], f_wr[2, :] = self.compute_F_sd_f(crane_configuration, -input_data["w_a"], -input_data["l_a"], crane_direction)
        f_wf[3, :], f_wr[3, :] = self.compute_F_sd_f(crane_configuration, input_data["w_a"], -input_data["l_a"], crane_direction)

        self.load_collective["wf"]["f_sd_f"] = np.max(abs(f_wf), axis=0)
        self.load_collective["wr"]["f_sd_f"] = np.max(abs(f_wr), axis=0)
        self.load_collective["r"]["f_sd_f"] = np.max(np.vstack((f_wf, f_wr)), axis=0)

    @staticmethod
    def get_crane_configuration(input_data, config):
        crane_configuration = input_data.copy()
        crane_configuration["l_m_t"] = crane_configuration["l_m"] + crane_configuration["l_m_ld"]
        crane_configuration["l_lv_x"] = crane_configuration["t_wd"] * crane_configuration["l_cg_x"]
        crane_configuration["m_lv_x"] = crane_configuration["t_wd"] * crane_configuration["m_cg_x"]
        if config == "m1":
            crane_configuration["l_lv_x"] = crane_configuration["m_lv_x"] + crane_configuration["l_cg_x"]    
        crane_configuration["l_lv_z"] = 1.3
        crane_configuration["t_m_t"] = (crane_configuration["t_wd"] * crane_configuration["t_m_l"] 
                                        + crane_configuration["t_m_a"] + 2 * 350)
        crane_configuration["t_lv_x"] = crane_configuration["t_cg_x"] * crane_configuration["t_wd"]
        crane_configuration["m_m_t"] = (crane_configuration["m_m_h"] * (crane_configuration["c_h"] - 0.8) 
                                        + crane_configuration["m_m_a"])
        crane_configuration["c_m"] = crane_configuration["m_m_t"] + crane_configuration["t_m_t"]
        crane_configuration["c_lv_z"] = crane_configuration["c_h"] * crane_configuration["c_cg_z"]

        return crane_configuration

    @staticmethod
    def compute_F_sd_f(crane_configuration, a_x, a_z, crane_direction):
        g_force = 9.81
        a_x = -a_x
        a_z = -a_z
        pos_z = crane_configuration["c_h"] + crane_configuration["l_lv_z"]
        f_right_static = (g_force/crane_configuration["t_wd"]
                          * (crane_configuration["l_m_t"] * crane_configuration["l_lv_x"]
                             + crane_configuration["t_m_t"] * crane_configuration["t_lv_x"]
                             + crane_configuration["m_m_t"] * crane_configuration["m_lv_x"]))

        f_right_dynamic = (1/crane_configuration["t_wd"]
                           * (crane_configuration["l_m_t"] * a_z * crane_configuration["l_lv_x"]
                              + crane_configuration["l_m_t"] * a_x * pos_z 
                              + crane_configuration["c_m"] * a_x * crane_configuration["c_lv_z"]))

        f_left_static = (g_force/crane_configuration["t_wd"]
                         * (crane_configuration["l_m_t"] * (crane_configuration["t_wd"] - crane_configuration["l_lv_x"]) 
                            + crane_configuration["t_m_t"] * (crane_configuration["t_wd"] - crane_configuration["t_lv_x"]) 
                            + crane_configuration["m_m_t"] * (crane_configuration["t_wd"] - crane_configuration["m_lv_x"])))

        f_left_dynamic = (1/crane_configuration["t_wd"]
                          * (crane_configuration["l_m_t"] * a_z * (crane_configuration["t_wd"] - crane_configuration["l_lv_x"]) 
                             - crane_configuration["l_m_t"] * a_x * pos_z
                             - crane_configuration["c_m"] * a_x * crane_configuration["c_lv_z"]))

        f_wf = f_left_static + f_left_dynamic if crane_direction == -1 else f_right_static + f_right_dynamic
        f_wr = f_right_static + f_right_dynamic if crane_direction == -1 else f_left_static + f_left_dynamic

        return np.array(f_wf), np.array(f_wr)

    def get_gps_kc(self, config, parts):

        def init_gp(part):
            gp_cur = ExactGPModel(data["X"], data[part], gp.likelihoods.GaussianLikelihood(), 
                                  gp.kernels.MaternKernel(ard_num_dims=17), gp.means.ZeroMean())
            gp_cur.double()
            gp_cur.train()
            gp_cur.load_state_dict(model_parameters[part]["state_dict"])
            gp_cur.eval()
            gp_cur.load_cache(model_parameters[part]["pred_dict"], data["X"])
            return gp_cur

        # init gps
        model_parameters = joblib.load(mypath / "model_parameters.pkl")
        data = joblib.load(mypath / "model_data.pkl")
        data = data[config]
        model_parameters = model_parameters[config]

        self.gps = {part: init_gp(part) for part in parts}
