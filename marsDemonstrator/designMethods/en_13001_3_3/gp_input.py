import numbers
import pathlib
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
import torch

from .input_error_check import ErrorCheck

mypath = pathlib.Path(__file__).parent.absolute()


class GPInput():
    """Class that contains input for predicting the load collectives using Gaussian Processes.

    Attributes:
    -----------
    raw: DataFrame
        Contains variables used for predicting load collective in raw form (not normalized)

    norm: DataFrame
        Contains normalized variales. This is used as input for GPs.

    var_names: list
        Names of Variables in raw_out for output.

    raw_out: DataFrame
        Data as it was provided by user, before modification. This will be printed back to the output file.

    input_scale: DataFrame
        Contains the scales for the variabels for transforming raw to norm.

    error_check: ErrorCheck
        Error check object for performing type and value checks on raw/norm.

    """

    def __init__(self) -> None:
        self.raw: pd.DataFrame
        self.norm: pd.DataFrame
        # self.loaded
        self.var_names: List[str]
        self.raw_out: pd.DataFrame
        self.input_scale: pd.DataFrame
        self.error_check = ErrorCheck(self.value_check_fn, {"value": "expected value in interval: ", "type": "expected type: "}, gp_input=True)

    def read(self, input_df, index_name):

        # read raw variables
        self.raw = input_df.loc[index_name, :]

        # removes rows with duplicate indicies, in case sheet has errors
        self.var_names = list(self.raw.index)

        # self.loaded = True

    def rearrange(self) -> None:

        # set first column to index and drop column with output var names
        self.raw.index = self.raw.iloc[:, 0]
        self.raw.drop(self.raw.columns[0], axis=1, inplace=True)

        # transpose dataframe and reset index
        self.raw = self.raw.transpose()
        self.raw.index = np.arange(0, len(self.raw))

        # create copy of dataframe for output and set headers to var_names for user
        self.raw_out = self.raw.copy()
        self.raw_out.columns = self.var_names

    def recompute(self, config: str) -> int:
        """Recompute gp input. This function computes some variables for load collective prediction based on variables given by user.
        Also normalizes gp data,

        Parameters
        ----------
        config : str
            Crane configuration. Either "m1" (1 Mast) or "m2" (2 Mast)

        Returns
        -------
        [type]
            [description]
        """        

        # load input scales
        input_scales = joblib.load(mypath / "input_scale.pkl")

        # get input scale for given configuration
        self.input_scale = input_scales[config]

        # recompute variabels "mast addition masses" and "traverse additional masses"
        # user gives total mass of traverse and mass and mass per height / length
        self.raw["m_m_a"] = self.raw["m_m_a"] - self.raw["m_m_h"] * (self.raw["c_h"] - 0.8)
        self.raw["t_m_a"] = self.raw["t_m_a"] - self.raw["t_m_l"] * self.raw["t_wd"]

        # currently only crane direction 1 i considered
        crane_direction = 1
        # if config == "m1":
        #     # if gp_input["m_cg_x"] > 0.5:
        #     #     gp_input["l_cg_x"] = 1 - gp_input["l_cg_x"]
        #     #     crane_direction = -1

        #     # if configuration is 1 Mast recompute center of gravity x for lift so that it is
        #     # represented as distance from cg x of mast
        #     self.raw["l_cg_x"] = (self.raw["l_cg_x"] - self.raw["m_cg_x"]) * self.raw["t_wd"]

        # initialize normalized gp input
        self.norm = self.raw.loc[:, ["c_h", "c_cg_z", "m_m_h", "m_cg_x", "m_m_a", "t_wd", "t_cg_x", "t_m_l",
                                     "t_m_a", "w_a", "w_s", "w_v", "l_cg_x", "l_m", "l_m_ld", "l_a", "r_l"]].copy()

        # self.raw = self.raw.loc[:, ["c_h", "c_cg_z", "m_m_h", "m_cg_x", "m_m_a", "t_wd", "t_cg_x", "t_m_l",
        #                             "t_m_a", "w_a", "w_s", "w_v", "l_cg_x", "l_m", "l_m_ld", "l_a", "r_l"]].copy()

        self.norm = self.norm.to_numpy()

        # normalize variables
        for idx, row in enumerate(self.norm):
            self.norm[idx, :] = (row - self.input_scale["min"]) / self.input_scale["diff"]

        # transform to torch tensor
        self.norm = torch.from_numpy(np.vstack(self.norm[:, :]).astype(np.float32))

        # call function to get expected values for gp input
        self.modify_input_scales()

        return crane_direction

    def modify_input_scales(self) -> None:

        # init scale data frame
        scale = pd.DataFrame()

        # last three entries are num cycles rail and wheel and cycle mode --> not in input scale 
        for idx, var_name in enumerate(self.raw.columns[:-3]):
            scale.loc[var_name, "min"] = self.input_scale["min"][idx]
            scale.loc[var_name, "diff"] = self.input_scale["diff"][idx]

        # compute max value for each variable
        scale["max"] = scale["min"] + scale["diff"]
        self.input_scale = scale

        # set interval for l_cg_x manually --> needs rework
        # l_cg_x_min = self.input_scale.loc["l_cg_x", "min"].copy()
        # l_cg_x_max = self.input_scale.loc["l_cg_x", "max"].copy()

        # self.input_scale.loc["l_cg_x", "min"] = 0.2
        # self.input_scale.loc["l_cg_x", "max"] = 0.6

        # max for rack length and empty lift mass needs to be set manually
        self.input_scale.loc["l_m", "max"] = 3000
        self.input_scale.loc["r_l", "max"] = 150

        # create max, min, and diff for num cycles and cycle mode
        self.input_scale.loc["num_cycles_wheel", "min"] = 0
        self.input_scale.loc["num_cycles_wheel", "max"] = 100000000
        self.input_scale.loc["num_cycles_rail", "min"] = 0
        self.input_scale.loc["num_cycles_rail", "max"] = 100000000
        self.input_scale.loc["cycle_mode", "min"] = 1
        self.input_scale.loc["cycle_mode", "max"] = 4

        # recompute min and max for mast and traverse additional masses --> needs to be total masses instead
        for field in ["min", "max"]:
            self.input_scale.loc["m_m_a", field] = self.input_scale.loc["m_m_a", field] + self.input_scale.loc["m_m_h", field] * (self.input_scale.loc["c_h", field] - 0.8)
            self.input_scale.loc["t_m_a", field] = self.input_scale.loc["t_m_a", field] + self.input_scale.loc["t_m_l", field] * self.input_scale.loc["t_wd", field]

        # define intervals for expected values in list [min, max]
        intervals = pd.DataFrame({"exp": (zip(self.input_scale["min"], self.input_scale["max"]))}) # expected interval
        intervals.index = self.input_scale.index

        # join intervals into input scales and set index to var_names known to user
        self.input_scale = self.input_scale.join(intervals.copy())
        self.input_scale.index = self.var_names

    def create_type_check_data(self) -> Tuple[pd.DataFrame, int]:

        # all variables are expecte to be numeric
        type_data = self.raw_out.copy()
        num_runs = len(type_data)
        type_data.loc["exp", :] = numbers.Number
        type_data.loc["exp_out", :] = "number"
        return type_data, num_runs

    def create_value_check_data(self) -> pd.DataFrame:

        # initialize table for value check --> copy of transposed raw out
        value_data = self.raw_out.transpose().copy()

        # join attribute exp (with expected intervals) and min and max for value checking into value_data table
        value_data = value_data.join(self.input_scale["exp"]).copy()
        value_data = value_data.join(self.input_scale["min"]).copy()
        value_data = value_data.join(self.input_scale["max"]).copy()
        value_data.loc[:, "exp_out"] = value_data.loc[:, "exp"]
        return value_data.transpose()

    def parse_type_check_data(self) -> None:

        # parse type check data to error check object
        self.error_check.load_type_data(self.create_type_check_data())

    def parse_value_check_data(self) -> None:

        # parse value check data to error check object
        self.error_check.load_value_data(self.create_value_check_data())

    @staticmethod
    def value_check_fn(value_check: pd.DataFrame, num_run: int) -> pd.DataFrame:
        """value check: checks if the values of gp inputs are within expected intervas

        Parameters
        ----------
        value_check : DataFrame
            Contains values of gp_input variables for each runs as well as their expected intervals.
        num_run : int
            Number of computation runs. Needed for indexing

        Returns
        -------
        value_data: DataFrame
            True for conig/param configuration where exp. values are met, False else.
        """        

        # separate gp input data from expected intervals
        value_check_data = value_check.iloc[:num_run, :].copy()
        value_check_compare = value_check.iloc[num_run:, :].copy()

        # check for each variable if they are within expected intervals
        for var_name in value_check_data.columns:
            if var_name == "Cycle Mode":
                value_check_data[var_name] = value_check_data.loc[:, var_name].isin([1, 2, 4])
                continue
            value_check_data[var_name] = np.logical_and((value_check_data[var_name] >= value_check_compare.loc["min", var_name]), 
                                                        (value_check_data[var_name] <= value_check_compare.loc["max", var_name]))

        # integrate results into initial value check table
        value_check.iloc[:num_run, :] = value_check_data
        return value_check
