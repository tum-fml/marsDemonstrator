import numbers
from typing import Optional, List, Tuple, Dict

import pathlib

import numpy as np
import pandas as pd

from .input_error_check import ErrorCheck, InputFileError


class RailWheelInput():

    def __init__(self) -> None:
        """Parent class for rail/wheel standard materials and geometries.
        """        
        self.wheel: pd.DataFrame
        self.rail: pd.DataFrame
        # self.loaded = None
        self.error_report: List[str] = []

    def read(self, filename: pathlib.Path, sheetname_rail: str, sheetname_wheel: str) -> None:
        # only abstract method
        self.wheel = pd.read_excel(filename, sheet_name=sheetname_wheel, index_col=0)
        self.rail = pd.read_excel(filename, sheet_name=sheetname_rail, index_col=0)

        # get rid of nan geometries
        self.wheel = self.wheel.loc[~self.wheel.index.isnull(), :]
        self.rail = self.rail.loc[~self.rail.index.isnull(), :]

        self.wheel.drop(self.wheel.index[0], inplace=True)
        self.rail.drop(self.rail.index[0], inplace=True)

        # self.loaded = True

    def get_errors(self, property_type: str) -> Tuple[List[str], List[np.array]]:
        """Performs type error checks on rail/wheel standard materials and geometries.

        Parameters
        ----------
        property_type : str
            either geometry or material

        Returns
        -------
        error_report: list 
            List of error reports. Shows which materials/geometries contain errors.
        error_idx_all: list
            List of names of faulty rail/wheel materials/geometries.
        """        

        # init error report and list of faulty materials/geometries
        error_report = []
        fault_mat_geoms_all = []

        # loop over part
        for part in ["wheel", "rail"]:

            # get copy of current table that is check: rail / wheel + material / geometry
            check_table = getattr(self, part).copy()
            current_table = check_table.copy()

            # all variables of rail / wheel material / geometry are expected to be numeric
            # check_table.loc["exp_type"] = numbers.Number

            # check for all variables if they are numeric
            for var_name in check_table.columns:
                check_table[var_name] = pd.to_numeric(check_table[var_name], errors="coerce").notnull() 
                current_table.loc[:, var_name] = pd.to_numeric(current_table[var_name], errors="coerce")  
                # check_table[var_name][:-1].isnan()          
                # check_table[var_name][:-1] = list(map(isinstance, check_table[var_name], [check_table.loc["exp_type", var_name]] * len(check_table)))[:-1]
            setattr(self, part, current_table)
            # check if there were any errors, if not function returns
            if not check_table.to_numpy().all():

                # get idx of geometry / material that has an error
                idx = np.where(check_table.to_numpy() == 0)

                # get name of faulty material or geometry and append to output list
                faulty_mat_geoms = check_table.index[idx[0]].to_list()
                fault_mat_geoms_all.append(faulty_mat_geoms[0])

                # get name of faulty variables
                error_vars = check_table.columns[idx[1]]

                # write faulty material or gemotry and their faulty variables to error report
                for faulty_mat_geom, error_var in zip(faulty_mat_geoms, error_vars):
                    error_report.append(
                        f"type error for {part} {property_type} {faulty_mat_geom}; error variable: {error_var}; expected type: number"
                    )
        return error_report, fault_mat_geoms_all

    def copy_parameters_to_gen_params(self, target_parameters: Dict[str, pd.DataFrame], gen_params: pd.DataFrame, property_names: List[str]) -> Dict[str, pd.DataFrame]:
        """Copy parameters of chosen rail / wheel materials or geometry to data frame containing material/geometry variables for all runs.

        Parameters
        ----------
        target_parameters : Dict of DataFrames
            Either material or geometry parameters for rail and wheel needed for computation.
        gen_params : DataFrame 
            Contains general parameters. Contains the name of the rail/wheel matierals or geometries.
        property_names : list of str
            Names of needed incices in gen_params. Defines whether to look for materials of geometries

        Returns
        -------
        target_parameters
        """    
        for part, param_name in zip(["wheel", "rail"], property_names):

            # table containing either standard materials of geometries for current part (rail/wheel)
            parameters_part = getattr(self, part)

            # get variables for chosen materials or geometries and reset index
            target_parameters[part] = parameters_part.loc[gen_params[param_name]]
            target_parameters[part].index = range(len(target_parameters[part]))
        return target_parameters


