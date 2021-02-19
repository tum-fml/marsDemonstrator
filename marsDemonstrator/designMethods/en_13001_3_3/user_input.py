import numbers
import pathlib
from itertools import chain

import joblib
import numpy as np
import pandas as pd
import torch

mypath = pathlib.Path(__file__).parent.absolute()


class EN_input():

    def __init__(self):
        self.gp_input = GPInput()
        self.parameters = ParameterInput()
        self.materials = MaterialInput()
        self.output = None
        self.config = None
        self.config_loaded = None
        self.error_configs = []
        self.error_report = []

    def load_gp_input(self, filename, sheetname):
        self.gp_input.read(filename, sheetname)
        self.gp_input.rearrange()

    def load_parameter_input(self, filename, sheetname):
        self.parameters.read(filename, sheetname)
        self.parameters.rearrange()

    def load_material_input_check(self, filename, sheetname_rail, sheetname_wheel):
        self.materials.read(filename, sheetname_rail, sheetname_wheel)
        error_report, error_mats = self.materials.get_errors()
        self.error_report.append(error_report)
        self.error_configs.append(list(self.parameters.get_material_error_runs(error_mats)))

    def perform_error_checks(self):
        self.gp_input.parse_type_check_data()
        self.gp_input.error_check.check_types()
        error_report, error_config = self.gp_input.error_check.get_error_reports()
        self.error_report.append(error_report)
        self.error_configs.append(list(chain(*error_config)))

        self.parameters.parse_check_data(self.materials)
        self.parameters.error_check.check_types()
        self.parameters.error_check.check_values()
        error_report, error_config = self.parameters.error_check.get_error_reports()
        self.error_report.append(error_report)
        self.error_configs.append(list(chain(*error_config)))

    def drop_error_configs(self):
        self.error_configs = list(set(chain(*self.error_configs)))
        self.parameters.data.drop(self.error_configs, inplace=True)
        self.parameters.data.index = range(len(self.parameters.data))
        self.gp_input.raw.drop(self.error_configs, inplace=True)
        self.gp_input.raw.index = range(len(self.parameters.data))
        self.gp_input.raw_out.drop(self.error_configs, inplace=True)
        self.gp_input.raw_out.index = range(len(self.parameters.data))
        self.gp_input.error_check.num_runs = len(self.gp_input.raw)

    def recompute_gp_data(self, config):
        self.gp_input.recompute(config)

    def set_materials_and_geometry(self):
        self.parameters.set_material_parameters(self.materials)
        self.parameters.set_geometry_parameters()

    def prepare_for_output(self):
        conf_out = self.gp_input.raw_out.copy()
        conf_out.columns = self.gp_input.var_names
        self.output = {"parameters": self.parameters.data.transpose(),
                       "configuration": conf_out.transpose()}


class ErrorCheck():
    def __init__(self, fn_check_val, error_msg):
        self.fn_check_val = fn_check_val
        self.check_results = {}
        self.error_msg = error_msg
        self.value_data = None
        self.type_data = None
        self.num_runs = None

    def load_type_data(self, data_runs):
        self.type_data, self.num_runs = data_runs

    def load_value_data(self, value_data):
        self.value_data = value_data

    def check_types(self):
        for var_name in self.type_data.columns:
            self.type_data[var_name][:self.num_runs] = list(map(isinstance,
                                                                self.type_data[var_name],
                                                                [self.type_data.loc["exp", var_name]] * len(self.type_data)))[:self.num_runs]
        if not self.type_data.to_numpy().all():
            self.check_results["type"] = self.type_data

    def check_values(self):
        value_check_results = self.fn_check_val(self.value_data, self.num_runs)
        if not value_check_results.to_numpy().all():
            self.check_results["value"] = value_check_results

    def get_error_reports(self):
        error_reports = []
        error_idx = [[]]
        for check in self.check_results.keys():
            idx = np.where(self.check_results[check].iloc[:-1, :].to_numpy() == 0)
            error_vars = self.check_results[check].columns[idx[1]]
            error_rows = idx[0] + 1
            error_idx.append(list(idx[0]))
            for error_var, error_row, exp in zip(error_vars, error_rows, self.check_results[check].loc["exp_out", error_vars]):
                error_reports.append(
                    f"{check} error in configuration no. {error_row}; error variable: {error_var}; {self.error_msg[check]}{exp}"
                )
        return error_reports, error_idx


