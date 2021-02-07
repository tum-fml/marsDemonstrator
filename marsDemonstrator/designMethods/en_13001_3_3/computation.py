import math
from collections import namedtuple
import numpy as np
import pandas as pd
# import abc

Coefficients = namedtuple("Coefficients", ["Y_m", "Y_cf", "m", "Y_p"])


class Computation():

    # functions
    def __init__(self, user_input, computed_data):
        input_df = user_input.parameters.data
        self.des_params = {"b": input_df["b_min"],
                           "f_1": input_df["f_1"],
                           "f_2": input_df["f_2"],
                           "w": input_df["w"],
                           "contact": input_df["contact"]}
        self.coefficients = Coefficients(1.1, 1.1, 10/3, 1)
        self.wheel_f = Wheel(user_input, computed_data, "wheel", "wf")
        self.wheel_r = Wheel(user_input, computed_data, "wheel", "wr")
        self.rail = Rail(user_input, computed_data, "rail", "r")
        self.v_c_data = {"travelled_dist": computed_data.travelled_dist, "num_cycles": input_df["num_cycles"]}
        self.D_w = input_df["D_w"]

    def compute_E_m(self):
        self.des_params["E_m"] = ((2*self.wheel_f.material["E"]*self.rail.material["E"]) / 
                                  (self.rail.material["E"] + self.wheel_f.material["E"]))

    def compute_pre_F_rd_all(self):
        self.compute_E_m()

        self.wheel_f.compute_z(self.des_params, self.D_w)
        self.wheel_r.compute_z(self.des_params, self.D_w)
        self.rail.compute_z(self.des_params, self.D_w)

        self.wheel_f.compute_f_ff(self.des_params)
        self.wheel_r.compute_f_ff(self.des_params)
        self.rail.compute_f_ff(self.des_params)

        self.wheel_f.compute_F_rd_s(self.coefficients, self.des_params, self.D_w)
        self.wheel_r.compute_F_rd_s(self.coefficients, self.des_params, self.D_w)
        self.rail.compute_F_rd_s(self.coefficients, self.des_params, self.D_w)

        self.wheel_f.compute_F_u(self.des_params, self.D_w)
        self.wheel_r.compute_F_u(self.des_params, self.D_w)
        self.rail.compute_F_u(self.des_params, self.D_w)

        self.wheel_f.compute_s_c(self.D_w, self.v_c_data["travelled_dist"])
        self.wheel_r.compute_s_c(self.D_w, self.v_c_data["travelled_dist"])
        self.rail.compute_s_c(self.v_c_data["num_cycles"])

    def compute_F_rd_all(self):
        self.wheel_f.compute_F_rd_f(self.coefficients)
        self.wheel_r.compute_F_rd_f(self.coefficients)
        self.rail.compute_F_rd_f(self.coefficients)

    def compute_proofs_all(self):
        self.wheel_f.compute_proofs()
        self.wheel_r.compute_proofs()
        self.rail.compute_proofs()

    # def compute_min_d(self):
    #     min_d_r_s = self.rail.compute_min_d_s()
    #     min_d_r_f = self.rail.compute_min_d_f()
    #     min_d_w_s = self.wheel.compute_min_d_s()
    #     min_d_w_f = self.wheel.compute_min_d_f()
    #     self.wheel.min_d = max(min_d_r_s, min_d_r_f, min_d_w_s, min_d_w_f)

    # def compute_condition_fullfilment(self):
    #     self.wheel.fullfilment_fatigue_strength = True if self.wheel.F_sd_f <= self.wheel.F_rd_f else False
    #     self.wheel.fullfilment_static_strength = True if self.wheel.F_sd_s <= self.wheel.F_rd_s else False
    #     self.rail.fullfilment_fatigue_strength = True if self.rail.F_sd_f <= self.rail.F_rd_f else False
    #     self.rail.fullfilment_static_strength = True if self.rail.F_sd_s <= self.rail.F_rd_s() else False


