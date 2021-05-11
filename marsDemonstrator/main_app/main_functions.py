import pathlib
import numpy as np
import pandas as pd
from ..designMethods.en_13001_3_3 import ENComputation, LoadCollectivePrediction, MARSInput
from .output import ResultWriter
from ..designMethods.en_13001_3_3.input_error_check import InputFileError


class MainApplication():

    def __init__(self) -> None:
        self.input = MARSInput()
        self.prediction = LoadCollectivePrediction()
        self.computation: ENComputation
        self.input_file_path: pathlib.Path
        self.output_file_path: pathlib.Path
        self.result_writer: ResultWriter
        self.sc_direction: int
        self.config: str

    def read_input_file(self, filename: pathlib.Path) -> None:
        # load data for load collective prediction
        self.input.clear_inputs()
        try:
            self.input.read_input_df(filename)
            self.input.check_input_df()

            if len(self.input.input_df.columns) == 1:
                raise InputFileError("More than 3 empty cells in all configurations")

            self.input.load_gp_input("Stacker Crane (SC) And Rack Configuration")

            # load en 13001 parameters
            self.input.load_parameter_input("EN-13001-3-3")

            # load materials
            self.input.materials.read(filename, "rail_materials", "wheel_materials")

            # load geometries
            self.input.geometries.read(filename, "rail_geometries", "wheel_geometries")

            # check materials and geometries
            self.input.geometry_and_material_error_check()

            # # load materials
            # self.input.load_material_input_check(filename, "rail_materials", "wheel_materials")

            # # load rail and wheel geometries
            # self.input.load_geometry_input_check(filename, "rail_geometries", "wheel_geometries")

            # check for input errors and drop faulty configurations
            self.input.perform_error_checks()
            self.input.drop_error_configs()

            if len(self.input.parameters.gen_params) == 0:
                raise InputFileError("At least one error in all configurations")

        except InputFileError as e:
            raise e

        except ValueError as e:
            if "Worksheet" in str(e):
                raise InputFileError("Broken input file: one or more required input sheets were missing. required sheets are: Input_variables, rail_materials, wheel_materials, wheel_geometries, rail_geometries") from e
            raise InputFileError("Unknown fatal error with input file, please redownload") from e

        except Exception as e:
            if "sheet" in str(e):
                raise InputFileError("Broken input file: one or more required input sheets were missing. required sheets are: Input_variables, rail_materials, wheel_materials, wheel_geometries, rail_geometries") from e
            raise InputFileError("Unknown fatal error with input file, please redownload") from e

    def prepare_gp_input(self):
        self.input.recompute_gp_data(self.config)

        # check gp input variables for values outside expected intervals
        self.input.perform_gp_input_warning_check()

    def run_computation(self) -> None:

        self.input.clear_computed_inputs()
        self.input.set_materials_and_geometry()
        self.input.parameters.compute_f_f3()
        self.input.parameters.compute_contact_and_f_1()

        self.prediction.clear_prediction_results()
        # assign f_sd_s
        self.prediction.load_f_sd_s(self.input.parameters.gen_params["F_sd_s_w"], self.input.parameters.gen_params["F_sd_s_r"])

        self.prediction.predict_kc(self.input.gp_input.norm)
        self.prediction.compute_F_sd_f_all(self.input.gp_input.raw, self.config, self.sc_direction)

        self.prediction.recompute_kc(self.input.parameters.gen_params["F_sd_f_w"], "wf")
        self.prediction.recompute_kc(self.input.parameters.gen_params["F_sd_f_w"], "wr")
        self.prediction.recompute_kc(self.input.parameters.gen_params["F_sd_f_r"], "r")
        self.prediction.predict_travelled_dist(self.input.gp_input.raw["cycle_mode"], self.input.gp_input.raw["num_cycles_wheel"], self.input.gp_input.raw["r_l"])

        # create computation instance and compute configs
        self.computation = ENComputation()
        self.computation.load_data(self.input, self.prediction)
        self.computation.compute_pre_F_rd_all()
        self.computation.compute_F_rd_all()
        self.computation.compute_proofs_all()

    def initialize_result_writer(self):
        # pick a filename that doesn't exist yet
        self.result_writer = ResultWriter(self.computation, self.input, self.output_file_path)
        self.result_writer.create_summary()

    def computation_mode_1(self) -> None:
        self.prepare_gp_input()
        self.run_computation()

        # reults output
        self.input.prepare_for_output()
        self.computation.load_results_all()

        self.initialize_result_writer()
        self.result_writer.write()
        # create_output_file(self.computation, self.input, self.output_file_path)

    def computation_mode_2(self) -> None:
        self.prepare_gp_input()

        # sort wheel geometries by diameter
        self.input.geometries.wheel.sort_values("D", inplace=True)
        wheel_geometries = list(self.input.geometries.wheel.index)

        proof_results = np.empty((len(wheel_geometries), len(self.input.parameters.gen_params)))
        for idx, wheel_geometry in enumerate(wheel_geometries):
            self.input.parameters.gen_params.loc[:, "wheel_geometry"] = wheel_geometry
            self.run_computation()

            # check if all proofs are fullfilled
            proof_results[idx, :] = np.logical_and.reduce((
                self.computation.wheel_f.proofs["static"], self.computation.wheel_f.proofs["fatigue"].loc[:, "preds"], 
                self.computation.wheel_r.proofs["static"], self.computation.wheel_r.proofs["fatigue"].loc[:, "preds"],
                self.computation.rail.proofs["static"], self.computation.rail.proofs["fatigue"].loc[:, "preds"]
            ))
        wheel_geometries_min_d = pd.Series(wheel_geometries)[proof_results.argmax(axis=0)]
        wheel_geometries_min_d = pd.DataFrame(wheel_geometries_min_d, columns=["Min. Wheel Geometry"])
        wheel_geometries_min_d.index = range(len(wheel_geometries_min_d))

        wheel_geometries_min_d[proof_results.sum(axis=0) < 1] = wheel_geometries[-1]
        self.input.parameters.gen_params.loc[:, "wheel_geometry"]  = list(wheel_geometries_min_d.to_numpy())
        self.run_computation()

        wheel_geometries_min_d[proof_results.sum(axis=0) < 1] = "NaN"

        # drop wheel geometry from output params
        # self.input.parameters.gen_params_out.drop(columns="wheel_geometry", inplace=True)

        # reults output
        self.input.prepare_for_output()
        self.computation.load_results_all()

        # add wheel geometry to output
        self.computation.wheel_f.results["static"] = pd.concat(
            [wheel_geometries_min_d, self.computation.wheel_f.results["static"]], axis=1
        )
        self.computation.wheel_r.results["static"] = pd.concat(
            [wheel_geometries_min_d, self.computation.wheel_r.results["static"]], axis=1
        )
        self.initialize_result_writer()

        # add wheel geometry to summary
        self.result_writer.summary["wheel_f"] = pd.concat([wheel_geometries_min_d, self.result_writer.summary["wheel_f"].T], axis=1)
        self.result_writer.summary["wheel_r"] = pd.concat([wheel_geometries_min_d, self.result_writer.summary["wheel_r"].T], axis=1)
        self.result_writer.summary["wheel_f"] = self.result_writer.summary["wheel_f"].T
        self.result_writer.summary["wheel_r"] = self.result_writer.summary["wheel_r"].T

        self.result_writer.write()
        # create_output_file(self.computation, self.input, self.output_file_path)

    def init_gps(self) -> None:
        self.prediction = LoadCollectivePrediction()
        gp_configs = {"m1": {1: "m1l", -1: "m1r"}, "m2": {1: "m2"}}
        gp_config = gp_configs[self.config][self.sc_direction]
        parts = ["wf", "wr", "r"]
        # self.prediction.load_gps(gp_config)
        self.prediction.get_gps_kc(gp_config, parts)
