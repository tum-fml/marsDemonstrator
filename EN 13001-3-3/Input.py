import pandas as  pd
from tkinter import *
from tkinter import filedialog
import tkinter.font as tkFont
import pandas.io.excel._xlrd as xlrd
import numpy as np

input = Tk()
input.title("MARS")
input.minsize(800,500)
#input.wm_iconbitmap('icon)

fontStyle = tkFont.Font(family="Lucida Grande", size=17)
fontStyle1 = tkFont.Font(family="Lucida Grande", size=15)
fontStyle2=tkFont.Font(family="Lucida Grande", size=12)

label_welcome =Label(input, text="Please follow the instructions below to specify the necessary parameters", font=fontStyle)
label_welcome.grid(padx=30, pady=10)




text_instructions="""
                       To enter the necessary parameters successfully,
                       please upload the Excel-file using the button below (open file) """

label_instructions=Label(input,text=text_instructions, font=fontStyle2, justify="left")
label_instructions.place(x=10, y=70)




#filedialog
#input.opendialog=filedialog.askopenfilename(initialdir="/C", title= "Choose the Excel-file", filetypes=('Excel-files','*.xlsx'))
def UploadAction():
    global y
    filename = filedialog.askopenfilename()
    selected= Label(input, text='Selected: ').place(x=125, y=200)
    print('Selected:', filename)
    with open(filename, 'r') as f:
      y = f.read()

    d=xlrd.open_workbook(filename) 
    sheet=d.sheet_by_index(0) 
        
    

openfile=Label(input, text="Upload the Excel-file containing the parameters:", font=fontStyle2)
buttonfile=Button(input,text="Open file", command=UploadAction)
openfile.place(x=100, y=150)
buttonfile.place(x=450 ,y= 150)





#dropdownmenus
clicked= StringVar()
clicked.set("Default")

dropdownmenu_text1= Label(input,text="choose a wheel-material:",font=fontStyle2).place(x=100 ,y=250)
dropdownmenu_wheel= OptionMenu(input, clicked, "GE 300","EN-GJS 600-3","EN-GJS-700-2","25CrMo4","34CrMo4","42CrMo4","33NiCrMoV14-5").place(x=300,y=250)


clicked1= StringVar()
clicked1.set("Default")

dropdownmenu_text2= Label(input,text="choose a rail-material:",font=fontStyle2).place(x=100, y=300)
dropdownmenu_rail= OptionMenu(input, clicked1, "42CrMo4", "S235","S275","S355","S690Q","C35E","C55","R260Mn").place(x=300,y=300)






input.mainloop()