class StandardMaterials(RailWheelInput):

    def read(self, filename: pathlib.Path, sheetname_rail: str, sheetname_wheel: str) -> Tuple[Optional[bool], Optional[bool]]: # type: ignore
        super().read(filename, sheetname_rail, sheetname_wheel)
        expected_vars = ["hardened", "f_y", "HB", "E", "v", "z"]

        if not pd.DataFrame(expected_vars).isin(list(self.wheel.columns)).all().loc[0]:
            raise InputFileError("Broken input file: wheel material sheet has missing vars")

        if not pd.DataFrame(expected_vars).isin(list(self.rail.columns)).all().loc[0]:
            raise InputFileError("Broken input file: rail material sheet has missing vars")

        self.wheel = self.wheel.loc[:, expected_vars]
        self.rail = self.rail.loc[:, expected_vars]


class StandardGeometries(RailWheelInput):

    def read(self, filename: pathlib. Path, sheetname_rail: str, sheetname_wheel: str) -> None: # type: ignore
        super().read(filename, sheetname_rail, sheetname_wheel)

        expected_vars_wheel = ["b", "r_k", "r_3", "D"]
        expected_vars_rail = ["b", "r_k", "r_3"]

        if not pd.DataFrame(expected_vars_wheel).isin(list(self.wheel.columns)).all().loc[0]:
            raise InputFileError("Broken input file: wheel geometry sheet has missing vars")

        if not pd.DataFrame(expected_vars_rail).isin(list(self.rail.columns)).all().loc[0]:
            raise InputFileError("Broken input file: rail geometry sheet has missing vars")

        self.wheel = self.wheel.loc[:, expected_vars_wheel]
        self.rail = self.rail.loc[:, expected_vars_rail]


