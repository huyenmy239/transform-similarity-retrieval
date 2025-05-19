import tkinter as tk
from tkinter import ttk
from tab.TLM_tab import TabTLM
from tab.CFS_tab import TabCFS
from tab.OC_tab import TabOC
from tab.Home_tab import TabHome
from tab.About_tab import TabAbout

# Tạo cửa sổ chính
root = tk.Tk()
root.title("transform-ation-based")
root.geometry("1000x500")

# Tạo Notebook để chứa các tab
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# Tạo các Frame cho từng tab
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
tab3 = ttk.Frame(notebook)
tab4 = ttk.Frame(notebook)
tab5 = ttk.Frame(notebook)

# Thêm các tab vào notebook
notebook.add(tab1, text='Home')
notebook.add(tab2, text='Transformation Library Manager')
notebook.add(tab3, text='Cost Function Server')
notebook.add(tab4, text='Object Convertor')
notebook.add(tab5, text='About')

# Tạo các tab
tab_home = TabHome(tab1)
tab_tlm = TabTLM(tab2)
tab_cfs = TabCFS(tab3)
tab_oc = TabOC(tab4)
tab_about = TabAbout(tab5)

# Chạy vòng lặp
root.mainloop()
