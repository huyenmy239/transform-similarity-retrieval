from tkinter import ttk

class TabHome:
    def __init__(self, parent):
        label = ttk.Label(parent, text="Chào mừng đến Home Tab")
        label.pack(pady=10)
        label = ttk.Label(parent, text="Chọn một tab khác để bắt đầu")