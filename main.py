import tkinter as tk
from tkinter import ttk
from tab.Home_tab import TabHome
from tab.TLM_tab import TabTLM
from tab.CFS_tab import TabCFS
from tab.OC_tab import TabOC
from tab.Sequence_tab import TabSequence
from tab.About_tab import TabAbout
from object_manager import ImageDatabase, load_or_create_database, save_database

db_file = "image_database.pkl"
db = load_or_create_database(db_file)

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Object Image Editor")
root.geometry("1200x750")
root.configure(bg="#f0f4f8")

# Tùy chỉnh giao diện với ttk.Style
style = ttk.Style()
style.configure("TButton", font=("Helvetica", 10), padding=5)
style.configure("TCombobox", font=("Helvetica", 10))
style.configure("TLabel", background="#f0f4f8", font=("Helvetica", 10, "bold"))
style.configure("TFrame", background="#f0f4f8")

# Tạo Notebook để chứa các tab
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# Tạo các Frame cho từng tab
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
tab3 = ttk.Frame(notebook)
tab4 = ttk.Frame(notebook)
tab5 = ttk.Frame(notebook)
tab6 = ttk.Frame(notebook)

# Thêm các tab vào notebook
notebook.add(tab1, text='Home')
notebook.add(tab2, text='Transformation Library Manager')
notebook.add(tab3, text='Cost Function Server')
notebook.add(tab4, text='Object Convertor')
notebook.add(tab5, text='Sequence Editor')
notebook.add(tab6, text='About')

# Tạo các tab
tab_home = TabHome(tab1, db)
tab_tlm = TabTLM(tab2, db)
tab_cfs = TabCFS(tab3)
tab_oc = TabOC(tab4, db)
tab_s = TabSequence(tab5, db)
tab_about = TabAbout(tab6)

# Chạy vòng lặp
root.mainloop()