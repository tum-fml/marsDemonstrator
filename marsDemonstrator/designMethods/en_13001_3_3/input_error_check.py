import numpy as np
import pandas as pd


class ErrorCheck():
    def __init__(self, fn_check_val, error_msg):
        self.fn_check_val = fn_check_val
        self.check_results = {}
        self.error_msg = error_msg
        self.value_data = None
        self.type_data = None
        self.nan_data = None
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