class GPInput():

    def __init__(self):
        self.raw = None
        self.norm = None
        self.loaded = None
        self.var_names = None
        self.raw_out = None
        self.input_scale = None
        self.error_check = ErrorCheck(self.value_check_fn, {"value": "expected value in interval: ", "type": "expected type: "})

    def read(self, filename, sheetname):
        self.raw = pd.read_excel(filename, sheet_name=sheetname, index_col=None, header=None)
        self.var_names = list(self.raw.loc[:, 0])
        self.loaded = True

    def rearrange(self):
        self.raw.drop(self.raw.columns[0], axis=1, inplace=True)
        self.raw = self.raw.transpose()
        self.raw.columns = self.raw.iloc[0]
        self.raw.drop(self.raw.index[0], inplace=True)
        self.raw.index = np.arange(0, len(self.raw))
        self.raw_out = self.raw.copy()
        self.raw_out.columns = self.var_names

    def recompute(self, config):
        input_scales = joblib.load(mypath / "input_scale.pkl")
        self.input_scale = input_scales[config]

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
            self.norm[idx, :] = (row - self.input_scale["min"]) / self.input_scale["diff"]

        self.norm = torch.from_numpy(np.vstack(self.norm[:, :]).astype(np.float64)).double()
        self.modify_input_scales()

        return crane_direction

    def modify_input_scales(self):
        scale = pd.DataFrame()
        for idx, var_name in enumerate(self.raw.columns):
            scale.loc[var_name, "min"] = self.input_scale["min"][idx]
            scale.loc[var_name, "diff"] = self.input_scale["diff"][idx]
        scale["max"] = scale["min"] + scale["diff"]
        self.input_scale = scale
        self.input_scale.loc["l_cg_x", "min"] = 0.2
        self.input_scale.loc["l_cg_x", "max"] = 0.6
        for field in ["min", "max"]:
            self.input_scale.loc["m_m_a", field] = self.input_scale.loc["m_m_a", field] + self.input_scale.loc["m_m_h", field] * (self.input_scale.loc["c_h", field] - 0.8)
            self.input_scale.loc["t_m_a", field] = self.input_scale.loc["t_m_a", field] + self.input_scale.loc["t_m_l", field] * self.input_scale.loc["t_wd", field]
        intervals = pd.DataFrame({"exp": (zip(self.input_scale["min"], self.input_scale["max"]))}) # expected interval
        intervals.index = self.input_scale.index
        self.input_scale = self.input_scale.join(intervals.copy())
        self.input_scale.index = self.var_names

    def create_type_check_data(self):
        type_data = self.raw_out.copy()
        num_runs = len(type_data)
        type_data.loc["exp", :] = numbers.Number
        type_data.loc["exp_out", :] = "number"
        return type_data, num_runs

    def create_value_check_data(self):
        value_data = self.raw_out.transpose().copy()
        value_data = value_data.join(self.input_scale["exp"]).copy()
        value_data = value_data.join(self.input_scale["min"]).copy()
        value_data = value_data.join(self.input_scale["max"]).copy()
        value_data.loc[:, "exp_out"] = value_data.loc[:, "exp"]
        return value_data.transpose()

    def parse_type_check_data(self):
        self.error_check.load_type_data(self.create_type_check_data())

    def parse_value_check_data(self):
        self.error_check.load_value_data(self.create_value_check_data())

    @staticmethod
    def value_check_fn(value_check, num_run):
        vaule_check_data = value_check.iloc[:num_run, :].copy()
        value_check_compare = value_check.iloc[num_run:, :].copy()
        for var_name in vaule_check_data.columns:
            vaule_check_data[var_name] = np.logical_and((vaule_check_data[var_name] >= value_check_compare.loc["min", var_name]), 
                                                        (vaule_check_data[var_name] <= value_check_compare.loc["max", var_name]))
        value_check.iloc[:num_run, :] = vaule_check_data
        return value_check


