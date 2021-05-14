import math
from collections import namedtuple
from typing import Dict, Union

import numpy as np
import pandas as pd

from .load_collective import LoadCollectivePrediction
from .mars_input import MARSInput

# import abc

# fixed coefficients
Coefficients = namedtuple("Coefficients", ["Y_m", "Y_cf", "m", "Y_p"])


class ENComputation():
    """Class for doing all computations
    """
    # functions

    def __init__(self) -> None:
        self.des_params: pd.DataFrame
        self.coefficients = Coefficients(1.1, 1.1, 10/3, 1)
        # self.wheel_f = None
        self.wheel_f: Wheel
        self.wheel_r: Wheel
        self.rail: Rail
        self.D_w: pd.DataFrame
        self.v_c_data: Dict[str, np.array]

    def load_data(self, user_input: MARSInput, predicted_data: LoadCollectivePrediction) -> None:
        # data frame with data for en computation
        input_df = user_input.parameters.gen_params
        gp_input = user_input.gp_input.raw

        # design parameters for en computation
        self.des_params = pd.DataFrame({"b": pd.to_numeric(input_df["b_min"]),
                                        "f_1": pd.to_numeric(input_df["f_1"]),
                                        "f_2": pd.to_numeric(input_df["f_2"]),
                                        "w": pd.to_numeric(input_df["w"]),
                                        "r_k": pd.to_numeric(input_df["r_k"]),
                                        "contact": input_df["contact"]})

        # wheels and rail as attributes
        self.wheel_f = Wheel(user_input, predicted_data, "wheel", "wf")
        self.wheel_r = Wheel(user_input, predicted_data, "wheel", "wr")
        self.rail = Rail(user_input, predicted_data, "rail", "r")

        # data for computing v_c
        self.v_c_data = {"travelled_dist": pd.to_numeric(predicted_data.travelled_dist), 
                         "num_cycles_wheel": pd.to_numeric(gp_input["num_cycles_wheel"]), 
                         "num_cycles_rail": pd.to_numeric(gp_input["num_cycles_rail"])}

        # wheel diameter as extra attribute because of its importance
        self.D_w = user_input.parameters.geometries["wheel"]["D"]

    def compute_E_m(self) -> None:
        self.des_params["E_m"] = ((2*self.wheel_f.material["E"]*self.rail.material["E"]) / 
                                  (self.rail.material["E"] + self.wheel_f.material["E"]))

    def compute_pre_F_rd_all(self) -> None:
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
    def compute_F_rd_all(self) -> None:
        self.wheel_f.compute_F_rd_f(self.coefficients)
        self.wheel_r.compute_F_rd_f(self.coefficients)
        self.rail.compute_F_rd_f(self.coefficients)

    # compute all proofs
    def compute_proofs_all(self) -> None:
        self.wheel_f.compute_proofs()
        self.wheel_r.compute_proofs()
        self.rail.compute_proofs()

    # prepare results for output
    def load_results_all(self) -> None:
        self.wheel_f.load_results()
        self.wheel_r.load_results()
        self.rail.load_results()


