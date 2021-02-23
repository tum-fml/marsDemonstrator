import pathlib

import gpytorch as gp
import joblib
import numpy as np
import pandas as pd

from .gpytorchModels import ExactGPModel
from . import gpytorchModels as gpytorchModels

mypath = pathlib.Path(__file__).parent.absolute()


class LoadCollectivePrediction():
    """Class for predicting k_c and v_c for rail and wheels

    Attributes:
    -----------
    gps: Dict
        Contains gaussian process models for predicting k_c for wheels and rail

    travelled_dist: Numpy array
        Computed travelled distance in x-direction over wheels' life cylce

    load_collective: Dict of DataFrames
        Contains k_c (pred and upper confidence) and f_sd_f

    """    

    def __init__(self):
        self.travelled_dist = None
        self.load_collective = {part: {"k_c": pd.DataFrame(), "f_sd_f": None} 
                                for part in ["wf", "wr", "r"]}
        self.gps = None

    def clear_prediction_results(self):
        self.load_collective = {part: {"k_c": pd.DataFrame(), "f_sd_f": None} 
                                for part in ["wf", "wr", "r"]}

    def predict_kc(self, input_data):

        # make predictions for k_c for wheels and rail
        parts = ["wf", "wr", "r"]
        for part in parts:
            self.gps[part].float()
            self.load_collective[part]["k_c"]["preds"], self.load_collective[part]["k_c"]["lower"], self.load_collective[part]["k_c"]["upper"] = self.gps[part].predict(input_data)

    def recompute_kc(self, f_sd_f_new, part):
        """Recompute k_c with user given f_sd

        Parameters
        ----------
        f_sd_f_new : DataFrame / np.array
            User give f_sd
        part : str
            [wf, wr, r]
        """    

        # get idx of computation runs where user gave f_sd_f and get their f_sd_f   
        idx = idx = np.where(f_sd_f_new != 0)[0]
        f_sd_compute = self.load_collective[part]["f_sd_f"].copy()
        f_sd_compute[idx] = f_sd_f_new[idx]

        # recompute k_c
        for field in ["preds", "upper"]:
            k_c_new = self.load_collective[part]["k_c"][field] * (self.load_collective[part]["f_sd_f"] ** (10 / 3))
            self.load_collective[part]["k_c"][field] = k_c_new / (f_sd_compute ** (10 / 3))

        # copy user given f_sd_f into load_collective's f_sd_f
        self.load_collective[part]["f_sd_f"] = f_sd_compute

    def predict_travelled_dist(self, cycle_mode, num_cycles, rack_length):

        # compute travelled dist based on cycle mode number of cylces for wheels and rack length
        mean_travelled_dist = np.ones(len(cycle_mode)) * 0.3
        mean_travelled_dist[np.where(cycle_mode == 1)[0]] = 0.4
        mean_travelled_dist[np.where(cycle_mode == 2)[0]] = 0.5
        self.travelled_dist = num_cycles * rack_length * mean_travelled_dist

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
            gp_cur = ExactGPModel(data["X"].float(), data[part].float(), gp.likelihoods.GaussianLikelihood().float(), 
                                  gp.kernels.MaternKernel(ard_num_dims=17).float(), gp.means.ZeroMean().float())
            gp_cur.float()
            gp_cur.train()
            for field in model_parameters_cur[part]["state_dict"]:
                model_parameters_cur[part]["state_dict"][field].float()
            gp_cur.load_state_dict(model_parameters_cur[part]["state_dict"])
            gp_cur.covar_module.float()
            gp_cur.eval()
            gp_cur.load_cache(model_parameters_cur[part]["pred_dict"], data["X"].float())
            gp_cur.float()
            gp_cur.prediction_strategy.mean_cache.data = gp_cur.prediction_strategy.mean_cache.data.float()
            gp_cur.prediction_strategy.covar_cache.data = gp_cur.prediction_strategy.covar_cache.data.float()
            return gp_cur

        # init gps
        model_parameters = joblib.load(mypath / "model_parameters.pkl")
        data = joblib.load(mypath / "model_data.pkl")
        data = data[config]
        model_parameters_cur = model_parameters[config]

        self.gps = {part: init_gp(part) for part in parts}

    def load_gps(self, config):
        # load gps directly from pkl
        gps = joblib.load(mypath / "gps.pkl")
        self.gps = gps[config]
