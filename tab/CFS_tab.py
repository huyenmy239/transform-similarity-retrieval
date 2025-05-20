from tkinter import ttk, messagebox, Toplevel, StringVar, Entry
from tkinter.ttk import Combobox
import tkinter as tk
import json
import re
from cost_function_server import CostFunctionServer

class TabCFS:
    def __init__(self, parent):
        self.parent = parent
        self.server = CostFunctionServer()

        # Label tiêu đề
        label = ttk.Label(parent, text="Hàm Chi Phí (CFS)", font=("Arial", 14))
        label.pack(pady=10)

        # Các nút chức năng
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="➕ Thêm Hàm Chi Phí", command=self.add_cost_function).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🧮 Tính Chi Phí", command=self.evaluate_cost).pack(side="left", padx=5)
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill="both", expand=True, pady=10)

        ttk.Label(self.main_frame, text="📄 Danh Sách Hàm Chi Phí", font=("Arial", 12, "bold")).pack(anchor="w", pady=10)

        # Thanh cuộn dọc
        scrollbar_y = ttk.Scrollbar(self.main_frame)
        scrollbar_y.pack(side="right", fill="y")

        # Thanh cuộn ngang
        scrollbar_x = ttk.Scrollbar(self.main_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        # Listbox với cả thanh cuộn dọc và ngang
        self.listbox = tk.Listbox(
            self.main_frame, width=80, height=15, font=("Arial", 10),
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )
        self.listbox.pack(pady=5, fill="both", expand=True)
        scrollbar_y.config(command=self.listbox.yview)
        scrollbar_x.config(command=self.listbox.xview)

        self.refresh_cost_functions()

    def normalize_formula(self, formula):
        formula = formula.replace("√", "sqrt")
        formula = formula.replace("∛", "cbrt")
        formula = formula.replace("∜", "fourthrt")
        formula = formula.replace("²", "**2")
        formula = formula.replace("^", "**")
        formula = formula.replace("∑", "sum")
        formula = re.sub(r"sqrt(\w+)", r"sqrt(\1)", formula)
        formula = re.sub(r"cbrt(\w+)", r"cbrt(\1)", formula)
        formula = re.sub(r"fourthrt(\w+)", r"fourthrt(\1)", formula)
        return formula

    def display_formula(self, formula):
        formula = formula.replace("sqrt", "√")
        formula = formula.replace("cbrt", "∛")
        formula = formula.replace("fourthrt", "∜")
        formula = formula.replace("**2", "²")
        formula = formula.replace("**", "^")
        formula = formula.replace("sum", "∑")
        return formula
    
    def refresh_cost_functions(self):
        self.listbox.delete(0, tk.END)
        try:
            with open(self.server.path, "r") as f:
                data = json.load(f)
                for func in data:
                    display_text = self.display_formula(func["formula"])
                    self.listbox.insert(
                        tk.END, f"{func['name']} ({func['type']}): {display_text}"
                    )
        except Exception as e:
            print("Lỗi khi đọc file JSON:", e)
            messagebox.showerror("Lỗi", f"Lỗi khi đọc file JSON: {e}", parent=self.parent)

    def add_cost_function(self):
        window = Toplevel(self.parent)
        window.title("Thêm Hàm Chi Phí")
        window.geometry("600x700")
        window.resizable(False, False)

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        input_fields = [
            ("Tên hàm chi phí:", StringVar()),
            ("Loại phép biến đổi:", StringVar()),
            ("Công thức:", StringVar()),
        ]

        for idx, (label_text, var) in enumerate(input_fields):
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill="x", pady=8)
            ttk.Label(row_frame, text=label_text, font=("Arial", 12), width=20, anchor="e").pack(side="left")
            entry = ttk.Entry(row_frame, textvariable=var, width=40, font=("Arial", 12))
            entry.pack(side="left", padx=5)
            if label_text == "Công thức:":
                formula_entry = entry

        # Máy tính công thức
        calc_frame = ttk.Frame(frame)
        calc_frame.pack(fill="both", pady=10)

        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2), ("/", 0, 3), ("p(", 0, 4), ("∑", 0, 5),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("*", 1, 3), (")", 1, 4), ("x", 1, 5),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2), ("-", 2, 3), ("q", 2, 4), ("y", 2, 5),
            ("0", 3, 0), (".", 3, 1), ("+", 3, 2), ("^", 3, 3), ("k", 3, 4), ("z", 3, 5),
            ("√", 4, 0), ("∛", 4, 1), ("∜", 4, 2), ("²", 4, 3), ("a", 4, 4), ("b", 4, 5),
            ("C", 5, 0), ("⌫", 5, 1), ("(", 5, 2), (")", 5, 3), ("=", 5, 4), (",", 5, 5),
        ]

        def insert_text(text):
            if text == "C":
                input_fields[2][1].set("")
            elif text == "⌫":
                current = input_fields[2][1].get()
                input_fields[2][1].set(current[:-1])
            else:
                formula_entry.insert(tk.END, text)

        for text, row, col in buttons:
            btn = ttk.Button(calc_frame, text=text, width=8, command=lambda t=text: insert_text(t))
            btn.grid(row=row, column=col, padx=2, pady=2)

        def submit():
            name = input_fields[0][1].get()
            type_ = input_fields[1][1].get()
            formula = input_fields[2][1].get()
            if not name or not type_ or not formula:
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!", parent=window)
                return
            normalized_formula = self.normalize_formula(formula)
            cost_func = {"name": name, "type": type_, "formula": normalized_formula}
            try:
                self.server.CostInsert(cost_func)
                self.refresh_cost_functions()
                window.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=window)

        ttk.Button(frame, text="Xác Nhận", command=submit).pack(pady=20)

    def evaluate_cost(self):
        with open(self.server.path, "r") as f:
            cost_functions = json.load(f)

        if not cost_functions:
            messagebox.showinfo("Thông báo", "Chưa có hàm chi phí nào.", parent=self.parent)
            return

        names = sorted(func["name"] for func in cost_functions)
        window = Toplevel(self.parent)
        window.title("Tính Chi Phí")
        window.geometry("400x500")
        window.resizable(False, False)

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        select_frame = ttk.Frame(frame)
        select_frame.pack(fill="x", pady=8)
        ttk.Label(select_frame, text="Chọn hàm chi phí:", font=("Arial", 12), width=20, anchor="e").pack(side="left")
        name_var = StringVar()
        cb = Combobox(select_frame, textvariable=name_var, values=names, state="readonly", width=30)
        cb.pack(side="left", padx=5)

        param_frame = ttk.Frame(frame)
        param_frame.pack(fill="both", pady=10)
        param_entries = {}

        def on_name_selected(event=None):
            for widget in param_frame.winfo_children():
                widget.destroy()

            selected_name = name_var.get()
            func = next((f for f in cost_functions if f["name"] == selected_name), None)
            if not func:
                messagebox.showerror("Lỗi", f"Không tìm thấy hàm chi phí với tên '{selected_name}'", parent=window)
                return

            formula = func["formula"]
            all_vars = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", formula)
            reserved = {"diff", "sqrt", "cbrt", "fourthrt", "sum", "rgb_to_val", "abs"}
            variables = sorted(set(v for v in all_vars if v not in reserved))

            param_entries.clear()
            for idx, var in enumerate(variables):
                row = ttk.Frame(param_frame)
                row.pack(fill="x", pady=5)
                ttk.Label(row, text=f"{var}:", width=20, font=("Arial", 10), anchor="e").pack(side="left")
                entry_var = StringVar()
                ttk.Entry(row, textvariable=entry_var, width=20).pack(side="left", padx=5)
                param_entries[var] = entry_var

        cb.bind("<<ComboboxSelected>>", on_name_selected)

        def submit():
            selected_name = name_var.get()
            func = next((f for f in cost_functions if f["name"] == selected_name), None)
            if not func:
                messagebox.showerror("Lỗi", f"Không tìm thấy hàm chi phí với tên '{selected_name}'", parent=window)
                return

            params = {}
            for var, entry_var in param_entries.items():
                value = entry_var.get()
                try:
                    value = float(value) if '.' in value else int(value)
                except:
                    value = value
                params[var] = value

            operator = {"type": func["type"], "params": params}
            try:
                cost = self.server.EvaluateCall(operator)
                messagebox.showinfo("Kết quả", f"Chi phí tính được: {cost}", parent=window)
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=window)

        ttk.Button(frame, text="Tính", command=submit).pack(pady=20)