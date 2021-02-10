import tkinter.font as tkFont
# from tkinter import * implizit --> nicht gut
# from tkinter import (Button,  Label, OptionMenu,  # explizit --> besser
#                    StringVar, Tk, filedialog)
import tkinter as tk
from tkinter import filedialog
# import tkinter as tk # alternative; im Code dann tk.Button etc.
from designMethods.en_13001_3_3 import User_input
from designMethods.en_13001_3_3 import Computed_data
from designMethods.en_13001_3_3 import Computation
from output import create_output_file

import pathlib


def build_graphical_interface():
    direction = 1
    # init input object
    en_13001_input = User_input()
    en_13001_computed = Computed_data()
    gen_vars = {"num_run": 1}
    
    def read_input_file():
        filename = filedialog.askopenfilename()
        gen_vars["msg"].set(f"Selected: {filename}")
        gen_vars["filename"] = pathlib.Path(filename).absolute()
        en_13001_input.load_gp_input(gen_vars["filename"], "configuration", "m1")
        en_13001_input.load_material_input(gen_vars["filename"], "rail_materials", "wheel_materials")
        en_13001_input.load_parameter_input(gen_vars["filename"], "Input_variables")
        en_13001_input.prepare_for_output()
        en_13001_input.set_materials_and_geometry()
        en_13001_input.parameters.compute_f_f3()
        en_13001_input.parameters.compute_contact_and_f_1()

    def init_gps():
        config = dropdown_config.get()
        gp_configs = {"m1": {1: "m1l", -1: "m1r"}, "m2": {1: "m2"}}
        gp_config = gp_configs[config][direction]
        parts = ["wf", "wr", "r"]
        en_13001_computed.get_gps_kc(gp_config, parts)
        en_13001_input.config_loaded = True

    def start_computation():

        if en_13001_input.parameters.loaded is None:
            gen_vars["msg"].set("Please upload an excel file")
            return

        if en_13001_input.config_loaded is None:
            init_gps()

        en_13001_computed.predict_kc(en_13001_input.gp_input.norm)
        en_13001_computed.compute_F_sd_f_all(en_13001_input.gp_input.raw, en_13001_input.config, direction)
        en_13001_computed.predict_travelled_dist(en_13001_input.parameters.data)
        en_computation = Computation(en_13001_input, en_13001_computed)
        en_computation.compute_pre_F_rd_all()
        en_computation.compute_F_rd_all()
        en_computation.compute_proofs_all()
        en_computation.load_results_all()
        gen_vars["outname"] = gen_vars["filename"].parent.absolute() / f"output_no{gen_vars['num_run']}.xlsx"
        create_output_file(en_computation, en_13001_input, gen_vars["outname"])
        gen_vars["msg"].set(f"Generated output file: output_no{gen_vars['num_run']}.xlsx")

    # init tk inter
    interface = tk.Tk()
    interface.title("MARS")
    interface.minsize(1100, 650)

    # define font styles
    fontStyle = tkFont.Font(family="Lucida Grande", size=17)
    fontStyle1 = tkFont.Font(family="Lucida Grande", size=15)
    fontStyle2 = tkFont.Font(family="Lucida Grande", size=12)

    # def msg box
    gen_vars["msg"] = tk.StringVar()
    msg_box = tk.Label(interface, textvariable=gen_vars["msg"], font=fontStyle2, fg="blue")
    msg_box.place(x=300, y=250)

    # header
    tk.Label(interface, text="WELCOME TO MARS", font=fontStyle).grid(padx=30, pady=10)

    # fields for uploading excel file
    tk.Label(interface, text="Upload the Excel-file:", font=fontStyle2).place(x=10, y=300)
    tk.Button(interface, text="Open file", command=read_input_file, font=fontStyle2).place(x=200, y=300)

    # dropdown for mast configurateion
    tk.Label(interface, text="choose mast configuration:", font=fontStyle2).place(x=10, y=360)
    dropdown_config = tk.StringVar(value="m1")
    tk.OptionMenu(interface, dropdown_config, "m1", "m2").place(x=250, y=360)
    tk.Button(interface, text="Update configuration", command=init_gps, font=fontStyle2).place(x=350, y=360)

    # dropdown for computation mode
    tk.Label(interface, text="Please choose the desired mode:", font=fontStyle2).place(x=10, y=80)
    dropdown_mode = tk.StringVar(value="proof")
    tk.OptionMenu(interface, dropdown_mode, "proof", "min_diameter").place(x=280, y=80)

    # start button
    tk.Button(interface, text="Start computation", font=fontStyle1, width=40, command=start_computation).place(x=300, y=500)
    return interface


if __name__ == "__main__":
    mars_interface = build_graphical_interface()
    mars_interface.mainloop()