class Part(): # pylint: disable=too-many-instance-attributes

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
        Contains k_c (pred and upper confidence), f_sd_f and f_sd_f

    z:
        Computed z

    results: Dict
        Results for output file
    """    

    def __init__(self, user_input: MARSInput, predicted_data: LoadCollectivePrediction, part_type: str, part: str) -> None:

        # load materials and geometries 
        self.material = user_input.parameters.materials[part_type]
        self.geometry = user_input.parameters.geometries[part_type]

        # factors for computing F_rd_f
        self.factors = {"f_f2": 1,
                        "f_f3": pd.to_numeric(user_input.parameters.gen_params["f_f3"]).to_numpy(),
                        "f_f4": pd.to_numeric(user_input.parameters.gen_params["f_f4"]).to_numpy(),
                        "f_ff": pd.Series()}

        # dictionary for F_rd_s and F_rd_f (pred and upper)
        self.F_rd: Dict[str, Union[pd.Series, pd.DataFrame]] = {"F_rd_s": pd.Series(), "F_rd_f": pd.DataFrame(), "F_u": pd.Series()}

        # parse F_sd for static and fatigue proof
        self.F_sd_f = pd.to_numeric(predicted_data.load_collective[part]["f_sd_f"])
        self.F_sd_s = pd.to_numeric(predicted_data.load_collective[part]["f_sd_s"])

        # dictionary for proor results
        self.proofs: Dict[str, Union[pd.Series, pd.DataFrame]] = {"static": pd.Series(), "fatigue": pd.DataFrame()}

        # load collective data (k_c and v_c) for computing F_rd_f
        self.load_collective = predicted_data.load_collective[part]
        self.z: pd.DataFrame
        self.results: Dict[str, pd.DataFrame] = {}

        # load user defined v_c
        self.load_collective["user_v_c"] = user_input.parameters.gen_params["v_c_w"] if "w" in part else user_input.parameters.gen_params["v_c_r"]

        # multiply k_c times dynamic factor
        self.load_collective["k_c"]["preds"] = self.load_collective["k_c"]["preds"] * user_input.parameters.gen_params["phi"]
        self.load_collective["k_c"]["upper"] = self.load_collective["k_c"]["upper"] * user_input.parameters.gen_params["phi"]

    def compute_z(self, design_param: pd.DataFrame, D_w: pd.Series) -> None:

        # get configurations for point and line contact
        point = design_param["contact"] == "point"
        line = design_param["contact"] == "line"
        self.z = np.zeros(len(line))

        # compute z
        self.z[np.where(line)[0]] = self.compute_z_ml(design_param, D_w, np.where(line)[0])
        self.z[np.where(point)[0]] = self.compute_z_mp(design_param, D_w, np.where(point)[0])

    def compute_z_ml(self, design_param: pd.DataFrame, D_w: pd.Series, idx: np.array) -> pd.Series:

        z_ml = (0.5 * (self.F_sd_f[idx] * math.pi * D_w[idx] * (1 - self.material["v"][idx] ** 2)
                       / (design_param["b"][idx] * design_param["E_m"][idx]))
                ** (1/2))
        return z_ml

    def compute_z_mp(self, design_param: pd.DataFrame, D_w: pd.Series, idx: np.array) -> pd.Series:
        z_mp = (0.68 * (self.F_sd_f[idx] / design_param["E_m"][idx]
                        * ((1 - self.material["v"][idx] ** 2) 
                           / (2 / D_w[idx] + 1 / design_param["r_k"][idx]))) 
                ** (1/3))
        return z_mp

    def compute_f_ff(self, design_params: pd.DataFrame) -> None:
        self.factors["f_f1"] = np.ones(len(design_params["b"]))

        # set f_f1 to f_1 for each run where current part has b_min, otherwise 1
        idx = np.where(design_params["b"] == self.geometry["b"])[0]
        self.factors["f_f1"][idx] = design_params["f_1"][idx]

        # compute f_ff
        self.factors["f_ff"] = self.factors["f_f1"] * self.factors["f_f2"] * self.factors["f_f3"] * self.factors["f_f4"]

    def compute_F_u(self, design_params: pd.DataFrame, D_w: pd.Series) -> None:

        # condition for when to use formula for hardned materials
        is_hardened = np.logical_and(self.material["hardened"] == 1, 
                                     np.logical_and((self.z < self.material["z"]), 
                                                    (self.material["HB"] >= 0.6 * self.material["f_y"])))

        # compute pre factor and F_u
        factor = np.ones(len(is_hardened)) * (3 * self.material["HB"]) ** 2
        factor[np.where(is_hardened)[0]] = (1.8 * self.material["f_y"][np.where(is_hardened)[0]]) ** 2
        self.F_rd["F_u"] = (factor * (math.pi * D_w * design_params["b"] * (1 - self.material["v"] ** 2)) 
                            / design_params["E_m"])

    def compute_F_rd_s(self, coefficients: Coefficients, design_params: pd.DataFrame, D_w: pd.Series) -> None:

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

    def compute_F_rd_f(self, coefficients: Coefficients):
        self.F_rd["F_rd_f"]["preds"] = ((self.F_rd["F_u"] * self.factors["f_ff"]) 
                                        / (coefficients.Y_cf * (self.load_collective["s_c"]["preds"] ** (1/coefficients.m))))
        self.F_rd["F_rd_f"]["upper"] = ((self.F_rd["F_u"] * self.factors["f_ff"]) 
                                        / (coefficients.Y_cf * (self.load_collective["s_c"]["upper"] ** (1/coefficients.m))))

    def compute_proofs(self):
        self.proofs["static"] = self.F_sd_s <= self.F_rd["F_rd_s"]
        self.proofs["fatigue"]["preds"] = self.F_sd_f <= self.F_rd["F_rd_f"]["preds"]
        self.proofs["fatigue"]["upper"] = self.F_sd_f <= self.F_rd["F_rd_f"]["upper"]

    def load_results(self):
        self.results["static"] = pd.DataFrame({
            "Design-Contact-Force-F_sd_s [kN]": self.F_sd_s / 1000,
            "Limit-Design-Contact-Force-Static-F_rd_s [kN]": self.F_rd["F_rd_s"] / 1000,
            "Condition-Fullfilled": self.proofs["static"]
        })

        self.results["fatigue"] = pd.DataFrame({
            "Design-Contact-Force-F_sd_f [kN]": self.F_sd_f / 1000,
            "Reference-Contact-Force-F_u [kN]": self.F_rd["F_u"] / 1000,
            "Relative-Total-Number-of-Rolling-Contacts-v_c": self.load_collective["v_c"],
            "Contact-Force-Spectrum-Factor-k_c-Prediction": self.load_collective["k_c"]["preds"],
            "Contact-Force-History-Parameter-s_c_Prediction": self.load_collective["s_c"]["preds"],
            "Limit-Design-Contact-Force-Fatigue-F_rd_f-Prediction [kN]": self.F_rd["F_rd_f"]["preds"] / 1000,
            "Condition-Fullfilled-Prediction": self.proofs["fatigue"]["preds"],
            "Contact-Force-Spectrum-Parameter-k_c-Upper-Confidence-Interval": self.load_collective["k_c"]["upper"],
            "Contact-Force-History-Parameter-s_c_Upper-Confidence-Interval": self.load_collective["s_c"]["upper"],
            "Limit-Force-F_rd_f-Prediction-Upper-Confidence-Interval [kN]": self.F_rd["F_rd_f"]["upper"] / 1000,
            "Condition-Fullfilled-Upper-Confidence_Interval": self.proofs["fatigue"]["preds"]
        })


class Wheel(Part):

    def compute_v_c(self, D_w: pd.Series, travelled_dist: np.array) -> None:
        i_tot = travelled_dist / (D_w * math.pi / 1000)
        self.load_collective["v_c"] = i_tot / 6.4e6

        # load user v_c
        self.load_collective["v_c"][self.load_collective["user_v_c"] != 0] = self.load_collective["user_v_c"][self.load_collective["user_v_c"] != 0]

    def compute_s_c(self, D_w: pd.Series, travelled_dist: np.array) -> None:
        self.compute_v_c(D_w, travelled_dist)
        self.load_collective["s_c"] = pd.DataFrame()
        self.load_collective["s_c"]["preds"] = self.load_collective["k_c"]["preds"] * self.load_collective["v_c"]
        self.load_collective["s_c"]["upper"] = self.load_collective["k_c"]["upper"] * self.load_collective["v_c"]


class Rail(Part):

    def compute_v_c(self, num_cycles: pd.Series) -> None:
        i_tot = num_cycles * 4
        self.load_collective["v_c"] = i_tot / 6.4e6

        # load user v_c
        self.load_collective["v_c"][self.load_collective["user_v_c"] != 0] = self.load_collective["user_v_c"][self.load_collective["user_v_c"] != 0].copy()

    def compute_s_c(self, num_cycles: pd.Series) -> None:
        self.compute_v_c(num_cycles)
        self.load_collective["s_c"] = pd.DataFrame()
        self.load_collective["s_c"]["preds"] = self.load_collective["k_c"]["preds"] * self.load_collective["v_c"]
        self.load_collective["s_c"]["upper"] = self.load_collective["k_c"]["upper"] * self.load_collective["v_c"]
