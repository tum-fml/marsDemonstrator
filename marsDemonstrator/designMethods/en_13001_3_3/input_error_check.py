import numpy as np
import pandas as pd


class ErrorCheck():
    def __init__(self, fn_check_val, error_msg, gp_input=None):
        self.gp_input = gp_input
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
            if self.type_data.loc["exp", var_name] == str:
                self.type_data[var_name][:self.num_runs] = list(map(isinstance,
                                                                    self.type_data[var_name],
                                                                    [self.type_data.loc["exp", var_name]] * len(self.type_data)))[:self.num_runs]
            else:
                self.type_data[var_name][:self.num_runs] = pd.to_numeric(self.type_data[var_name][:self.num_runs], errors="coerce").notnull()

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
            idx = np.where(self.check_results[check].iloc[:self.num_runs, :].to_numpy() == 0)
            error_vars = self.check_results[check].columns[idx[1]]
            error_rows = idx[0] + 1
            error_idx.append(list(idx[0]))
            for error_var, error_row, exp in zip(error_vars, error_rows, self.check_results[check].loc["exp_out", error_vars]):
                error_report = f"{check} error in input configuration no. {error_row}; error variable: {error_var}; {self.error_msg[check]}{exp}"

                # value error for gp input is not an error but a warning
                if self.gp_input and check == "value":
                    error_report = f"warning in output configuration no. {error_row}; {error_var} value outside expected interval; expected interval: {exp}"
                error_reports.append(error_report)
        return error_reports, error_idx
