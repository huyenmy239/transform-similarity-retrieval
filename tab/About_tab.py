import tkinter as tk
from tkinter import ttk

class TabAbout:
    def __init__(self, parent):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.parent, bg="#f0f4f8")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="About Object Image Editor", font=("Helvetica", 12, "bold"), bg="#f0f4f8", fg="#2c3e50").pack(pady=10)
        tk.Label(frame, text="Phiên bản: 1.0\nTác giả: Nhóm 06\nMô tả: Ứng dụng chỉnh sửa ảnh với các phép biến đổi.", 
                 font=("Helvetica", 10), bg="#f0f4f8", justify="left").pack(pady=5)