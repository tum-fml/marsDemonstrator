import pathlib
from typing import Optional, Dict
from ..designMethods.en_13001_3_3 import Computation, LoadCollectivePrediction, EN_input
from .output import ResultWriter # , create_output_file

none_or_bool = Optional[bool]


class Main_application():

    def __init__(self) -> None:
        self.input = EN_input()
        self.prediction = LoadCollectivePrediction()
        self.computation = Computation()
        self.input_file_path: pathlib.Path
        self.is_loaded: Dict[str, none_or_bool] = {
            "config": None, "input_file": None, "reload_file_config": None
        }
        self.num_run = 0
        self.outname: pathlib.Path

    def read_input_file(self, filename: pathlib.Path) -> Optional[str]:
        # load data for load collective prediction
        self.input.clear_inputs()
        try:
            self.input.read_input_df(filename)
            bad_file = self.input.check_input_df()
            error_msg = None

            if bad_file:
                error_msg = "broken input file: main sheet has missing vars"

            if len(self.input.input_df.columns) == 1:
                error_msg = "more than 3 empty cells in all configurations"

            if error_msg:
                return error_msg

            self.input.load_gp_input("Stacker Crane (SC) And Rack Configuration")

            # load en 13001 parameters
            self.input.load_parameter_input("EN-13001-3-3")

            # load materials
            wheel_error, rail_error = self.input.materials.read(filename, "rail_materials", "wheel_materials")

            if wheel_error:
                error_msg = "broken input file: wheel material sheet has missing vars"
            if rail_error:
                error_msg = "broken input file: rail material sheet has missing vars"
            if wheel_error and rail_error:
                error_msg = "broken input file: wheel and rail material sheets have missing vars"

            if error_msg:
                return error_msg

            # load geometries
            wheel_error, rail_error = self.input.geometries.read(filename, "rail_geometries", "wheel_geometries")

            if wheel_error:
                error_msg = "broken input file: wheel geometry sheet has missing vars"
            if rail_error:
                error_msg = "broken input file: rail geometry sheet has missing vars"
            if wheel_error and rail_error:
                error_msg = "broken input file: wheel and rail geometry sheets have missing vars"

            if error_msg:
                return error_msg

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
                return "at least one error in all configurations"

            # precompute factors and set geometriy and material parameters
            self.input.set_materials_and_geometry()
            self.input.parameters.compute_f_f3()
            self.input.parameters.compute_contact_and_f_1()
            self.is_loaded["input_file"] = True
            self.is_loaded["reload_file_config"] = True

            return None
        except ValueError as e:
            if "Worksheet" in str(e):
                return "broken input file: one or more required input sheets were missing. required sheets are: Input_variables, rail_materials, wheel_materials, wheel_geometries, rail_geometries"
            return "unknown fatal error"

    def run_computation_and_create_output(self, direction: int) -> None:
        if self.is_loaded["reload_file_config"]:
            self.num_run += 1
            self.input.recompute_gp_data(self.input.config)

            # check gp input variables for values outside expected intervals
            self.input.perform_gp_input_warning_check()

            self.prediction.clear_prediction_results()
            self.prediction.predict_kc(self.input.gp_input.norm)
            self.prediction.compute_F_sd_f_all(self.input.gp_input.raw, self.input.config, direction)
            self.prediction.predict_travelled_dist(self.input.gp_input.raw["cycle_mode"], self.input.gp_input.raw["num_cycles_wheel"], self.input.gp_input.raw["r_l"])

            # create computation instance and compute configs
            self.computation.load_data(self.input, self.prediction)
            self.computation.compute_pre_F_rd_all()
            self.computation.compute_F_rd_all()
            self.computation.compute_proofs_all()

            # reults output
            self.input.prepare_for_output()
            self.computation.load_results_all()

            # pick a filename that doesn't exist yet
            if not self.outname:
                self.outname = self.input_file_path.parent.absolute() / f"output_no{self.num_run}.xlsx"
            while self.outname.is_file():
                self.num_run += 1
                self.outname = self.input_file_path.parent.absolute() / f"output_no{self.num_run}.xlsx"

            results_writer = ResultWriter(self.computation, self.input, self.outname)
            results_writer.create_summary()
            results_writer.write()
            # create_output_file(self.computation, self.input, self.outname)
            self.is_loaded["reload_file_config"] = None

    def init_gps(self) -> None:
        self.prediction = LoadCollectivePrediction()
        direction = 1
        gp_configs = {"m1": {1: "m1l", -1: "m1r"}, "m2": {1: "m2"}}
        gp_config = gp_configs[self.input.config][direction]
        parts = ["wf", "wr", "r"]
        # self.prediction.load_gps(gp_config)
        self.prediction.get_gps_kc(gp_config, parts)
        self.is_loaded["config"] = True
        self.is_loaded["reload_file_config"] = True