class ParameterInput():

    def __init__(self) -> None:
        self.data = None
        self.loaded = None
        self.materials = {"wheel": None, "rail": None}
        self.geometries = {"wheel": None, "rail": None}
        self.error_check = ErrorCheck(self.value_check_fn, {"value": "expected value from: ", "type": "expected type: "})

    def read(self, filename, sheetname):
        self.data = pd.read_excel(filename, sheet_name=sheetname, index_col=None, header=None)
        self.loaded = True

    def rearrange(self):
        self.data = self.data.transpose()
        self.data.columns = self.data.iloc[0]
        self.data = self.data.drop(self.data.index[0])
        self.data.index = np.arange(0, len(self.data))

    def create_type_check_data(self):
        type_data = self.data.copy()
        num_runs = len(type_data)
        type_data.loc["exp", :] = numbers.Number
        type_data.loc["exp_out", :] = "number"
        type_data.loc["exp", ["contact", "material_wheel", "material_rail"]] = str
        type_data.loc["exp_out", ["contact", "material_wheel", "material_rail"]] = "string"
        return type_data, num_runs

    def create_value_check_data(self, materials_all):
        value_data = self.data.loc[:, ["material_wheel", "material_rail", "contact"]].copy()
        value_data.loc["exp", :] = 0
        value_data.at["exp", "contact"] = ["point", "line"]
        value_data.at["exp", "material_wheel"] = list(materials_all.wheel.index)
        value_data.at["exp", "material_rail"] = list(materials_all.rail.index)
        value_data.loc["exp_out", :] = value_data.loc["exp", :]
        return value_data

    def parse_check_data(self, materials_all):
        self.error_check.load_type_data(self.create_type_check_data())
        self.error_check.load_value_data(self.create_value_check_data(materials_all))

    @staticmethod
    def value_check_fn(value_data, num_run):
        for var_name in value_data.columns:
            value_data[var_name][:num_run] = value_data[var_name][:num_run] .isin(value_data.loc["exp", var_name])
        return value_data

    def set_material_parameters(self, materials_all):
        for part, param_name in zip(["wheel", "rail"], ["material_wheel", "material_rail"]):
            materials_part = getattr(materials_all, part)
            self.materials[part] = materials_part.loc[self.data[param_name]]
            self.materials[part].index = range(len(self.materials[part]))

    def get_material_error_runs(self, error_mats):
        if error_mats:
            idx = np.where(np.logical_or((self.data["material_wheel"].isin(error_mats)), (self.data["material_rail"].isin(error_mats))))
            return idx[0]
        return []

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
        self.geometries["wheel"] = pd.DataFrame({"b": self.data["b_w"],
                                                 "r_k": self.data["r_k_w"],
                                                 "r_3": self.data["r_3_w"]})
        self.geometries["rail"] = pd.DataFrame({"b": self.data["b_r"],
                                                "r_k": self.data["r_k_r"],
                                                "r_3": self.data["r_3_r"]})


class MaterialInput():

    def __init__(self):
        self.wheel = None
        self.rail = None
        self.loaded = None
        self.error_report = []

    def read(self, filename, sheetname_rail, sheetname_wheel):
        self.wheel = pd.read_excel(filename, sheet_name = sheetname_wheel, index_col = 0)
        self.rail = pd.read_excel(filename, sheet_name = sheetname_rail, index_col = 0)
        self.wheel.drop(columns = ["norm", "material_number"], inplace = True)
        self.rail.drop(columns = ["norm", "material_number"], inplace = True)
        self.loaded = True

    def get_errors(self):
        error_report = []
        error_mats_all = []
        for part in ["wheel", "rail"]:
            check = getattr(self, part).copy()
            check.loc["exp_type"] = numbers.Number
            for var_name in check.columns:             
                check[var_name][:-1] = list(map(isinstance, check[var_name], [check.loc["exp_type", var_name]] * len(check)))[:-1]

            if not check.iloc[:-1, :].to_numpy().all():
                idx = np.where(check.to_numpy() == 0)
                error_mats = check.index[idx[0]].to_list()
                error_mats_all.append(error_mats[0])
                error_vars = check.columns[idx[1]]
                for error_mat, error_var in zip(error_mats, error_vars):
                    error_report.append(
                        f"type error for {part} material {error_mat}; error variable: {error_var}; expected type: number"
                    )
        return error_report, error_mats_all
