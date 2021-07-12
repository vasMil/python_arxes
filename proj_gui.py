from tkinter import *
from tkinter import ttk


def main_window(filenames, ws_argv):
    # Always include this
    root = Tk()
    root.geometry('340x150')
    root.resizable(False, False)
    root.title('Python Project')

    update_db = IntVar()
    download = IntVar()

    # Define all the labels
    l_dataset = Label(root, text="Dataset:")
    l_plot = Label(root, text="Plot:")
    l_country = Label(root, text="Country:")
    # Place labels on grid
    l_dataset.grid(row=0, column=0, sticky=W, padx=10, pady=10)
    l_country.grid(row=1, column=0, sticky=W, padx=10, pady=10)
    l_plot.grid(row=2, column=0, rowspan=2, sticky=W, padx=10, pady=10)

    # Create buttons
    b_nat = Button(root, text="Natives", width=9)
    b_for = Button(root, text="Foreigners", width=9)
    b_tot = Button(root, text="Total", width=9)
    b_bar = Button(root, text="Barchart", width=35)
    # Place on grid
    b_nat.grid(row=2, column=1, sticky=W)
    b_for.grid(row=2, column=2)
    b_tot.grid(row=2, column=3, sticky=E)
    b_bar.grid(row=3, column=1, columnspan=3)

    # Create Checkboxes
    cb_db = Checkbutton(root, text='Update', variable=update_db, onvalue=1, offvalue=0)
    cb_down = Checkbutton(root, text='Down', variable=download, onvalue=1, offvalue=0)
    # Place on grid
    cb_db.grid(row=1, column=3, pady=10)
    cb_down.grid(row=1, column=2, pady=10)

    # Combobox
    combo_inp = StringVar()
    data_combo = ttk.Combobox(root, width=35, textvariable=combo_inp)
    data_combo['values'] = ([option.split(" ")[0] for option in filenames])
    data_combo.grid(row=0, column=1, columnspan=3)

    root.mainloop()

