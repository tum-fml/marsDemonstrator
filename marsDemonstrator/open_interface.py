import tkinter.font as tkFont
# from tkinter import * implizit --> nicht gut
from tkinter import (Button,  Label, OptionMenu,  # explizit --> besser
                     StringVar, Tk, filedialog)
# import tkinter as tk # alternative; im Code dann tk.Button etc.
from designMethods.en_13001_3_3 import User_input
from designMethods.en_13001_3_3 import Computed_data
from designMethods.en_13001_3_3 import Computation

def build_graphical_interface():
    direction = 1
    # init input object
    en_13001_input = User_input()
    en_13001_computed = Computed_data()

    def read_input_file():
        filename = filedialog.askopenfilename()
        Label(interface, text=f"Selected: {filename}", font=fontStyle2, fg="blue").place(x=300, y=250)
        en_13001_input.load_gp_input(filename, "configuration", "m1")
        en_13001_input.load_parameter_input(filename, "Input_variables")
        en_13001_input.load_material_input(filename, "rail_materials", "wheel_materials")
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
        if en_13001_input.config_loaded is None:
            init_gps()
        if en_13001_input.parameters.loaded:
            en_13001_computed.predict_kc(en_13001_input.gp_input.norm)
            en_13001_computed.compute_F_sd_f_all(en_13001_input.gp_input.raw, en_13001_input.config, direction)
            en_13001_computed.predict_travelled_dist(en_13001_input.parameters.data)
            en_computation = Computation(en_13001_input, en_13001_computed)
            en_computation.compute_pre_F_rd_all()
            en_computation.compute_F_rd_all()
        else:
            print("Please upload an excel file")
            Label(interface, text="Please upload an excel file", font=fontStyle2, fg="red").place(x=100, y=280)

    # init tk inter
    interface = Tk()
    interface.title("MARS")
    interface.minsize(1100, 650)

    # define font styles
    fontStyle = tkFont.Font(family="Lucida Grande", size=17)
    fontStyle1 = tkFont.Font(family="Lucida Grande", size=15)
    fontStyle2 = tkFont.Font(family="Lucida Grande", size=12)

    # header
    Label(interface, text="WELCOME TO MARS", font=fontStyle).grid(padx=30, pady=10)

    # fields for uploading excel file
    Label(interface, text="Upload the Excel-file:", font=fontStyle2).place(x=10, y=400)
    Button(interface, text="Open file", command=read_input_file, font=fontStyle2).place(x=200, y=400)

    # dropdown for mast configurateion
    Label(interface, text="choose mast configuration:", font=fontStyle2).place(x=10, y=360)
    dropdown_config = StringVar(value="m1")
    OptionMenu(interface, dropdown_config, "m1", "m2").place(x=250, y=360)
    Button(interface, text="Update configuration", command=init_gps, font=fontStyle2).place(x=100, y=400)

    # dropdown for computation mode
    Label(interface, text="Please choose the desired mode", font=fontStyle2).place(x=10, y=80)
    dropdown_mode = StringVar(value="proof")
    OptionMenu(interface, dropdown_mode, "proof", "min_diameter").place(x=40, y=100)

    # start button
    Button(interface, text="Start", font=fontStyle1, width=40, command=start_computation).place(x=300, y=500)
    return interface


if __name__ == "__main__":
    mars_interface = build_graphical_interface()
    mars_interface.mainloop()
