# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import itertools
import pathlib
import pandas as pd

from marsDemonstrator.main_app import MainApplication


# %%
# read input file
main_application = MainApplication()
main_application.input_file_path = pathlib.Path.cwd().parent / "input_file" / "inputparameters.xlsx"
main_application.read_input_file(main_application.input_file_path)

# set a result file
main_application.output_file_path = pathlib.Path.cwd().parent / "test_output" / "result.xlsx"

# set configuration ["m1", "m2"]
main_application.config = "m1r"

main_application.sc_direction = 1
if "m1" in main_application.config:
    main_application.sc_direction = 1 if "l" in main_application.config else -1
    main_application.config = "m1" 

# initialize gaussian processes
main_application.init_gps()


# %%
# computation mode 1

# run computation
main_application.computation_mode_1()

# read results
results_summary = pd.read_excel(main_application.output_file_path, sheet_name="summary", header=None, index_col=[0, 1, 2])
results_detailed = pd.read_excel(main_application.output_file_path, sheet_name="results", header=None, index_col=[0, 1, 2])

# print errors
for error in list(itertools.chain(*main_application.input.error_report)):
    print(error)


# %%
# computation mode 2

# run computation
main_application.computation_mode_2()

# read results
results_summary = pd.read_excel(main_application.output_file_path, sheet_name="summary", header=None, index_col=[0, 1, 2])
results_detailed = pd.read_excel(main_application.output_file_path, sheet_name="results", header=None, index_col=[0, 1, 2])

# print errors
for error in list(itertools.chain(*main_application.input.error_report)):
    print(error)


# %%
# show result summary
results_summary


# %%
# show detailed results
results_detailed


# %%



