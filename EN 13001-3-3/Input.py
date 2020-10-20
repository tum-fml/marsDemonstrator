import tkinter as tk

window = tk.Tk()
window.title("Address Entry Form")

frame1 = tk.Frame(master=window)
frame1["relief"] = tk.SUNKEN
frame1["borderwidth"] = 3
frame1.pack(fill=tk.X)

frame2 = tk.Frame(master=window)
frame2.pack(fill=tk.X)

list = {
    0: "First Name",
    1: "Last Name",
    2: "Address Line 1",
    3: "Address Line 2",
    4: "City",
    5: "State/Province",
    6: "Postal Code",
    7: "Country",
}