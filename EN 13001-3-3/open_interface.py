import tkinter.font as tkFont
# from tkinter import * implizit --> nicht gut
from tkinter import (Button, IntVar, Label, OptionMenu,  # explizit --> besser
                     Radiobutton, StringVar, Tk, filedialog)
# import tkinter as tk # alternative; im Code dann tk.Button etc.
from Computation_classes_new import User_input
from Main_functions import main_computation
from Standard_materials import materials
import webbrowser


def build_graphical_interface():

    # init input object
    user_input = User_input()

    '''# functions dropdown auswahl speichern (chosen dictionary)
    def update_dropdown_values(dropdown):
        chosen = {"wheel": {}, "rail": {}}
        chosen["wheel"]["material"] = dropdown["wheel"]["material"].get()
        chosen["wheel"]["hardened"] = dropdown["wheel"]["hardened"].get()
        chosen["rail"]["material"] = dropdown["rail"]["material"].get()
        chosen["rail"]["hardened"] = dropdown["rail"]["hardened"].get()
        return chosen'''

    def read_input_file():
        filename = filedialog.askopenfilename()
        Label(interface, text=f"Selected: {filename}", font=fontStyle2, fg="blue").place(x=300, y=250)
        user_input.read_data(filename)
        user_input.rearrange_data()

    def start_computation():
        mode = mode_value.get()
        chosen = update_dropdown_values(dropdown)
        if user_input.loaded:
            main_computation(mode, chosen, user_input)
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

    # radiobuttons for choosing computation mode
    text_mode1 = "Mode 1: checking fulfillment of safety conditions by entry of all parameters"
    text_mode2 = "Mode 2: checking the optimal diameter of the wheel while fulfillment of safety conditions by entry of all other parameters"
    text_instructions = """To enter the necessary parameters successfully, please follow the necessary instructions:
                            
                            1-download the excel-file and save it on your machine.
                            2-enter your parameters in the excel-table und save the changes.
                            3-reupload the excel-file using the button (open file)."""
    mode_value = IntVar()
    Label(interface, text="Please choose the desired mode", font=fontStyle2).place(x=10, y=80)
    Radiobutton(interface, text=text_mode1, variable=mode_value, value=1, font=fontStyle2).place(x=40, y=100)  # hier bitte den Code so anpassen, dass ein Modus vorausgewählt ist
    Radiobutton(interface, text=text_mode2, variable=mode_value, value=2, font=fontStyle2).place(x=40, y=130)
    Label(interface, text=text_instructions, font=fontStyle2, anchor="w").place(x=10, y=210)

    def callback():
        webbrowser.open_new(link_excel)
    link_excel = "https://sheet.zoho.com/sheet/officeapi/v1/24736d1736c762408e06de5f7f52bf322b508d86d5ec36cd896047f333601f424e47719c6df6d4c8fe06fe0a723cfe6e10fa2a0673a6b8b7b012c011b86ce7e7"
    Label(interface, text= "To download the excel-file, click on the button:", font = fontStyle2).place(x=10, y=350)
    Button(interface, text="download file", font=fontStyle2, command=callback).place(x=400, y=350)
    #command= callback(link_excel)

    # fields for uploading excel file
    Label(interface, text="Upload the Excel-file:", font=fontStyle2).place(x=10, y=400)
    Button(interface, text="Open file", command=read_input_file, font=fontStyle2).place(x=200, y=400)

    '''# dropdown menus wheel and rail material
    dropdown = {part: {attr: StringVar(value="Default") for attr in ["material", "hardened"]} for part in ["wheel", "rail"]}
    # wheel
    Label(interface, text="choose a wheel-material:", font=fontStyle2).place(x=10, y=360)
    OptionMenu(interface, dropdown["wheel"]["material"], *[*materials["wheel"].keys()]).place(x=250, y=360)
    Label(interface, text="Hardened:", font=fontStyle2).place(x=400, y=360)
    OptionMenu(interface, dropdown["wheel"]["hardened"], "True", "False").place(x=500, y=360)

    # rail
    Label(interface, text="choose a rail-material:", font=fontStyle2).place(x=10, y=400)
    OptionMenu(interface, dropdown["rail"]["material"], *[*materials["rail"].keys()]).place(x=250, y=400)
    Label(interface, text="Hardened:", font=fontStyle2).place(x=400, y=400)
    OptionMenu(interface, dropdown["rail"]["hardened"], "True", "False").place(x=500, y=400)
    '''

    # start button
    Button(interface, text="Start", font=fontStyle1, width=40, command=start_computation).place(x=300, y=500)
    return interface


if __name__ == "__main__":
    mars_interface = build_graphical_interface()
    mars_interface.mainloop()
