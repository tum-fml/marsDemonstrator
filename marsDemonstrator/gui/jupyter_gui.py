# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# import designMethods.en_13001_3_3 as en
# from output import create_output_file
import itertools
import os
import pathlib
from typing import Optional

import ipywidgets as widgets
from IPython.display import FileLink, display
from marsDemonstrator.gui.main_functions import Main_application

# %%
# !pip install voila
# !jupyter serverextension enable voila --sys-prefix


# %%
class MARSGui():

    def __init__(self):
        self.fatal_error = None
        self.main_application = Main_application()

        self.input_file = FileLink("./tests/input_file/inputparameters.xlsx", result_html_prefix="Click here to download example input file: ")

        # uploader for input
        uploader_label = widgets.Label("Upload input file:  ")
        self.uploader = widgets.FileUpload(accept=".xlsx", multiple=False)
        self.uploader_box = widgets.HBox([uploader_label, self.uploader])

        # dropdown for computation mode
        label_mode = widgets.Label("Computation Mode:  ")
        drop_mode = widgets.Dropdown(options=["proof", "min_diameter"], value="proof")
        self.mode_box = widgets.HBox([label_mode, drop_mode])

        # dropdown for configuration
        label_config = widgets.Label("SC Configuration:  ")
        self.drop_config = widgets.Dropdown(options=["1 Mast", "2 Masts"], value="1 Mast")

        # button for updating configuration
        btn_update_config = widgets.Button(description="Update Configuration")
        btn_update_config.layout.width = "200px"
        btn_update_config.on_click(self.init_gps)
        self.config_box = widgets.HBox([label_config, self.drop_config, btn_update_config])

        # button to start computation
        self.btn_start = widgets.Button(description="Start computation")
        self.btn_start.on_click(self.start_computation)

        # output widget to display output file
        self.out_file = widgets.Output()

        # output widget to write error reports
        self.out_errors = widgets.Output()

        # output widget to display progress
        self.out_information = widgets.Output()

    def show(self) -> None:
        # display(widgets.Label("MARS Demonstrator"))
        display(self.input_file)
        gui = widgets.VBox([self.config_box, self.uploader_box, self.btn_start, self.out_information, self.out_file, self.out_errors])
        display(gui)

    def read_input(self) -> Optional[bool]:
        self.main_application.input_file_path = pathlib.Path("./input.xlsx")
        with open(self.main_application.input_file_path, "w+b") as i:
            i.write(self.uploader.data[-1])

        # read temp file and delete after
        self.fatal_error = None
        self.fatal_error = self.main_application.read_input_file(self.main_application.input_file_path)
        # self.uploader._counter = 0
        self.uploader.value.clear()
        self.uploader._counter = 0 # pylint: disable=protected-access
        if self.fatal_error:
            self.out_errors.clear_output()
            with self.out_errors:
                print("Fatal error in input file")
                print(self.fatal_error)
            return True
        return None

    def init_gps(self, change) -> None: # pylint: disable=unused-argument
        self.out_information.clear_output()
        configs = {"1 Mast": "m1", "2 Masts": "m2"}
        with self.out_information:
            print("Initializing GPs: this may take up to 30 seconds")

        # initialize prediction class
        # en_13001.computed = en.Computed_data()

        # get current config (1 mast or 2 mast)
        self.main_application.input.config = configs[self.drop_config.value]

        self.main_application.init_gps()

        # en_13001["input"].config_loaded = True
        # en_13001.input.config_loaded = True
        self.out_information.clear_output()
        with self.out_information:
            print("Initialized GPs")

    def start_computation(self, change) -> None: # pylint: disable=unused-argument
        self.out_information.clear_output()
        self.out_errors.clear_output()
        self.out_file.clear_output()
        # if there were never inputs loaded throw error message 
        if self.main_application.input_file_loaded is None or self.fatal_error:
            if self.uploader._counter == 0: # pylint: disable=protected-access
                with self.out_information:
                    print("Please upload an excel file")
                return

        # if there is a new upload file load its content and do make new computation
        if self.uploader._counter > 0: # pylint: disable=protected-access

            try:
                self.read_input()

                os.remove(self.main_application.input_file_path)
                if self.fatal_error:
                    return
            except Exception as e:
                with self.out_errors:
                    print("Invald input file. Unknown error")
                    print(str(e))
                    print("Please re-download input file")
                    self.uploader._counter = 0 # pylint: disable=protected-access
                    self.uploader.value.clear()
                return
        try:
            # if gps for configuration were not loaded yet load them
            if self.main_application.config_loaded is None:
                self.init_gps(None)
            with self.out_information:
                print("Start Computation") 

            self.main_application.run_computation_and_create_output(1)
            with self.out_information:
                print("Finished computation")

            # create output file
            local_file = FileLink(f"./{self.main_application.outname.name}", result_html_prefix="Click here to download results: ")

            with self.out_file:
                display(local_file)
                # display(btn_delete_output)
            self.write_error_reports()
        except Exception as e:
            with self.out_errors:
                print("Unknown error! Please report")
                print(str(e))

    def write_error_reports(self) -> None:
        with self.out_errors:
            for error in list(itertools.chain(*self.main_application.input.error_report)):
                print(error)


# %%
# gui = MARSGui()
# gui.show()


# %%
