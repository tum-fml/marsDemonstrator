import tkinter


input = tkinter.Tk()
input.title("Eigenschaften des Rad-Schiene Systems")
input.minsize(600,450)
label_welcome = tkinter.Label(input, text="Welcome to MARS")
label_welcome.pack()

entry_par = tkinter.Entry(input, width="45")
entry_par.pack()
#input.geometry("800x600")

input.mainloop()

