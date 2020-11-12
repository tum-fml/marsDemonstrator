import pandas as  pd
from tkinter import *
from tkinter import filedialog
import tkinter.font as tkFont
import pandas.io.excel._xlrd as xlrd
import numpy as np



input = Tk()
input.title("MARS")
input.minsize(1000,500)

#input.wm_iconbitmap('icon)

fontStyle = tkFont.Font(family="Lucida Grande", size=17)
fontStyle1 = tkFont.Font(family="Lucida Grande", size=15)
fontStyle2=tkFont.Font(family="Lucida Grande", size=12)

label_welcome =Label(input, text="WELCOME TO MARS", font=fontStyle)
label_welcome.grid(padx=30, pady=10)

def confirm_mode():
  mode=v.get()
  
  

#radiobutton to choose mode
label_choose_mode=Label(input,text='Please choose the desired mode',font=fontStyle2).place(x=10,y=80)
v=IntVar()
Radiobutton(input, text="checking fulfillment of safety conditions by entry of all parameters ", variable=v, value=1,font=fontStyle2).place(x=40,y=100)
Radiobutton(input, text="checking the optimal diameter of the wheel while fulfillment of safety conditions by entry of all other parameters", variable=v, value=2,font=fontStyle2).place(x=40,y=130)
button_confirm=Button(input, text="confirm", command=confirm_mode, font=fontStyle2).place(x=40,y=160)

text_instructions="To enter the necessary parameters successfully, please upload the Excel-file containing the parameters using the button below (open file) "

label_instructions=Label(input,text=text_instructions, font=fontStyle2)
label_instructions.place(x=10, y=210)



def UploadAction():
    filename = filedialog.askopenfilename()
    selected= Label(input, text='Selected: '+ filename, font= fontStyle2 , fg = "blue").place(x=125, y=280)
    df = pd.read_excel (filename, index_col=None, header= None)  
    print(df)
    l=len(df.columns)
      


#user uploads excel file
openfile=Label(input, text="Upload the Excel-file:",  font=fontStyle2)
buttonfile=Button(input,text="Open file", command=UploadAction, font=fontStyle2 )
openfile.place(x=40, y=250)
buttonfile.place(x=200 ,y= 250)





#dropdownmenus wheel and rail material
clicked= StringVar()
clicked.set("Default")

dropdownmenu_text1= Label(input,text="choose a wheel-material:",font=fontStyle2).place(x=100 ,y=360)
dropdownmenu_wheel= OptionMenu(input, clicked, "GE 300","EN-GJS 600-3","EN-GJS-700-2","25CrMo4","34CrMo4","42CrMo4","33NiCrMoV14-5").place(x=300,y=360)


clicked1= StringVar()
clicked1.set("Default")

dropdownmenu_text2= Label(input,text="choose a rail-material:",font=fontStyle2).place(x=100, y=400)
dropdownmenu_rail= OptionMenu(input, clicked1, "42CrMo4", "S235","S275","S355","S690Q","C35E","C55","R260Mn").place(x=300,y=400)

def callback(*args):
    choosen_material_wheel=clicked.get()
    choosen_material_rail=clicked1.get()
    

clicked.trace("w", callback)
clicked1.trace("w",callback)





input.mainloop()

