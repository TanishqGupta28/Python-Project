"""
Mall Bill Generator - colourful UI + Add / Remove Products
Uses: tkinter (GUI), numpy (calculations), matplotlib (live chart)

Run:  python bill_generator_mall.py
Install once:  pip install numpy matplotlib

Products are saved automatically in products.json (next to this file),
so the products you add or remove are remembered next time.
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
SHOP_NAME = "CITY MALL"
GST_RATE = 18  # percent
PRODUCTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")

DEFAULT_PRODUCTS = {
    "T-Shirt": 599,
    "Jeans": 1499,
    "Sneakers": 2499,
    "Wrist Watch": 1999,
    "Backpack": 1299,
    "Headphones": 1799,
    "Phone Case": 399,
    "Perfume": 899,
    "Sunglasses": 999,
    "Water Bottle": 349,
    "Handbag": 1899,
    "Toy Car": 499,
}

# ------------------------------------------------------------------
# Colour palette
# ------------------------------------------------------------------
BG = "#fdf2f8"        # soft pink background
HEADER = "#7c3aed"    # purple
PRIMARY = "#2563eb"   # blue
SUCCESS = "#16a34a"   # green
DANGER = "#dc2626"    # red
WARN = "#f59e0b"      # orange
TEAL = "#0d9488"
CARD = "#ffffff"
TEXT = "#334155"
DARK = "#1e1b4b"
BAR_COLORS = ["#7c3aed", "#2563eb", "#0d9488", "#16a34a", "#f59e0b",
              "#ef4444", "#ec4899", "#06b6d4"]


def make_button(parent, text, command, color, width=14):
    return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                     activebackground=color, activeforeground="white",
                     font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                     width=width, pady=7, cursor="hand2")


class BillApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{SHOP_NAME} - Bill Generator")
        self.root.geometry("1180x720")
        self.root.minsize(1020, 660)
        self.root.configure(bg=BG)

        self.products = self.load_products()
        self.items = []  # bill items: [name, price, qty]

        self.setup_style()
        self.build_header()

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=15, pady=10)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        self.build_customer_card(left)
        self.build_item_card(left)
        self.build_table(left)
        self.build_totals_card(right)
        self.build_chart_card(right)
        self.build_buttons(right)

        self.refresh()

    # ------------------------ Product storage ---------------------
    def load_products(self):
        try:
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data:
                return {str(k): float(v) for k, v in data.items()}
        except (OSError, ValueError):
            pass
        return {k: float(v) for k, v in DEFAULT_PRODUCTS.items()}

    def save_products(self):
        try:
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
        except OSError:
            messagebox.showwarning("Save failed", "Could not save products.json")

    # ------------------------ Styling -----------------------------
    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=30, font=("Segoe UI", 10),
                        borderwidth=0)
        style.configure("Treeview.Heading", background=HEADER, foreground="white",
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview.Heading", background=[("active", HEADER)])
        style.map("Treeview", background=[("selected", PRIMARY)],
                  foreground=[("selected", "white")])

    def card(self, parent, title, color=HEADER):
        outer = tk.Frame(parent, bg=CARD, highlightbackground="#e9d5ff",
                         highlightthickness=1)
        outer.pack(fill="x", pady=(0, 10))
        tk.Frame(outer, bg=color, height=4).pack(fill="x")  # coloured top strip
        tk.Label(outer, text=title, bg=CARD, fg=color,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(6, 2))
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="x", padx=12, pady=(0, 10))
        return inner

    # ------------------------ Header ------------------------------
    def build_header(self):
        header = tk.Frame(self.root, bg=HEADER, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"\U0001F6CD  {SHOP_NAME}", bg=HEADER, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=20)
        self.clock_var = tk.StringVar()
        tk.Label(header, textvariable=self.clock_var, bg=HEADER, fg="#ddd6fe",
                 font=("Segoe UI", 11)).pack(side="right", padx=20)
        self.update_clock()

    def update_clock(self):
        self.clock_var.set(datetime.now().strftime("%d %b %Y   %I:%M:%S %p"))
        self.root.after(1000, self.update_clock)

    # ------------------------ Left side ---------------------------
    def build_customer_card(self, parent):
        inner = self.card(parent, "Customer Details", HEADER)
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        self.discount_var.trace_add("write", lambda *a: self.refresh())

        fields = [("Name", self.name_var, 22), ("Phone", self.phone_var, 15),
                  ("Discount %", self.discount_var, 6)]
        for col, (label, var, width) in enumerate(fields):
            tk.Label(inner, text=label, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 9)).grid(row=0, column=col, sticky="w", padx=(0, 10))
            tk.Entry(inner, textvariable=var, width=width, font=("Segoe UI", 10),
                     relief="solid", bd=1).grid(row=1, column=col, padx=(0, 10), ipady=4)

    def build_item_card(self, parent):
        inner = self.card(parent, "Add Item to Bill", TEAL)
        self.product_var = tk.StringVar()
        self.qty_var = tk.IntVar(value=1)
        self.price_var = tk.StringVar(value="0.00")

        tk.Label(inner, text="Product", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.combo = ttk.Combobox(inner, textvariable=self.product_var, state="readonly",
                                  width=20, font=("Segoe UI", 10))
        self.combo.grid(row=1, column=0, padx=(0, 10), ipady=3)
        self.combo.bind("<<ComboboxSelected>>", self.on_product_change)

        tk.Label(inner, text="Price", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")
        tk.Label(inner, textvariable=self.price_var, bg="#ccfbf1", fg=TEAL,
                 font=("Segoe UI", 11, "bold"), width=9).grid(row=1, column=1, padx=(0, 10), ipady=4)

        tk.Label(inner, text="Quantity", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w")
        tk.Spinbox(inner, from_=1, to=999, textvariable=self.qty_var, width=5,
                   font=("Segoe UI", 10), relief="solid", bd=1).grid(row=1, column=2, padx=(0, 10), ipady=4)

        make_button(inner, "+ Add", self.add_item, PRIMARY, 8).grid(row=1, column=3, padx=(0, 6))
        make_button(inner, "Manage Products", self.open_product_manager, HEADER, 16).grid(row=1, column=4)

        self.reload_combo()

    def build_table(self, parent):
        wrap = tk.Frame(parent, bg=CARD, highlightbackground="#e9d5ff", highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        cols = ("item", "price", "qty", "total")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        for col, text, width in [("item", "Item", 230), ("price", "Price", 90),
                                 ("qty", "Qty", 70), ("total", "Total", 110)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")
        self.tree.tag_configure("odd", background="#faf5ff")
        self.tree.tag_configure("even", background=CARD)

        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        row_btns = tk.Frame(parent, bg=BG)
        row_btns.pack(fill="x", pady=8)
        make_button(row_btns, "Remove Selected", self.remove_item, DANGER, 16).pack(side="left")
        make_button(row_btns, "Clear Bill", self.clear_all, WARN, 12).pack(side="left", padx=8)

    # ------------------------ Right side --------------------------
    def build_totals_card(self, parent):
        inner = self.card(parent, "Bill Summary", PRIMARY)
        self.sub_var = tk.StringVar()
        self.disc_amt_var = tk.StringVar()
        self.gst_var = tk.StringVar()
        self.total_var = tk.StringVar()

        rows = [("Subtotal", self.sub_var, DARK), ("Discount", self.disc_amt_var, DANGER),
                (f"GST ({GST_RATE}%)", self.gst_var, WARN)]
        for r, (label, var, color) in enumerate(rows):
            tk.Label(inner, text=label, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 10)).grid(row=r, column=0, sticky="w", pady=2)
            tk.Label(inner, textvariable=var, bg=CARD, fg=color,
                     font=("Segoe UI", 10, "bold")).grid(row=r, column=1, sticky="e", pady=2)
        inner.columnconfigure(1, weight=1)

        box = tk.Frame(inner, bg=SUCCESS)
        box.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(box, text="GRAND TOTAL", bg=SUCCESS, fg="white",
                 font=("Segoe UI", 9, "bold")).pack(pady=(6, 0))
        tk.Label(box, textvariable=self.total_var, bg=SUCCESS, fg="white",
                 font=("Segoe UI", 22, "bold")).pack(pady=(0, 6))

    def build_chart_card(self, parent):
        outer = tk.Frame(parent, bg=CARD, highlightbackground="#e9d5ff", highlightthickness=1)
        outer.pack(fill="both", expand=True, pady=(0, 10))
        tk.Frame(outer, bg=WARN, height=4).pack(fill="x")
        tk.Label(outer, text="Live Chart", bg=CARD, fg=WARN,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(6, 0))

        self.fig = Figure(figsize=(4, 2.8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=outer)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def build_buttons(self, parent):
        make_button(parent, "Generate Bill", self.generate_bill, SUCCESS, 30).pack(fill="x")

    # ------------------------ Product manager ---------------------
    def reload_combo(self):
        names = list(self.products)
        self.combo["values"] = names
        if names:
            if self.product_var.get() not in self.products:
                self.product_var.set(names[0])
            self.on_product_change()
        else:
            self.product_var.set("")
            self.price_var.set("0.00")

    def open_product_manager(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Products")
        win.configure(bg=BG)
        win.geometry("460x520")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Manage Mall Products", bg=HEADER, fg="white",
                 font=("Segoe UI", 14, "bold"), pady=10).pack(fill="x")

        wrap = tk.Frame(win, bg=CARD, highlightbackground="#e9d5ff", highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=15, pady=(12, 6))
        tree = ttk.Treeview(wrap, columns=("name", "price"), show="headings", height=10)
        tree.heading("name", text="Product")
        tree.heading("price", text="Price")
        tree.column("name", width=250, anchor="w")
        tree.column("price", width=100, anchor="center")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def fill_tree():
            tree.delete(*tree.get_children())
            for n, (name, price) in enumerate(self.products.items()):
                tree.insert("", "end", iid=name, tags=("odd" if n % 2 else "even",),
                            values=(name, f"{price:.2f}"))
            tree.tag_configure("odd", background="#faf5ff")
            tree.tag_configure("even", background=CARD)

        form = tk.Frame(win, bg=BG)
        form.pack(fill="x", padx=15, pady=6)
        name_var, price_var = tk.StringVar(), tk.StringVar()
        tk.Label(form, text="Product name", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(form, text="Price", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")
        tk.Entry(form, textvariable=name_var, width=28, font=("Segoe UI", 10),
                 relief="solid", bd=1).grid(row=1, column=0, padx=(0, 10), ipady=4)
        tk.Entry(form, textvariable=price_var, width=10, font=("Segoe UI", 10),
                 relief="solid", bd=1).grid(row=1, column=1, ipady=4)

        def on_select(_e=None):
            sel = tree.selection()
            if sel:
                name_var.set(sel[0])
                price_var.set(f"{self.products[sel[0]]:g}")
        tree.bind("<<TreeviewSelect>>", on_select)

        def add_or_update():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Invalid", "Enter a product name.", parent=win)
                return
            try:
                price = float(price_var.get())
                if price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Price must be a number greater than 0.", parent=win)
                return
            self.products[name] = price
            self.save_products()
            fill_tree()
            self.reload_combo()
            name_var.set("")
            price_var.set("")

        def remove():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select", "Select a product to remove.", parent=win)
                return
            name = sel[0]
            if not messagebox.askyesno("Confirm", f"Remove '{name}' from products?", parent=win):
                return
            del self.products[name]
            self.save_products()
            fill_tree()
            self.reload_combo()
            name_var.set("")
            price_var.set("")

        btns = tk.Frame(win, bg=BG)
        btns.pack(pady=8)
        make_button(btns, "Add / Update", add_or_update, SUCCESS, 14).grid(row=0, column=0, padx=5)
        make_button(btns, "Remove Selected", remove, DANGER, 15).grid(row=0, column=1, padx=5)
        make_button(btns, "Close", win.destroy, PRIMARY, 8).grid(row=0, column=2, padx=5)

        fill_tree()

    # ------------------------ Logic (numpy) -----------------------
    def calculate(self):
        if not self.items:
            return np.array([]), 0.0, 0.0, 0.0, 0.0
        prices = np.array([i[1] for i in self.items], dtype=float)
        qtys = np.array([i[2] for i in self.items], dtype=float)
        line_totals = prices * qtys

        try:
            pct = float(self.discount_var.get() or 0)
        except ValueError:
            pct = 0.0
        pct = float(np.clip(pct, 0, 100))

        subtotal = line_totals.sum()
        discount = subtotal * pct / 100
        gst = (subtotal - discount) * GST_RATE / 100
        total = subtotal - discount + gst
        return (line_totals, round(subtotal, 2), round(discount, 2),
                round(gst, 2), round(total, 2))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        line_totals, subtotal, discount, gst, total = self.calculate()
        for n, (item, lt) in enumerate(zip(self.items, line_totals)):
            self.tree.insert("", "end", tags=("odd" if n % 2 else "even",),
                             values=(item[0], f"{item[1]:.2f}", item[2], f"{lt:.2f}"))
        self.sub_var.set(f"\u20b9 {subtotal:,.2f}")
        self.disc_amt_var.set(f"- \u20b9 {discount:,.2f}")
        self.gst_var.set(f"\u20b9 {gst:,.2f}")
        self.total_var.set(f"\u20b9 {total:,.2f}")
        self.draw_chart(line_totals)

    def draw_chart(self, line_totals):
        self.ax.clear()
        if len(line_totals) == 0:
            self.ax.text(0.5, 0.5, "Add items to see chart", ha="center",
                         va="center", color="#94a3b8", fontsize=11)
            self.ax.axis("off")
        else:
            names = [i[0] for i in self.items]
            colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(len(names))]
            self.ax.axis("on")
            self.ax.barh(names, line_totals, color=colors)
            self.ax.set_xlabel("Amount (\u20b9)", fontsize=8)
            self.ax.tick_params(labelsize=8)
            self.ax.invert_yaxis()
            for spine in ("top", "right"):
                self.ax.spines[spine].set_visible(False)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    # ------------------------ Bill actions ------------------------
    def on_product_change(self, _event=None):
        name = self.product_var.get()
        if name in self.products:
            self.price_var.set(f"{self.products[name]:.2f}")

    def add_item(self):
        name = self.product_var.get()
        if name not in self.products:
            messagebox.showinfo("No product", "Add a product first using Manage Products.")
            return
        try:
            qty = int(self.qty_var.get())
            if qty <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid", "Quantity must be a positive whole number.")
            return

        for item in self.items:
            if item[0] == name:
                item[2] += qty
                item[1] = self.products[name]
                break
        else:
            self.items.append([name, self.products[name], qty])
        self.qty_var.set(1)
        self.refresh()

    def remove_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an item in the table first.")
            return
        del self.items[self.tree.index(sel[0])]
        self.refresh()

    def clear_all(self):
        if self.items and not messagebox.askyesno("Confirm", "Clear the whole bill?"):
            return
        self.items.clear()
        self.name_var.set("")
        self.phone_var.set("")
        self.discount_var.set("0")
        self.refresh()

    def build_bill_text(self):
        line_totals, subtotal, discount, gst, total = self.calculate()
        now = datetime.now()
        bar = "=" * 52
        lines = [
            bar, SHOP_NAME.center(52), "TAX INVOICE".center(52), bar,
            f"Bill No : {now.strftime('%Y%m%d%H%M%S')}",
            f"Date    : {now.strftime('%d-%m-%Y %H:%M')}",
            f"Customer: {self.name_var.get() or 'Walk-in'}",
            f"Phone   : {self.phone_var.get() or '-'}",
            bar, f"{'Item':<24}{'Price':>8}{'Qty':>6}{'Total':>12}", "-" * 52,
        ]
        for item, lt in zip(self.items, line_totals):
            lines.append(f"{item[0]:<24}{item[1]:>8.2f}{item[2]:>6}{lt:>12.2f}")
        lines += [
            "-" * 52,
            f"{'Subtotal':<38}{subtotal:>14.2f}",
            f"{'Discount':<38}{-discount:>14.2f}",
            f"{'GST (' + str(GST_RATE) + '%)':<38}{gst:>14.2f}",
            bar, f"{'GRAND TOTAL':<38}{total:>14.2f}", bar,
            "Thank you! Visit again.".center(52),
        ]
        return "\n".join(lines)

    def generate_bill(self):
        if not self.items:
            messagebox.showwarning("Empty", "Add at least one item first.")
            return
        text = self.build_bill_text()

        win = tk.Toplevel(self.root)
        win.title("Bill")
        win.configure(bg=BG)
        box = tk.Text(win, font=("Courier New", 10), width=54, height=30,
                      relief="flat", bg="white")
        box.insert("1.0", text)
        box.config(state="disabled")
        box.pack(padx=15, pady=15)

        def save():
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text file", "*.txt")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                messagebox.showinfo("Saved", f"Bill saved to:\n{path}", parent=win)

        make_button(win, "Save as .txt", save, PRIMARY, 18).pack(pady=(0, 15))


if __name__ == "__main__":
    root = tk.Tk()
    BillApp(root)
    root.mainloop()