import pandas as  pd
from tkinter import *
from tkinter import Tk, filedialog
import tkinter.font as tkFont
import pandas.io.excel._xlrd as xlrd
import numpy as np
from Anhang import *
from Berechnung import RBG
df=None


input = Tk()
input.title("MARS")
input.minsize(1100,650)

#input.wm_iconbitmap('icon)

fontStyle = tkFont.Font(family="Lucida Grande", size=17)
fontStyle1 = tkFont.Font(family="Lucida Grande", size=15)
fontStyle2=tkFont.Font(family="Lucida Grande", size=12)

label_welcome =Label(input, text="WELCOME TO MARS", font=fontStyle)
label_welcome.grid(padx=30, pady=10)
 

#radiobutton to choose mode
label_choose_mode=Label(input,text='Please choose the desired mode',font=fontStyle2).place(x=10,y=80)
v=IntVar()
Radiobutton(input, text="Mode 1: checking fulfillment of safety conditions by entry of all parameters ", variable=v, value=1,font=fontStyle2).place(x=40,y=100)
Radiobutton(input, text="Mode 2: checking the optimal diameter of the wheel while fulfillment of safety conditions by entry of all other parameters", variable=v, value=2,font=fontStyle2).place(x=40,y=130)



text_instructions="To enter the necessary parameters successfully, please upload the Excel-file containing the parameters using the button below (open file) "

label_instructions=Label(input,text=text_instructions, font=fontStyle2)
label_instructions.place(x=10, y=210)




def UploadAction():
    global df 
    filename = filedialog.askopenfilename()
    selected= Label(input, text='Selected: '+ filename, font= fontStyle2 , fg = "blue").place(x=300 ,y= 250)
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
clicked3= StringVar()
clicked3.set("Default")

dropdownmenu_text1= Label(input,text="choose a wheel-material:",font=fontStyle2).place(x=10 ,y=360)
dropdownmenu_wheel= OptionMenu(input, clicked, "GE 300","EN-GJS 600-3","EN-GJS-700-2","25CrMo4","34CrMo4","42CrMo4","33NiCrMoV14-5").place(x=250,y=360)
dropdownmenu_text3= Label(input,text="Hardened:",font=fontStyle2).place(x=400, y=360)
dropdownmenu_wheel_hardened= OptionMenu(input, clicked3, 'True','False').place(x=500,y=360)

clicked1= StringVar()
clicked1.set("Default")
clicked2= StringVar()
clicked2.set("Default")

dropdownmenu_text2= Label(input,text="choose a rail-material:",font=fontStyle2).place(x=10, y=400)
dropdownmenu_rail= OptionMenu(input, clicked1, "S235","S275","S355","S690Q","C35E","C55","R260Mn").place(x=250,y=400)
dropdownmenu_text4= Label(input,text="Hardened:",font=fontStyle2).place(x=400, y=400)
dropdownmenu_rail_hardened= OptionMenu(input, clicked2, 'True','False').place(x=500,y=400)

def callback():
    
    choosen_material_wheel=clicked.get()
    choosen_material_rail=clicked1.get()
    choosen_hardness_wheel=clicked3.get()
    choosen_hardness_rail=clicked2.get()
    return choosen_material_rail,choosen_hardness_rail,choosen_material_wheel,choosen_hardness_wheel
    

clicked.trace("w", callback)
clicked1.trace("w",callback)



#startbutton

def Set_material_parameters(choosen_material_w,choosen_material_r):
      
         E_Modul_w=wheel_dict[choosen_material_w].E
         Bri_Härte_w=wheel_dict[choosen_material_w].HB
         F_Y_w=wheel_dict[choosen_material_w].f_y
         
         E_Modul_r=rail_dict[choosen_material_r].E
         Bri_Härte_r=rail_dict[choosen_material_r].HB
         F_Y_r=rail_dict[choosen_material_r].f_y
        
          
         return E_Modul_r, Bri_Härte_r, F_Y_r, E_Modul_w, Bri_Härte_w, F_Y_w

