import pathlib

import joblib
import numpy as np
import pandas as pd
import torch

mypath = pathlib.Path(__file__).parent.absolute()


class User_input():

    def __init__(self):
        self.gp_input = GPInput()
        self.parameters = ParameterInput()
        self.materials = MaterialInput()
        self.config = None
        self.config_loaded = None

    def load_gp_input(self, filename, sheetname, config):
        self.gp_input.read(filename, sheetname)
        self.gp_input.rearange(config)

    def load_parameter_input(self, filename, sheetname):
        self.parameters.read(filename, sheetname)
        self.parameters.rearange()

    def load_material_input(self, filename, sheetname_rail, sheetname_wheel):
        self.materials.read(filename, sheetname_rail, sheetname_wheel)
        self.materials.rearange()

    def set_materials_and_geometry(self):
        self.parameters.set_material_parameters(self.materials)
        self.parameters.set_geometry_parameters()


class GPInput():

    def __init__(self):
        self.raw = None
        self.norm = None
        self.loaded = None

    def read(self, filename, sheetname):
        self.raw = pd.read_excel(filename, sheet_name=sheetname, index_col=None, header=None)
        self.loaded = True

    def rearange(self, config):
        self.raw.drop(self.raw.columns[0], axis=1, inplace=True)
        self.raw = self.raw.transpose()
        self.raw.columns = self.raw.iloc[0]
        self.raw.drop(self.raw.index[0], inplace=True)
        self.raw.index = np.arange(0, len(self.raw))

        input_scale = joblib.load(mypath / "input_scale.pkl")
        input_scale = input_scale[config]

        self.raw["m_m_a"] = self.raw["m_m_a"] - self.raw["m_m_h"] * (self.raw["c_h"] - 0.8)
        self.raw["t_m_a"] = self.raw["t_m_a"] - self.raw["t_m_l"] * self.raw["t_wd"]
        crane_direction = 1
        if config == "m1":
            # if gp_input["m_cg_x"] > 0.5:
            #     gp_input["l_cg_x"] = 1 - gp_input["l_cg_x"]
            #     crane_direction = -1
            self.raw["l_cg_x"] = (self.raw["l_cg_x"] - self.raw["m_cg_x"]) * self.raw["t_wd"]
        self.norm = self.raw.copy()
        self.norm = self.norm.to_numpy()
        for idx, row in enumerate(self.norm):
            self.norm[idx, :] = (row - input_scale["min"]) / input_scale["diff"]

        self.norm = torch.from_numpy(np.vstack(self.norm[:, :]).astype(np.float64)).double()

        return crane_direction


class ParameterInput():

    def __init__(self) -> None:
        self.data = None
        self.loaded = None
        self.materials = {"wheel": None, "rail": None}
        self.geometries = {"wheel": None, "rail": None}

    def read(self, filename, sheetname):
        self.data = pd.read_excel(filename, sheet_name=sheetname, index_col=None, header=None)
        self.loaded = True

    def rearange(self):
        self.data = self.data.transpose()
        self.data.columns = self.data.iloc[0]
        self.data = self.data.drop(self.data.index[0])
        self.data.index = np.arange(0, len(self.data))

    def set_material_parameters(self, materials_all):
        for part, param_name in zip(["wheel", "rail"], ["material_wheel", "material_rail"]):
            materials_part = getattr(materials_all, part)
            f_y = np.zeros(len(self.data))
            hb = f_y.copy()
            e = f_y.copy()
            v = f_y.copy()
            z = f_y.copy()
            hardened = f_y.copy()
            for idx, material in enumerate(self.data[param_name]):
                f_y[idx] = materials_part[material]["f_y"]
                hb[idx] = materials_part[material]["HB"]
                e[idx] = materials_part[material]["E"]
                v[idx] = materials_part[material]["v"]
                z[idx] = materials_part[material]["z"]
                hardened[idx] = materials_part[material]["hardened"]

            self.materials[part] = {"f_y": f_y,
                                    "HB": hb,
                                    "E": e,
                                    "v": v,
                                    "hardened": hardened,
                                    "z": z}

    def compute_f_f3(self):
        self.data["f_f3"] = (0.005 / self.data["alpha"]) ** (1 / 3)
        self.data.loc[np.where(self.data["alpha"] < 0.005)[0], "f_f3"] = 1

    def compute_contact_and_f_1(self):
        b = np.vstack((self.data["b_w"], self.data["b_r"]))
        r_k = np.vstack((self.data["r_k_w"], self.data["r_k_r"]))
        r_3 = np.vstack((self.data["r_3_w"], self.data["r_3_r"]))
        self.data["b_min"] = np.min(b, axis=0)
        b_min_idx = np.argmin(b, axis=0)
        self.data["r_k_b_min"] = r_k[b_min_idx, np.arange(len(self.data))]
        r_3_b_min = r_3[b_min_idx, np.arange(len(self.data))]
        is_point = self.data["contact"] == "point"
        line_condition = self.data["r_k_b_min"] > 200 * self.data["b_min"]
        self.data.loc[np.where(np.logical_and(is_point, line_condition))[0], "contact"] = "line"
        is_line = self.data["contact"] == "line"
        line_idx_1 = np.where(np.logical_and(is_line, r_3_b_min / self.data["w"] <= 0.1))[0]
        line_idx_2 = np.where(np.logical_and(is_line, 
                                             np.logical_and(r_3_b_min / self.data["w"] > 0.1, r_3_b_min / self.data["w"] <= 0.8)))[0]
        self.data["f_1"] = np.ones(len(self.data))
        self.data.loc[line_idx_1, "f_1"] = 0.85
        self.data.loc[line_idx_2, "f_1"] = (0.58 + 0.15 * (r_3_b_min / self.data["w"])) / 0.7

    def set_geometry_parameters(self):
        self.geometries["wheel"] = {"b": self.data["b_w"],
                                    "r_k": self.data["r_k_w"],
                                    "r_3": self.data["r_3_w"]}
        self.geometries["rail"] = {"b": self.data["b_r"],
                                   "r_k": self.data["r_k_r"],
                                   "r_3": self.data["r_3_r"]}


class MaterialInput():

    def __init__(self):
        self.wheel = None
        self.rail = None
        self.loaded = None

    def read(self, filename, sheetname_rail, sheetname_wheel):
        self.wheel = pd.read_excel(filename, sheet_name=sheetname_wheel, index_col=None, 
                                   header=None)
        self.rail = pd.read_excel(filename, sheet_name=sheetname_rail, index_col=None,  
                                  header=None)
        self.loaded = True

    def rearange(self):
        self.wheel.columns = self.wheel.iloc[1]
        wheel = self.wheel.drop(self.wheel.index[0:2])
        wheel.index = np.arange(0, len(wheel))
        self.rail.columns = self.rail.iloc[1]
        rail = self.rail.drop(self.rail.index[0:2])
        rail.index = np.arange(0, len(rail))

        self.wheel = {name: wheel.iloc[idx] for idx, name in enumerate(wheel.name)}
        self.rail = {name: rail.iloc[idx] for idx, name in enumerate(rail.name)}