class Part():

    def __init__(self, user_input, computed_data, part_type, part):
        self.material = user_input.parameters.materials[part_type]
        self.geometry = user_input.parameters.geometries[part_type]
        self.factors = {"f_f2": 1,
                        "f_f3": user_input.parameters.data["f_f3"].to_numpy(),
                        "f_f4": user_input.parameters.data["f_f4"].to_numpy(),
                        "f_ff": None}
        self.F_rd = {"F_rd_s": None, "F_rd_f": pd.DataFrame(), "F_u": None}
        self.F_sd = computed_data.load_collective[part]["f_sd_f"]
        self.proofs = {"static": None, "fatigue": pd.DataFrame()}
        self.load_collective = computed_data.load_collective[part]
        self.z = None

    def compute_z(self, design_param, D_w):
        point = design_param["contact"] == "point"
        line = design_param["contact"] == "line"
        self.z = np.zeros(len(line))
        self.z[np.where(line)[0]] = self.compute_z_ml(design_param, D_w, np.where(line)[0])
        self.z[np.where(point)[0]] = self.compute_z_mp(design_param, D_w, np.where(point)[0])

    def compute_z_ml(self, design_param, D_w, idx):

        z_ml = (0.5 * (self.F_sd[idx] * math.pi * D_w[idx] * (1 - self.material["v"][idx] ** 2)
                       / (design_param["b"][idx] * design_param["E_m"][idx]))
                ** (1/2))
        return z_ml

    def compute_z_mp(self, design_param, D_w, idx):
        z_mp = (0.68 * (self.F_sd[idx] / design_param["E_m"][idx]
                        * ((1 - self.material["v"][idx] ** 2) 
                           / (2 / D_w[idx] + 1 / self.geometry["r_k"][idx]))) 
                ** (1/3))
        return z_mp

    def compute_f_ff(self, design_params):
        self.factors["f_f1"] = np.ones(len(design_params["b"]))
        idx = np.where(design_params["b"] == self.geometry["b"])[0]
        self.factors["f_f1"][idx] = design_params["f_1"][idx]
        self.factors["f_ff"] = self.factors["f_f1"] * self.factors["f_f2"] * self.factors["f_f3"] * self.factors["f_f4"]

    def compute_F_u(self, design_params, D_w):
        is_hardened = np.logical_and(self.material["hardened"] == 1, 
                                     np.logical_and((self.z < self.material["z"]), 
                                                    (self.material["HB"] >= 0.6 * self.material["f_y"])))
        factor = np.ones(len(is_hardened)) * (3 * self.material["HB"]) ** 2
        factor[np.where(is_hardened)[0]] = (1.8 * self.material["f_y"][np.where(is_hardened)[0]]) ** 2
        self.F_rd["F_u"] = (factor * (math.pi * D_w * design_params["b"] * (1 - self.material["v"] ** 2)) 
                            / design_params["E_m"])

    def compute_F_rd_s(self, coefficients, design_params, D_w):
        is_hardened = np.logical_and(self.material["hardened"] == 1, 
                                     np.logical_and((self.z < self.material["z"]), 
                                                    (self.material["HB"] >= 0.6 * self.material["f_y"])))
        factor = np.ones(len(is_hardened)) * 7 * self.material["HB"]
        factor[np.where(is_hardened)[0]] = 4.2 * self.material["f_y"][np.where(is_hardened)[0]]
        self.F_rd["F_rd_s"] = (((factor ** 2) / coefficients.Y_m) 
                               * ((math.pi * D_w * design_params["b"] * (1 - self.material["v"] ** 2) 
                                   * design_params["f_1"] * design_params["f_2"]) 
                                   / design_params["E_m"]))
        # self.F_rd["F_rd_s"] = ((factor ** 2) * design_params["f_1"] * design_params["f_2"] / coefficients.Y_m 
        #                        * math.pi * D_w * design_params["b"] * (1 - self.material["v"] ** 2)
        #                        / design_params["E_m"])

    def compute_F_rd_f(self, coefficients):
        self.F_rd["F_rd_f"]["preds"] = ((self.F_rd["F_u"] * self.factors["f_ff"]) 
                                        / (coefficients.Y_cf * (self.load_collective["s_c"]["preds"] ** (1/coefficients.m))))
        self.F_rd["F_rd_f"]["upper"] = ((self.F_rd["F_u"] * self.factors["f_ff"]) 
                                        / (coefficients.Y_cf * (self.load_collective["s_c"]["upper"] ** (1/coefficients.m))))

    def compute_proofs(self):
        self.proofs["static"] = self.F_sd <= self.F_rd["F_rd_s"]
        self.proofs["fatigue"]["preds"] = self.F_sd <= self.F_rd["F_rd_f"]["preds"]
        self.proofs["fatigue"]["upper"] = self.F_sd <= self.F_rd["F_rd_f"]["upper"]

    # @abc.abstractmethod
    # def compute_v_c(self):
    #     return

    # def compute_min_d_f(self, factors, coefficients, b, E_m):
    #     s_c = self.compute_s_c()
    #     if self.material.hardened == 'False':
    #         denominator = factors["f_f"]*math.pi*(3*self.material.HB)**2*b*(1-coefficients.v**2)
    #         numerator = (self.F_sd_f*coefficients.Y_cf*s_c**(1/coefficients.m)*E_m)
    #         min_d_f = numerator / denominator
    #     else:
    #         denominator = (factors["f_f"]*math.pi*(1.8*self.material.f_y)**2*b*(1-coefficients.v**2))
    #         numerator = (self.F_sd_f*coefficients.Y_cf*s_c**(1/coefficients.m)*E_m)
    #         min_d_f = numerator / denominator
    #     return min_d_f

    # def compute_min_d_s(self, factors, coefficients, b, E_m):
    #     if self.material.hardened == 'False':
    #         numerator = self.F_sd_s*coefficients.Y_m * E_m
    #         denominator = (7*self.material.HB)**2*math.pi*b*(1-coefficients.v**2)*factors["f_1"]*factors["f_2"]
    #         min_d_s = numerator / denominator
    #     else:
    #         numerator = self.F_sd_s*coefficients.Y_m*E_m
    #         denominator = (4.2*self.material.f_y)**2*math.pi*b*(1-coefficients.v**2)*factors["f_1"]*factors["f_2"]
    #         min_d_s = numerator / denominator
    #     return min_d_s


class Wheel(Part):

    def compute_v_c(self, D_w, travelled_dist):
        i_tot = travelled_dist / D_w
        self.load_collective["v_c"] = i_tot / 6.4e6

    def compute_s_c(self, D_w, travelled_dist):
        self.compute_v_c(D_w, travelled_dist)
        self.load_collective["s_c"] = pd.DataFrame()
        self.load_collective["s_c"]["preds"] = self.load_collective["k_c"]["preds"] * self.load_collective["v_c"]
        self.load_collective["s_c"]["upper"] = self.load_collective["k_c"]["upper"] * self.load_collective["v_c"]


class Rail(Part):

    def compute_v_c(self, num_cycles):
        i_tot = num_cycles * 4
        self.load_collective["v_c"] = i_tot / 6.4e6

    def compute_s_c(self, num_cycles):
        self.compute_v_c(num_cycles)
        self.load_collective["s_c"] = pd.DataFrame()
        self.load_collective["s_c"]["preds"] = self.load_collective["k_c"]["preds"] * self.load_collective["v_c"]
        self.load_collective["s_c"]["upper"] = self.load_collective["k_c"]["upper"] * self.load_collective["v_c"]