def Start():
        #set mode and material 
        mode=v.get()
        choosen_material_rail,choosen_hardness_rail,choosen_material_wheel,choosen_hardness_wheel=callback()
        E_Modul_r, Bri_Härte_r, F_Y_r, E_Modul_w, Bri_Härte_w, F_Y_w=Set_material_parameters(choosen_material_wheel,choosen_material_rail)
        
        for i in range(len(df.columns)-1):
            #set factors
            factors={"f_1": 1, "f_2": 1, "f_f":1 ,"f_f1": 1, "f_f2": 1,  "f_f3": 1,"f_f4": 1}
            coefficients={'Y_m': 1.1,'Y_cf': 1.1,'m': 10/3,'v_w': 0.3,'Y_p': 1 }
            
            '''
            if df.iloc[18,i+1]!=None:
                factors["f_1"]=df.iloc[18,i+1]
            if df.iloc[19,i+1]!=None:
                factors["f_2"]=df.iloc[19,i+1]    
            if df.iloc[11,i+1]!= None:
                factors["f_f1"]=df.iloc[11,i+1]
            if  df.iloc[12,i+1]!= None:
                factors["f_f2"]=df.iloc[12,i+1]  
            if  df.iloc[13,i+1]!= None:
                factors["f_f3"]=df.iloc[13,i+1]  
            if  df.iloc[14,i+1]!= None:
                factors["f_f4"]=df.iloc[14,i+1]       
            factors["f_f"]=factors["f_f1"]*factors["f_f2"]*factors["f_f3"]*factors["f_f4"]
            '''
            
            
            #wheel parameters
            Wheel= namedtuple("Wheel", ['material', 'geometry', 'design_parameters', 'variable_parameters', 'factors', 'coefficients'])
            Wheel_material = namedtuple("Wheel_material", "name E hardened HB f_y")    
            Wheel_geometry = namedtuple("Wheel_geometry", ['b_w', 'r_k'])    
            Wheel_variable_parameters={"D_w": df.iloc[10,i+1],"E_m":None, 'Kontaktart':None, 'F_rd_s_w':4, 'F_sd_f':None, 'F_sd_s':None, 'F_u_w':None, 'F_rd_f_w':None, 'D_w_Sf_min': None, 'D_w_Ef_min':None, 'b':None}
            Wheel_design_parameters={'s_c':None,"k_c": None, "i_tot": None,"v_c": None}   
        
                                    
                                                    
            #wheel instance
            wheel_geometry=Wheel_geometry(df.iloc[7,i+1],df.iloc[16,i+1])                  
            wheel_material=Wheel_material(choosen_material_wheel,E_Modul_w,choosen_hardness_wheel,Bri_Härte_w,F_Y_w)
            wheel= Wheel(wheel_material, wheel_geometry, Wheel_design_parameters, Wheel_variable_parameters, factors, coefficients)
                

            #railparameters
            Rail=namedtuple ("Rail", "material geometry design_parameters variable_parameters factors coefficients" )
            Rail_material = namedtuple("Rail_material", "name E hardened HB f_y")   
            Rail_geometry = namedtuple("Rail_geometry", "b_r r_3")    
            Rail_variable_parameters={"E_m": None, 'Kontaktart':None, 'F_rd_s_r':None,'F_sd_f':None,'F_sd_s':None,'F_u_r':None,
                                        'F_rd_f_r':None,'D_w_Sf_min': None,'D_w_Ef_min':None}
            Rail_design_parameters={'s_c':None,"k_c": None, "i_tot": None,"v_c": None}
            
            #rail instance 
            rail_material=Rail_material(choosen_material_rail,E_Modul_r,choosen_hardness_rail,Bri_Härte_r,F_Y_r)
            rail_geometry=Rail_geometry(df.iloc[6,i+1],df.iloc[17,i+1])
            rail=Rail(rail_material, rail_geometry, Rail_variable_parameters, Rail_design_parameters, factors, coefficients)
            
            rbg=RBG(wheel,rail)
            
            rbg.compute_b()
            rbg.compute_E_m()
            wheel = rbg.get_wheel()

            print(i+1)
            
            if mode == 1 :    
                rbg.compute_F_rd_s_w()
                wheel = rbg.get_wheel()
                print(wheel.variable_parameters['F_rd_s_w'])
                    
                rbg.compute_F_u_w()
                wheel = rbg.get_wheel()
                print(wheel.variable_parameters['F_u_w'])        
                    
                rbg.compute_k_c()
                rbg.compute_ν_c()
                wheel=rbg.get_wheel()
                
                rbg.compute_s_c()
                wheel=rbg.get_wheel()

                rbg.compute_F_rd_f_w()
                wheel=rbg.get_wheel()
                print(wheel.variable_parameters["F_rd_f_w"])

            elif mode==2 :

                 rbg.compute_F_sd_s()
                 wheel = rbg.get_wheel()
                 print(wheel.variable_parameters['F_sd_s'])
                 
                 

                 rbg.compute_F_sd_f()
                 wheel=rbg.get_wheel()
                 print(wheel.variable_parameters['F_sd_f'])
                 
                 rbg.compute_k_c()
                 rbg.compute_ν_c()
                 wheel=rbg.get_wheel()
                 
                 rbg.compute_s_c()
                 wheel= rbg.get_wheel()
                 print(wheel.design_parameters['s_c'])
                 
                 
                 rbg.compute_D_w_Ef_min()
                 wheel= rbg.get_wheel()
                 print(wheel.variable_parameters['D_w_Ef_min'])

                 
                     
            else:
                print("please select the desired mode")                
                

        

        
        
        
           #wheel = rbg.get_wheel()
    

    
Start_button= Button(input, text='Start', font=fontStyle1, width=40, command=Start).place(x=300, y=500)

input.mainloop()
