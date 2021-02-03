import gpytorch as gp
import joblib
import numpy as np
import pandas as pd

from gpytorchModels import ExactGPModel


def get_gps_kc(config, parts):

    def init_gp(part):
        gp_cur = ExactGPModel(data["X"], data[part], likelihood, kernel, mean)
        gp_cur.load_state_dict(model_parameters[part]["state_dict"])
        gp_cur.double()
        gp_cur.eval()
        gp_cur.load_cache(model_parameters[part]["pred_dict"], data["X"])

        return gp_cur

    # init gps
    model_parameters = joblib.load("model_parameters.pkl")
    data = joblib.load("model_data.pkl")
    data = data[config]
    model_parameters = model_parameters[config]
    kernel = gp.kernels.MaternKernel(ard_num_dims=17)
    mean = gp.means.ZeroMean()
    likelihood = gp.likelihoods.GaussianLikelihood()
    likelihood.double()

    gps = list(map(init_gp, parts))
    return {part: gp_cur for part, gp_cur in zip(parts, gps)} 


def predict_kc(config, input_data):
    parts = ["wf", "wr", "r"]
    gps = get_gps_kc(config, parts)
    kc_preds = pd.DataFrame()
    kc_upper = pd.DataFrame()
    kc_lower = pd.DataFrame()
    for part in parts:
        kc_preds[part], kc_lower[part], kc_upper[part] = gps[part].predict(input_data)

    return kc_preds, kc_lower, kc_upper


def compute_F_sd_f_all(input_data, config, crane_direction):

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
        crane_configuration["m_m_t"] = crane_configuration["m_m_h"] * (crane_configuration["c_h"] - 0.8) + crane_configuration["m_m_a"]
        crane_configuration["c_m"] = crane_configuration["m_m_t"] + crane_configuration["t_m_t"]
        crane_configuration["c_lv_z"] = crane_configuration["c_h"] * crane_configuration["c_cg_z"]

        return crane_configuration

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

    f_wf = np.zeros((4, len(input_data)))
    f_wr = f_wf.copy()
    crane_configuration = get_crane_configuration(input_data, config)

    f_wf[0, :], f_wr[0, :] = compute_F_sd_f(crane_configuration, input_data["w_a"], input_data["l_a"], crane_direction)
    f_wf[1, :], f_wr[1, :] = compute_F_sd_f(crane_configuration, -input_data["w_a"], input_data["l_a"], crane_direction)
    f_wf[2, :], f_wr[2, :] = compute_F_sd_f(crane_configuration, -input_data["w_a"], -input_data["l_a"], crane_direction)
    f_wf[3, :], f_wr[3, :] = compute_F_sd_f(crane_configuration, input_data["w_a"], -input_data["l_a"], crane_direction)

    f_wf = np.max(abs(f_wf), axis=0)
    f_wr = np.max(abs(f_wr), axis=0)
    f_r = np.max(np.vstack((f_wf, f_wr)), axis=0)

    return {"wf": f_wf, "wr": f_wr, "r": f_r}
