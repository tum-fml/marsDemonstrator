import math
from collections import namedtuple
import numpy as np
import pandas as pd
from .user_input import EN_input
from .predictions import LoadCollectivePrediction
# import abc

# fixed coefficients
Coefficients = namedtuple("Coefficients", ["Y_m", "Y_cf", "m", "Y_p"])


class Computation():
    """Class for doing all computations
    """
    # functions
    def __init__(self):
        self.des_params = None
        self.coefficients = self.coefficients = Coefficients(1.1, 1.1, 10/3, 1)
        self.wheel_f = None
        self.wheel_r = None
        self.rail = None 
        self.D_w = None
        self.v_c_data = None

    def load_data(self, user_input: EN_input, predicted_data: LoadCollectivePrediction):
        # data frame with data for en computation
        input_df = user_input.parameters.gen_params

        # design parameters for en computation
        self.des_params = pd.DataFrame({"b": input_df["b_min"],
                                        "f_1": input_df["f_1"],
                                        "f_2": input_df["f_2"],
                                        "w": input_df["w"],
                                        "r_k": input_df["r_k"],
                                        "contact": input_df["contact"]})
        
        # wheels and rail as attributes
        self.wheel_f = Wheel(user_input, predicted_data, "wheel", "wf")
        self.wheel_r = Wheel(user_input, predicted_data, "wheel", "wr")
        self.rail = Rail(user_input, predicted_data, "rail", "r")

        # data for computing v_c
        self.v_c_data = {"travelled_dist": predicted_data.travelled_dist, "num_cycles_wheel": input_df["num_cycles_wheel"], "num_cycles_rail": input_df["num_cycles_rail"]}

        # wheel diameter as extra attribute because of its importance
        self.D_w = user_input.parameters.geometries["wheel"]["D"]

    def compute_E_m(self):
        self.des_params["E_m"] = ((2*self.wheel_f.material["E"]*self.rail.material["E"]) / 
                                  (self.rail.material["E"] + self.wheel_f.material["E"]))

    def compute_pre_F_rd_all(self):
        self.compute_E_m()

        # compute z for wheels and rail
        self.wheel_f.compute_z(self.des_params, self.D_w)
        self.wheel_r.compute_z(self.des_params, self.D_w)
        self.rail.compute_z(self.des_params, self.D_w)

        # compute f_ff for wheels and rail
        self.wheel_f.compute_f_ff(self.des_params)
        self.wheel_r.compute_f_ff(self.des_params)
        self.rail.compute_f_ff(self.des_params)

        # compute F_rd for static proof for wheels and rail
        self.wheel_f.compute_F_rd_s(self.coefficients, self.des_params, self.D_w)
        self.wheel_r.compute_F_rd_s(self.coefficients, self.des_params, self.D_w)
        self.rail.compute_F_rd_s(self.coefficients, self.des_params, self.D_w)

        # compute F_u for F_rd_f for wheels and rail
        self.wheel_f.compute_F_u(self.des_params, self.D_w)
        self.wheel_r.compute_F_u(self.des_params, self.D_w)
        self.rail.compute_F_u(self.des_params, self.D_w)

        # compute s_c for wheels and rail
        self.wheel_f.compute_s_c(self.D_w, self.v_c_data["travelled_dist"])
        self.wheel_r.compute_s_c(self.D_w, self.v_c_data["travelled_dist"])
        self.rail.compute_s_c(self.v_c_data["num_cycles_rail"])

    # finish computing F_rd_f for wheels and rail
    def compute_F_rd_all(self):
        self.wheel_f.compute_F_rd_f(self.coefficients)
        self.wheel_r.compute_F_rd_f(self.coefficients)
        self.rail.compute_F_rd_f(self.coefficients)

    # compute all proofs
    def compute_proofs_all(self):
        self.wheel_f.compute_proofs()
        self.wheel_r.compute_proofs()
        self.rail.compute_proofs()

    # prepare results for output
    def load_results_all(self):
        self.wheel_f.load_results()
        self.wheel_r.load_results()
        self.rail.load_results()

    # def compute_min_d(self):
    #     min_d_r_s = self.rail.compute_min_d_s()
    #     min_d_r_f = self.rail.compute_min_d_f()
    #     min_d_w_s = self.wheel.compute_min_d_s()
    #     min_d_w_f = self.wheel.compute_min_d_f()
    #     self.wheel.min_d = max(min_d_r_s, min_d_r_f, min_d_w_s, min_d_w_f)


