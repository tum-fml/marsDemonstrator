from tkinter import *


"""def Auswahl(v):
    if v==1:    

      Modus1= Tk()
      Modus1.title("Modus 1: Überprüfung der statischen Festigkeits- und Ermüdungsfestigkeitsnachweise")
      l1=Label(Modus1, text='Bitte tragen Sie die Parameter ein.').pack()
      l2=Label(Modus1, text="yacine").pack()
      e1= Entry(Modus1).pack()
      
      Modus1.mainloop()
      
    elif v==2:    
       
        Modus2= Tk()
        Modus2.title("Modus 2: Bestimmung des minimalen Laufraddurchmessers unter Nachweiserfüllung ")
        Label3=Label(Modus2, Text='Bitte tragen Sie die Parameter ein.').grid(row=0)
        
        Label4=Label(Modus2, Text="yacine2").grid(row=1)
        e1 = Entry(Modus2)
        e1.grid(row=1, column=1)
        
        Modus2.mainloop() """

def yassine():
      
      Modus1= Tk()
      Modus1.title("Modus 1: Überprüfung der statischen Festigkeits- und Ermüdungsfestigkeitsnachweise")
      Modus1.minsize(600,500)
      l1=Label(Modus1, text='Bitte tragen Sie die Parameter ein.').grid(row=1, column=1)
      
      for x in range(0,len(fields)):
       l2=Label(Modus1, text=fields[x]).grid(row=3+x)
       e1= Entry(Modus1).grid(row=3+x, column=1)
      
      Modus1.mainloop()

input = Tk()
input.title("Eigenschaften des Rad-Schiene Systems")
input.minsize(600,500)
label_welcome =Label(input, text="Willkommen bei MARS.")
label_welcome.grid(row=1, column = 1)

   
v=IntVar()
Label2=Label(input, text="Wählen Sie bitte den von Ihnen gewünschten Modus").grid(row=7,column=1)
r1=Radiobutton(input, text="Modus 1: Überprüfung der statischen Festigkeits- und Ermüdungsfestigkeitsnachweis ", padx = 20, variable=v, value=1).grid(row=8,column=1)
r2=Radiobutton(input, text="Modus 2: Bestimmung des minimalen Laufraddurchmessers unter Nachweiserfüllung", padx = 20, variable=v, value=2).grid(row=9,column=1)

b1=Button(input, text="Bestätigen", command=yassine).grid(row=10, column=1)





fields = ('Brinellhärte des Radmaterials: HB_w =', 'Brinellhärte des Schienenmaterials: HB_r', 'Querkontraktionszahl des Schienenmaterials: v_r =', 'Querkontraktionszahl des Radmaterials: v_w ', 'Raddurchmesser: D_w =', 'Elastizitätsmodul des Schienenmaterials: E_r','Elastizitätsmodul des Radmaterials: E_w =','Kontaktwiderstandsbeiwert: Y_cf =','Risikobeiwert: Y_n =','Teilsicherheitsbeiwert: Y_p =','Neigungskonstante für log-F/log-N-Kurve für Rollkontakte: m =','Radius der Laufradkante: r_3 =','Materialbreite des Laufrads: b_w =','Materialbreite der Schiene: b_r =')


input.mainloop()