class EN13001Input():
    """Class that contains standard inputs for en computation.

    Attributes:
    ---------------
    gen_params: DataFrame
        General parameters needed for computation for computation.

    gen_params_out: DataFrame
        Copy of gen_params before it gets modified. This will be printed back to output file.

    var_names: list
        Names of Variables in gen_params_out for output.

    materials: Dict of Data Frames
        Data Frames that contain variables of rail / wheel materials for each run.

    geometries: Dict of Data Frames
        Data Frames that contain variables of rail / wheel geometries for each run.

    error_check: ErrorCheck
        Error check object for performing type and value checks on gen_params.

    """

    def __init__(self) -> None:
        # general parameters for computation
        self.gen_params: pd.DataFrame
        self.gen_params_out: pd.DataFrame

        # if parameters have been loaded already
        # self.loaded: Optional[bool]

        # variable names for output
        self.var_names: List[str]

        # material and geometry variables for computation
        self.materials = {"wheel": pd.DataFrame(), "rail": pd.DataFrame()}
        self.geometries = {"wheel": pd.DataFrame(), "rail": pd.DataFrame()}

        # type and value check for gen_params
        self.error_check = ErrorCheck(self.value_check_fn, {"value": "expected value from: ", "type": "expected type: "})

    def read(self, input_df: pd.DataFrame, index_name: str) -> None:

        # read gen params from input data frame
        self.gen_params = input_df.loc[index_name, :]

        # removes rows with duplicate indicies, in case sheet has errors
        self.gen_params = self.gen_params[~self.gen_params.index.duplicated(keep='first')]
        self.var_names = list(self.gen_params.index)

        # self.loaded = True

    def rearrange(self) -> None:

        # set first column to index and drop column with output var names
        self.gen_params.index = self.gen_params.iloc[:, 0]
        self.gen_params.drop(self.gen_params.columns[0], axis=1, inplace=True)

        # transpose dataframe and reset index
        self.gen_params = self.gen_params.transpose()
        self.gen_params.index = np.arange(0, len(self.gen_params))

        # create copy of dataframe for output and set headers to var_names for user
        self.gen_params_out = self.gen_params.copy()
        self.gen_params_out.columns = self.var_names

    def get_material_geometry_error_runs(self, error_configs: List[str], wheel_field: str, rail_field: str) -> List[np.array]:
        """Checks which runs have a rail/wheel material or geometry that contained an error, and returns their config number.

        Parameters
        ----------
        error_configs : list
            Contains names of rail/wheel materials or geometries that contain error.
        wheel_field : str
            [Specifies whether to look for wheel geometry or wheel material in gen params.
        rail_field : str
            Specifies whether to look for rail geometry or rail material in gem params.

        Returns
        -------
        list
            inicies of runs that have a rail/wheel material or geometry that contained an error
        """
        if error_configs:
            idx = np.where(np.logical_or((self.gen_params[wheel_field].isin(error_configs)), (self.gen_params[rail_field].isin(error_configs))))
            return idx[0]
        return []

    def create_type_check_data(self) -> Tuple[pd.DataFrame, int]:

        # create data frame for type check and get number of runs
        type_data = self.gen_params.copy()
        num_runs = len(type_data)

        # expected type of most variables is numeric
        type_data.loc["exp", :] = numbers.Number
        type_data.loc["exp_out", :] = "number"

        # rail/wheel materials and geometries are expected to be strings
        type_data.loc["exp", ["material_wheel", "material_rail", "wheel_geometry", "rail_geometry"]] = str
        type_data.loc["exp_out", ["material_wheel", "material_rail", "wheel_geometry", "rail_geometry"]] = "string"
        return type_data, num_runs

    def create_value_check_data(self, materials_all: StandardMaterials, geometries_all: StandardGeometries) -> pd.DataFrame:

        # create data frame for value check, only rail/wheel materials and geometries have expected values
        value_data = self.gen_params.loc[:, ["material_wheel", "material_rail", "wheel_geometry", "rail_geometry"]].copy()

        # initialize row for expected values
        value_data.loc["exp", :] = 0

        # expected values come from data frames containing the standard materials and geometries
        value_data.at["exp", "wheel_geometry"] = list(geometries_all.wheel.index)
        value_data.at["exp", "rail_geometry"] = list(geometries_all.rail.index)
        value_data.at["exp", "material_wheel"] = list(materials_all.wheel.index)
        value_data.at["exp", "material_rail"] = list(materials_all.rail.index)
        value_data.loc["exp_out", :] = value_data.loc["exp", :]
        return value_data

    def parse_check_data(self, materials_all: StandardMaterials, geometries_all: StandardGeometries) -> None:

        # parse data for value and type checks to error check attribute
        self.error_check.load_type_data(self.create_type_check_data())
        self.error_check.load_value_data(self.create_value_check_data(materials_all, geometries_all))

    @staticmethod
    def value_check_fn(value_data: pd.DataFrame, num_run: int) -> pd.DataFrame:
        """value check: checks if the values of rail/wheel geometries and materials come from list of possible values

        Parameters
        ----------
        value_data : DataFrame
            Contains the gen_params data that have expected value and their expected values.
        num_run : int
            Number of computation runs. Needed for indexing

        Returns
        -------
        value_data: DataFrame
            True for conig/param configuration where exp. values are met, False else.
        """        
        for var_name in value_data.columns:
            value_data[var_name][:num_run] = value_data[var_name][:num_run].isin(value_data.loc["exp", var_name])
        return value_data

    def compute_f_f3(self) -> None:

        # compute f_f3 depending on alpha
        self.gen_params["f_f3"] = (0.005 / self.gen_params["alpha"]) ** (1 / 3)
        self.gen_params.loc[np.where(self.gen_params["alpha"] < 0.005)[0], "f_f3"] = 1

    def compute_contact_and_f_1(self) -> None:

        """Computes following paramters:

            b_min
            r_k
            f_1
        """

        # get b_min from wheel an rail b
        b = np.vstack((self.geometries["wheel"]["b"], self.geometries["rail"]["b"]))
        self.gen_params["b_min"] = np.min(b, axis=0)

        # compute w 
        computed_w = (abs(self.geometries["wheel"]["b"] - self.geometries["rail"]["b"])) / 2
        cond = (self.gen_params["w"] == 0)
        self.gen_params.loc[cond, "w"][cond] = computed_w[cond]

        # coerce w to numbers
        self.gen_params.loc[:, "w"] = pd.to_numeric(self.gen_params["w"])

        # find r_k --> either wheel or rail r_k should be zero
        r_k = np.vstack((self.geometries["wheel"]["r_k"], self.geometries["rail"]["r_k"]))
        self.gen_params["r_k"] = np.max(r_k, axis=0)

        # get r_3 of part that has min b
        r_3 = np.vstack((self.geometries["wheel"]["r_3"], self.geometries["rail"]["r_3"]))
        b_min_idx = np.argmin(b, axis=0)
        r_3_b_min = r_3[b_min_idx, np.arange(len(self.gen_params))]

        # determine contact type for each run, if both r_k = 0  or line condition fullfilled --> line
        self.gen_params.loc[:, "contact"] = "point"
        line_condition = np.logical_or((self.gen_params["r_k"] <= 0), (self.gen_params["r_k"] > 200 * self.gen_params["b_min"]))
        self.gen_params.loc[np.where(line_condition)[0], "contact"] = "line"

        # compute f_1 for each configuration that has line contact, f_1 for point contact = 1
        is_line = np.logical_and(self.gen_params["contact"] == "line", self.gen_params["w"] > 0)
        self.gen_params["f_1"] = np.ones(len(self.gen_params))

        is_line_1 = np.logical_and(is_line, r_3_b_min / self.gen_params["w"] <= 0.1)
        is_line_2 = np.logical_and(is_line, 
                                   np.logical_and(r_3_b_min / self.gen_params["w"] > 0.1, r_3_b_min / self.gen_params["w"] <= 0.8))
        self.gen_params.loc[is_line_1, "f_1"] = 0.85
        self.gen_params.loc[is_line_2, "f_1"] = (0.58 + 0.15 * (r_3_b_min / self.gen_params["w"])) / 0.7
