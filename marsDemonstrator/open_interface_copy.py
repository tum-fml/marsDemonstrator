import pathlib
# from tkinter import * implizit --> nicht gut
# from tkinter import (Button,  Label, OptionMenu,  # explizit --> besser
#                    StringVar, Tk, filedialog)
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog

# import tkinter as tk # alternative; im Code dann tk.Button etc.
from designMethods.en_13001_3_3 import Computation, Computed_data, EN_input
from output import create_output_file


class MarsGUI():

    def __init__(self):
        self.root = tk.Tk()
        self.direction = 1
        # init input object
        self.en_13001_input = EN_input()
        self.en_13001_computed = Computed_data()
        self.gen_vars = {"num_run": 1}
        # init tk inter

        self.root.title("MARS")
        self.root.minsize(1100, 650)

        # define font styles
        fontStyle = tkFont.Font(family="Lucida Grande", size=17)
        fontStyle1 = tkFont.Font(family="Lucida Grande", size=15)
        fontStyle2 = tkFont.Font(family="Lucida Grande", size=12)

        # def msg box
        self.gen_vars["msg"] = tk.StringVar()
        msg_box = tk.Label(self.root, textvariable=self.gen_vars["msg"], font=fontStyle2, fg="blue")
        msg_box.place(x=300, y=250)

        # header
        tk.Label(self.root, text="WELCOME TO MARS", font=fontStyle).grid(padx=30, pady=10)

        # fields for uploading excel file
        tk.Label(self.root, text="Upload the Excel-file:", font=fontStyle2).place(x=10, y=300)
        tk.Button(self.root, text="Open file", command=self.read_input_file, font=fontStyle2).place(x=200, y=300)

        # dropdown for mast configurateion
        tk.Label(self.root, text="choose mast configuration:", font=fontStyle2).place(x=10, y=360)
        self.dropdown_config = tk.StringVar(value="m1")
        tk.OptionMenu(self.root, self.dropdown_config, "m1", "m2").place(x=250, y=360)
        tk.Button(self.root, text="Update configuration", command=self.init_gps, font=fontStyle2).place(x=350, y=360)

        # dropdown for computation mode
        tk.Label(self.root, text="Please choose the desired mode:", font=fontStyle2).place(x=10, y=80)
        dropdown_mode = tk.StringVar(value="proof")
        tk.OptionMenu(self.root, dropdown_mode, "proof", "min_diameter").place(x=280, y=80)

        # start button
        tk.Button(self.root, text="Start computation", font=fontStyle1, width=40, command=self.start_computation).place(x=300, y=500)

    def read_input_file(self):
        filename = filedialog.askopenfilename()
        self.gen_vars["msg"].set(f"Selected: {filename}")
        self.gen_vars["filename"] = pathlib.Path(filename).absolute()

        # load data for load collective prediction
        self.en_13001_input.load_gp_input(self.gen_vars["filename"], "configuration")

        # load material and en 13001 parameters
        self.en_13001_input.load_material_input_check(self.gen_vars["filename"], "rail_materials", "wheel_materials")
        self.en_13001_input.load_parameter_input(self.gen_vars["filename"], "Input_variables")

        # check for input errors and drop faulty configurations
        self.en_13001_input.perform_error_checks()
        self.en_13001_input.drop_error_configs()

        # precompute factors and material parameters
        self.en_13001_input.parameters.compute_f_f3()
        self.en_13001_input.parameters.compute_contact_and_f_1()
        self.en_13001_input.set_materials_and_geometry()

    def init_gps(self):
        self.en_13001_input.config = self.dropdown_config.get()
        gp_configs = {"m1": {1: "m1l", -1: "m1r"}, "m2": {1: "m2"}}
        gp_config = gp_configs[self.en_13001_input.config][self.direction]
        parts = ["wf", "wr", "r"]
        self.en_13001_computed.get_gps_kc(gp_config, parts)
        self.en_13001_input.config_loaded = True

    def start_computation(self):

        if self.en_13001_input.parameters.loaded is None:
            self.gen_vars["msg"].set("Please upload an excel file")
            return

        if self.en_13001_input.config_loaded is None:
            self.init_gps()

        self.en_13001_input.recompute_gp_data(self.en_13001_input.config)
        self.en_13001_computed.predict_kc(self.en_13001_input.gp_input.norm)
        self.en_13001_computed.compute_F_sd_f_all(self.en_13001_input.gp_input.raw, self.en_13001_input.config, self.direction)
        self.en_13001_computed.predict_travelled_dist(self.en_13001_input.parameters.data)

        # create computation instance and compute configs
        en_computation = Computation(self.en_13001_input, self.en_13001_computed)
        en_computation.compute_pre_F_rd_all()
        en_computation.compute_F_rd_all()
        en_computation.compute_proofs_all()

        # reults output
        self.en_13001_input.prepare_for_output()
        en_computation.load_results_all()
        self.gen_vars["outname"] = self.gen_vars["filename"].parent.absolute() / f"output_no{self.gen_vars['num_run']}.xlsx"
        create_output_file(en_computation, self.en_13001_input, self.gen_vars["outname"])
        self.gen_vars["msg"].set(f"Generated output file: output_no{self.gen_vars['num_run']}.xlsx")