class Part():

    """Parent class for wheel and rail

    Attributes:
    -----------
    
    material: DataFrame
        material parameters of rail / wheel

    geometry: DataFrame
        geometry parameters of rail / wheel

    factors: Dict
        Factors needed to compute F_rd_f

    F_rd: Dict
        F_rd_s, F_rd_f, F_u

    F_sd:
        F_sd_f and F_sd_s are the same

    proofs:
        Results of static and fatigue proof

    load_collective: Dict of DataFrames
        Contains k_c (pred and upper confidence) and f_sd_f

    z:
        Computed z

    results: Dict
        Results for output file
    """    

    def __init__(self, user_input, predicted_data, part_type, part):

        # load materials and geometries 
        self.material = user_input.parameters.materials[part_type]
        self.geometry = user_input.parameters.geometries[part_type]

        # factors for computing F_rd_f
        self.factors = {"f_f2": 1,
                        "f_f3": user_input.parameters.gen_params["f_f3"].to_numpy(),
                        "f_f4": user_input.parameters.gen_params["f_f4"].to_numpy(),
                        "f_ff": None}

        # dictionary for F_rd_s and F_rd_f (pred and upper)
        self.F_rd = {"F_rd_s": None, "F_rd_f": pd.DataFrame(), "F_u": None}

        # parse F_sd for static and fatigue proof
        self.F_sd = predicted_data.load_collective[part]["f_sd_f"]

        # dictionary for proor results
        self.proofs = {"static": None, "fatigue": pd.DataFrame()}

        # load collective data (k_c and v_c) for computing F_rd_f
        self.load_collective = predicted_data.load_collective[part]
        self.z = None
        self.results = {}

    def compute_z(self, design_param, D_w):

        # get configurations for point and line contact
        point = design_param["contact"] == "point"
        line = design_param["contact"] == "line"
        self.z = np.zeros(len(line))

        # compute z
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
                           / (2 / D_w[idx] + 1 / design_param["r_k"][idx]))) 
                ** (1/3))
        return z_mp

    def compute_f_ff(self, design_params):
        self.factors["f_f1"] = np.ones(len(design_params["b"]))

        # set f_f1 to f_1 for each run where current part has b_min, otherwise 1
        idx = np.where(design_params["b"] == self.geometry["b"])[0]
        self.factors["f_f1"][idx] = design_params["f_1"][idx]

        # compute f_ff
        self.factors["f_ff"] = self.factors["f_f1"] * self.factors["f_f2"] * self.factors["f_f3"] * self.factors["f_f4"]

    def compute_F_u(self, design_params, D_w):

        # condition for when to use formula for hardned materials
        is_hardened = np.logical_and(self.material["hardened"] == 1, 
                                     np.logical_and((self.z < self.material["z"]), 
                                                    (self.material["HB"] >= 0.6 * self.material["f_y"])))
        
        # compute pre factor and F_u
        factor = np.ones(len(is_hardened)) * (3 * self.material["HB"]) ** 2
        factor[np.where(is_hardened)[0]] = (1.8 * self.material["f_y"][np.where(is_hardened)[0]]) ** 2
        self.F_rd["F_u"] = (factor * (math.pi * D_w * design_params["b"] * (1 - self.material["v"] ** 2)) 
                            / design_params["E_m"])

    def compute_F_rd_s(self, coefficients, design_params, D_w):

        # condition for when to use formula for hardned materials
        is_hardened = np.logical_and(self.material["hardened"] == 1, 
                                     np.logical_and((self.z < self.material["z"]), 
                                                    (self.material["HB"] >= 0.6 * self.material["f_y"])))

        # compute pre factor and F_u
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

    def load_results(self):
        self.results["static"] = pd.DataFrame({
            "F_sd_s": self.F_sd,
            "F_rd_s": self.F_rd["F_rd_s"],
            "Fulfilled": self.proofs["static"]
        })

        self.results["fatigue"] = {"prediction": {}, "upper_confidence": {}}
        self.results["fatigue"] = pd.DataFrame({
            "Bemessungskontaktkraft-F_sd_f[kN]": self.F_sd / 1000,
            "Bezugskontaktkraft-F_u": self.F_rd["F_u"] / 1000,
            "Rollkontakte-v_c": self.load_collective["v_c"],
            "Kontaktkraftkollektivbeiwert-k_c_pred": self.load_collective["k_c"]["preds"],
            "Kontaktverlaufsparameter-s_c_pred": self.load_collective["s_c"]["preds"],
            "F_rd_f_pred": self.F_rd["F_rd_f"]["preds"],
            "Fulfilled_pred": self.proofs["fatigue"]["preds"],
            "k_c_upper": self.load_collective["k_c"]["upper"],
            "s_c_upper": self.load_collective["s_c"]["upper"],
            "F_rd_f_upper": self.F_rd["F_rd_f"]["upper"],
            "Fulfilled_upper": self.proofs["fatigue"]["preds"]
        })

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
