from ..designMethods.en_13001_3_3 import Computation, LoadCollectivePrediction, EN_input
from .output import create_output_file


class Main_application():

    def __init__(self):
        self.input = EN_input()
        self.prediction = LoadCollectivePrediction()
        self.computation = Computation()
        self.input_file_path = None
        self.input_file_loaded = None
        self.config_loaded = None
        self.num_run = 0
        self.outname = None
        self.new_input_file_loaded = None

    def read_input_file(self, filename):
        # load data for load collective prediction
        self.input.clear_inputs()
        bad_file = self.input.read_input_df(filename)

        if bad_file:
            return "broken input file not all required vars found"

        if len(self.input.input_df.columns) == 1:
            return "more than 3 empty cells in all configurations"
        self.input.load_gp_input("RBG-Konfiguration")

        # load material and en 13001 parameters
        self.input.load_material_input_check(filename, "rail_materials", "wheel_materials")
        self.input.load_parameter_input("General Input")

        # load rail and wheel geometries
        self.input.load_geometry_input_check(filename, "rail_geometries", "wheel_geometries")

        # check for input errors and drop faulty configurations
        self.input.perform_error_checks()
        self.input.drop_error_configs()

        if len(self.input.parameters.gen_params) == 0:
            return "at least one error in all configurations"

        # precompute factors and set geometriy and material parameters
        self.input.set_materials_and_geometry()
        self.input.parameters.compute_f_f3()
        self.input.parameters.compute_contact_and_f_1()
        self.input_file_loaded = True
        self.new_input_file_loaded = True
        return None

    def run_computation_and_create_output(self, direction):
        if self.new_input_file_loaded:
            self.num_run += 1
            self.input.recompute_gp_data(self.input.config)
            self.prediction.clear_prediction_results()
            self.prediction.predict_kc(self.input.gp_input.norm)
            self.prediction.compute_F_sd_f_all(self.input.gp_input.raw, self.input.config, direction)
            self.prediction.predict_travelled_dist(self.input.parameters.gen_params, self.input.parameters.gen_params["num_cycles_wheel"], self.input.gp_input.raw["r_l"])

            # create computation instance and compute configs
            self.computation.load_data(self.input, self.prediction)
            self.computation.compute_pre_F_rd_all()
            self.computation.compute_F_rd_all()
            self.computation.compute_proofs_all()

            # reults output
            self.input.prepare_for_output()
            self.computation.load_results_all()
            self.outname = self.input_file_path.parent.absolute() / f"output_no{self.num_run}.xlsx"
            create_output_file(self.computation, self.input, self.outname)
            self.new_input_file_loaded = None

    def init_gps(self):
        self.prediction = LoadCollectivePrediction()
        direction = 1
        gp_configs = {"m1": {1: "m1l", -1: "m1r"}, "m2": {1: "m2"}}
        gp_config = gp_configs[self.input.config][direction]
        parts = ["wf", "wr", "r"]
        # self.prediction.load_gps(gp_config)
        self.prediction.get_gps_kc(gp_config, parts)
        self.config_loaded = True

