
import pathlib
from itertools import chain

import pandas as pd

from .gp_input import GPInput
from .parameter_input import StandardGeometries, StandardMaterials, StandardInput

mypath = pathlib.Path(__file__).parent.absolute()


class EN_input():
    """Class that contains all input classes.

    Attributes:
    -----------
    gp_input: GPInput

    parameters: StandardInput

    materials: StandardMaterials

    geometries: Standard Geometries

    input_df: DataFrame
        Contains data for gp_input and gen_params in parameters.

    output: Dict of DataFrames
        Output versions of gp_input.raw and parameters.gen_params_raw

    config: str
        Current configuration. Either "m1" or "m2".

    config_loaded: bool
        Whether configuration has been loaded yet.

    error_configs:
        Idx of faulty configurations

    error_report:
        list of all error reports
    
    """
    def __init__(self):
        self.gp_input = GPInput()
        self.parameters = StandardInput()
        self.materials = StandardMaterials()
        self.geometries = StandardGeometries()
        self.input_df = None
        self.output = None
        self.config = None
        self.config_loaded = None
        self.error_configs = []
        self.error_report = []

    def read_input_df(self, filename):
        self.input_df = pd.read_excel(filename, sheet_name="Input_variables", index_col=[0, 1], header=None)

        # define list of expected input vars
        expected_vars = ["wheel_geometry", "rail_geometry", "alpha", "f_2", "f_f4", "material_wheel", "material_rail", "F_sd_f_w", "F_sd_f_r",
                         "num_cycles_wheel", "num_cycles_rail", "cycle_mode", "c_h", "c_cg_z", "m_m_h", "m_cg_x", "m_m_a", "t_wd", "t_cg_x", "t_m_l", "t_m_a", "w_a",
                         "w_s", "w_v", "l_cg_x", "l_m", "l_m_ld", "l_a", "r_l"]

        self.input_df = self.input_df[~self.input_df.index.duplicated(keep='first')]
        self.input_df = self.input_df[(self.input_df.iloc[:, 0].isin(expected_vars))]
        if not pd.DataFrame(expected_vars).isin(list(self.input_df.iloc[:, 0])).all().loc[0]:
            return True
        self.input_df = self.input_df.loc[:, (self.input_df.isnull().sum(axis=0) <= 3)]

        # check if there are all expected vars
        return None

    def clear_inputs(self):

        # reset
        self.gp_input = GPInput()
        self.parameters = StandardInput()
        self.materials = StandardMaterials()
        self.geometries = StandardGeometries()
        self.output = None
        self.error_configs = []
        self.error_report = []

    def load_gp_input(self, index_name):

        # load and rearrange gp input
        self.gp_input.read(self.input_df, index_name)
        self.gp_input.rearrange()

    def load_parameter_input(self, index_name):

        # load and rearrange parameters.gen_params
        self.parameters.read(self.input_df, index_name)
        self.parameters.rearrange()

    def load_material_input_check(self, filename, sheetname_rail, sheetname_wheel):

        # load standard materials and check for input errors
        self.materials.read(filename, sheetname_rail, sheetname_wheel)
        error_report, error_mats = self.materials.get_errors("material")
        self.error_report.append(error_report)

        # get configuration numbers that contain faulty materials
        self.error_configs.append(list(self.parameters.get_material_geometry_error_runs(error_mats, "material_wheel", "material_rail")))

    def load_geometry_input_check(self, filename, sheetname_rail, sheetname_wheel):

        # load standard geometries and check for input errors
        self.geometries.read(filename, sheetname_rail, sheetname_wheel)
        error_report, error_geoms = self.geometries.get_errors("geometry")
        self.error_report.append(error_report)

        # get configuration numbers that contain faulty geometries
        self.error_configs.append(list(self.parameters.get_material_geometry_error_runs(error_geoms, "wheel_geometry", "rail_geometry")))

    def perform_error_checks(self):

        # run type check on gp input and get error reports and config numbers
        self.gp_input.parse_type_check_data()
        self.gp_input.error_check.check_types()
        error_report, error_config = self.gp_input.error_check.get_error_reports()
        self.error_report.append(error_report)
        self.error_configs.append(list(chain(*error_config)))

        # run type and value check on gen_param input and get error reports and config numbers
        self.parameters.parse_check_data(self.materials, self.geometries)
        self.parameters.error_check.check_types()
        self.parameters.error_check.check_values()
        error_report, error_config = self.parameters.error_check.get_error_reports()
        self.error_report.append(error_report)
        self.error_configs.append(list(chain(*error_config)))

    def drop_error_configs(self):

        # unpack error configurations into single list
        self.error_configs = list(set(chain(*self.error_configs)))

        # drop error configurations from gp_input.raw and gen_params
        self.parameters.gen_params.drop(self.error_configs, inplace=True)
        self.parameters.gen_params.index = range(len(self.parameters.gen_params))
        self.parameters.gen_params_out.drop(self.error_configs, inplace=True)
        self.parameters.gen_params_out.index = range(len(self.parameters.gen_params))
        self.gp_input.raw.drop(self.error_configs, inplace=True)
        self.gp_input.raw.index = range(len(self.parameters.gen_params))
        self.gp_input.raw_out.drop(self.error_configs, inplace=True)
        self.gp_input.raw_out.index = range(len(self.parameters.gen_params))

        # update number of runs for value error check for gp input vars
        self.gp_input.error_check.num_runs = len(self.gp_input.raw)

    def recompute_gp_data(self, config):

        # recompute and normalize gp input
        self.gp_input.recompute(config)

    def set_materials_and_geometry(self):

        # get material and geometry parameters for each run
        self.parameters.materials = self.materials.copy_parameters_to_gen_params(self.parameters.materials, self.parameters.gen_params, ["material_wheel", "material_rail"])
        self.parameters.geometries = self.geometries.copy_parameters_to_gen_params(self.parameters.geometries, self.parameters.gen_params, ["wheel_geometry", "rail_geometry"])

    def prepare_for_output(self):

        # prepare input for printing back to output file
        conf_out = self.gp_input.raw_out.copy()
        conf_out.columns = self.gp_input.var_names
        params_out = self.parameters.gen_params_out
        params_out.columns = self.parameters.var_names
        self.output = {"parameters": params_out.transpose(),
                       "configuration": conf_out.transpose()}
