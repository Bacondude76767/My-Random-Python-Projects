# Calculator.py — fully patched, integrated, ready-to-run
import tkinter as tk
from tkinter import Toplevel, messagebox, ttk, colorchooser
import subprocess
import sys
import webbrowser
import platform

# requests is optional — we handle if missing
try:
    import requests
except Exception:
    requests = None

# --- Configuration / Constants ---
APP_VERSION = "2.3.7"
AUTHOR = "Bacondude76767"
GITHUB_URL = "https://github.com/Bacondude76767"

# a compact but useful list of currency codes for comboboxes
CURRENCY_CODES = [
    "USD","EUR","GBP","JPY","AUD","CAD","CHF","CNY","SEK","NZD",
    "MXN","SGD","HKD","NOK","KRW","TRY","INR","RUB","BRL","ZAR"
]

FALLBACK_RATES = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.8, "JPY": 145.0, "AUD": 1.5, "CAD": 1.35,
    "CHF": 0.97, "CNY": 7.2, "SEK": 10.0, "NZD": 1.6, "MXN": 18.5, "SGD": 1.35,
    "HKD": 7.8, "NOK": 11.0, "KRW": 1380.0, "TRY": 29.0, "INR": 83.0, "RUB": 77.0,
    "BRL": 5.2, "ZAR": 19.0
}

# --- Main Application ---
class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        # borderless window but still movable via header
        self.overrideredirect(True)
        self.configure(bg="#c0c0c0")

        # default window size (modifiable in Preferences)
        self.window_width = 400
        self.window_height = 550

        # header color (modifiable in Preferences)
        self.top_border_color = "#000080"

        # storage for calculation history
        self.last_results = []

        # used to avoid keyboard handling while average window is open (prevents conflicts)
        self.average_window_open = False

        # offset for dragging
        self.offset_x = 0
        self.offset_y = 0

        # build UI and center
        self._center_window(self.window_width, self.window_height)
        self._build_ui()

        # global keyboard handling (safe: will ignore events when focus is an Entry that's not the main display)
        self.bind_all("<Key>", self._on_key, add=True)

    # -------------------- Window utilities --------------------
    def _center_window(self, width, height):
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _center_child(self, win, width, height):
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _create_window(self, width=350, height=250, title=""):
        """Create a centered bordered Toplevel window matching header color and draggable top bar."""
        win = Toplevel(self)
        win.overrideredirect(True)
        self._center_child(win, width, height)
        win.configure(bg="#c0c0c0")

        top = tk.Frame(win, bg=self.top_border_color, height=30)
        top.pack(fill="x", side="top")
        if title:
            tk.Label(top, text=title, bg=self.top_border_color, fg="white", font=("Segoe UI", 11, "bold")).pack(side="left", padx=8)
        # close button on the right
        tk.Button(top, text="X", bg="#ff0000", fg="white", relief="raised", command=win.destroy).pack(side="right", padx=6, pady=2)

        # make the top draggable for the child window
        def start(e):
            win._drag_x = e.x
            win._drag_y = e.y
        def drag(e):
            win.geometry(f"+{e.x_root - win._drag_x}+{e.y_root - win._drag_y}")
        top.bind("<Button-1>", start)
        top.bind("<B1-Motion>", drag)
        return win, top

    # -------------------- Header / Main UI --------------------
    def _build_ui(self):
        # header
        self.header = tk.Frame(self, bg=self.top_border_color, height=30)
        self.header.pack(fill="x", side="top")
        self.header.bind("<Button-1>", self._start_move)
        self.header.bind("<B1-Motion>", self._on_move)

        # top-right header buttons: X, placeholder (⋯) -> now Information, and @ (Settings)
        for text, cmd, bg in [
            ("X", self.destroy, "#ff0000"),
            ("⋯", self._open_info_window, "#c0c0c0"),
            ("@", self.open_settings, "#c0c0c0")
        ]:
            tk.Button(self.header, text=text, bg=bg, fg="white" if bg == "#ff0000" else "black",
                      relief="raised", command=cmd).pack(side="right", padx=3, pady=2)

        tk.Label(self.header, text="Calculator", bg=self.top_border_color, fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=8)

        # display (read-only)
        self.display = tk.Entry(self, font=("Consolas", 20), justify="right",
                                bd=2, relief="sunken", bg="#00ff00", fg="black",
                                insertbackground="black", state="readonly")
        self.display.pack(padx=10, pady=(10, 0), fill="x")
        self._set_display("0")

        # buttons frame
        btn_frame = tk.Frame(self, bg="#c0c0c0")
        btn_frame.pack(pady=10)

        # button layout (5 columns: numeric/operators + special buttons)
        buttons = [
            ('7', '8', '9', '/', 'G'),   # G = Graph
            ('4', '5', '6', '*', '$'),   # $ = Currency
            ('1', '2', '3', '-', '🛠'),  # 🛠 = Preferences (wrench)
            ('0', '.', 'C', '+', '')     # last cell reserved for spacing / column-fitting
        ]

        for r, row in enumerate(buttons):
            for c, char in enumerate(row):
                if char == '':
                    continue
                tk.Button(btn_frame, text=char, width=6, height=2,
                          bg="#d9d9d9", fg="black", font=("Segoe UI", 12),
                          relief="raised", activebackground="#e0e0e0",
                          command=lambda ch=char: self._on_button(ch)).grid(row=r, column=c, padx=4, pady=4)

        # Extra bottom buttons:
        # - Place '=' spanning 3 columns (columns 0,1,2 at row 4)
        # - Average at col3 row4
        # - Data Table at col4 row3 (normal size)
        # The layout here ensures '=' is wider horizontally.
        tk.Button(btn_frame, text="=", width=6 * 3, height=2, bg="#d9d9d9", fg="black",
                  font=("Segoe UI", 12), relief="raised", activebackground="#e0e0e0",
                  command=self._evaluate).grid(row=4, column=0, columnspan=3, padx=4, pady=4)
        tk.Button(btn_frame, text="Average", width=6, height=2, bg="#d9d9d9", fg="black",
                  font=("Segoe UI", 12), relief="raised", activebackground="#e0e0e0",
                  command=self._open_average_window).grid(row=4, column=3, padx=4, pady=4)
        tk.Button(btn_frame, text="DT", width=6, height=2, bg="#d9d9d9", fg="black",
                  font=("Segoe UI", 12), relief="raised", activebackground="#e0e0e0",
                  command=self._open_data_table).grid(row=3, column=4, padx=4, pady=4)

    # -------------------- Dragging main window --------------------
    def _start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def _on_move(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.geometry(f"+{x}+{y}")

    # -------------------- Display helpers --------------------
    def _set_display(self, text):
        self.display.config(state="normal")
        self.display.delete(0, tk.END)
        self.display.insert(0, text)
        self.display.config(state="readonly")

    def _reset_display(self):
        self._set_display("0")

    # -------------------- Button handling --------------------
    def _on_button(self, ch):
        if ch == "C":
            self._reset_display()
        elif ch == "$":
            self._open_currency_window()
        elif ch == "G":
            self._open_graph_window()
        elif ch == "🛠":
            self._open_preferences_window()
        else:
            # If the main display currently shows "0", replace it; else append
            cur = self.display.get()
            if cur == "0":
                self._set_display(ch)
            else:
                self._set_display(cur + ch)

    def _evaluate(self):
        expr = self.display.get()
        try:
            # safe-ish eval environment
            result = eval(expr, {"__builtins__": None}, {})
            self.last_results.append((expr, result))
            self._set_display(str(result))
        except Exception:
            self._set_display("Error")
            self.after(1000, self._reset_display)

    # -------------------- Info Window (⋯ top button) --------------------
    def _open_info_window(self):
        win, top = self._create_window(380, 260, "Information")
        frame = tk.Frame(win, bg="#c0c0c0")
        frame.pack(pady=16, padx=14, fill="both", expand=True)

        tk.Label(frame, text=f"Version: {APP_VERSION}", bg="#c0c0c0", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=4)
        tk.Label(frame, text="A feature-rich calculator with utilities and graphing.", bg="#c0c0c0", font=("Segoe UI", 10)).pack(anchor="w", pady=4)
        tk.Label(frame, text="Codebase: Built in Python using Tkinter", bg="#c0c0c0", font=("Segoe UI", 10)).pack(anchor="w", pady=4)
        tk.Label(frame, text=f"Python Version: {platform.python_version()}", bg="#c0c0c0", font=("Segoe UI", 10)).pack(anchor="w", pady=4)
        tk.Label(frame, text="Environment: Made in Visual Studio Code", bg="#c0c0c0", font=("Segoe UI", 10, "italic")).pack(anchor="w", pady=4)

    # -------------------- Data Table --------------------
    def _open_data_table(self):
        win, top = self._create_window(300, 300, "Data Table")
        frame = tk.Frame(win, bg="#c0c0c0")
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        if self.last_results:
            for expr, res in self.last_results[-100:]:  # show last 100 entries at most
                tk.Label(frame, text=f"{expr} = {res}", bg="#c0c0c0", fg="black", font=("Segoe UI", 10)).pack(anchor="w")
        else:
            tk.Label(frame, text="No data available", bg="#c0c0c0", fg="black", font=("Segoe UI", 10)).pack(pady=10)

    # -------------------- Average Window --------------------
    def _open_average_window(self):
        if self.average_window_open:
            return
        self.average_window_open = True
        win, top = self._create_window(420, 240, "Average Number Calculator")
        tk.Label(win, text="Enter numbers separated by commas:", bg="#c0c0c0", font=("Segoe UI", 10)).pack(pady=8)
        entry = tk.Entry(win, width=40)
        entry.pack(pady=4)

        result_label = tk.Label(win, text="", bg="#c0c0c0", font=("Segoe UI", 11))
        result_label.pack(pady=8)

        def calculate_average():
            s = entry.get()
            try:
                numbers = [float(x.strip()) for x in s.split(",") if x.strip() != ""]
                if not numbers:
                    result_label.config(text="No numbers entered")
                    return
                avg = sum(numbers) / len(numbers)
                result_label.config(text=f"Average: {avg}")
                self._set_display(str(avg))
            except Exception:
                result_label.config(text="Invalid input")

        def close_win():
            self.average_window_open = False
            win.destroy()

        tk.Button(win, text="Calculate", bg="#00ff00", fg="black", command=calculate_average).pack(pady=5)
        tk.Button(win, text="Close", bg="#ff0000", fg="white", command=close_win).pack(pady=4)

    # -------------------- Currency Converter --------------------
    def _open_currency_window(self):
        win, top = self._create_window(420, 300, "Money Converter")

        frm = tk.Frame(win, bg="#c0c0c0")
        frm.pack(pady=8)

        tk.Label(frm, text="From:", bg="#c0c0c0").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        from_box = ttk.Combobox(frm, values=CURRENCY_CODES, width=10)
        from_box.grid(row=0, column=1, padx=6, pady=6)
        from_box.set("USD")

        tk.Label(frm, text="To:", bg="#c0c0c0").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        to_box = ttk.Combobox(frm, values=CURRENCY_CODES, width=10)
        to_box.grid(row=1, column=1, padx=6, pady=6)
        to_box.set("EUR")

        tk.Label(frm, text="Amount:", bg="#c0c0c0").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        amt_entry = tk.Entry(frm, width=14)
        amt_entry.grid(row=2, column=1, padx=6, pady=6)
        amt_entry.insert(0, "1")

        res_label = tk.Label(win, text="", bg="#c0c0c0", font=("Segoe UI", 11))
        res_label.pack(pady=8)

        def convert():
            try:
                amount = float(amt_entry.get())
            except Exception:
                res_label.config(text="Invalid amount")
                return

            from_cur = (from_box.get() or "USD").upper()
            to_cur = (to_box.get() or "EUR").upper()
            converted = None

            # try API if available
            if requests:
                try:
                    url = f"https://api.exchangerate.host/convert?from={from_cur}&to={to_cur}&amount={amount}"
                    r = requests.get(url, timeout=6)
                    data = r.json()
                    if isinstance(data, dict) and data.get("success", True) and "result" in data:
                        converted = data["result"]
                except Exception:
                    converted = None

            # fallback if API failed or requests missing
            if converted is None:
                rate_from = FALLBACK_RATES.get(from_cur, FALLBACK_RATES["USD"])
                rate_to = FALLBACK_RATES.get(to_cur, FALLBACK_RATES["USD"])
                converted = amount / rate_from * rate_to

            res_label.config(text=f"{amount} {from_cur} = {converted:.4f} {to_cur}")
            # put rounded result to main display
            try:
                self._set_display(str(round(converted, 4)))
            except Exception:
                pass

        tk.Button(win, text="Convert", bg="#00ff00", fg="black", command=convert).pack(pady=6)

    # -------------------- Graph Window (100x100 grid, clickable) --------------------
    def _open_graph_window(self):
        win, top = self._create_window(520, 520, "Graph Plotter")
        canvas_size = 400
        padding_top = 48  # space for controls
        canvas = tk.Canvas(win, width=canvas_size, height=canvas_size, bg="white")
        canvas.pack(padx=8, pady=(8, 6))

        # controls frame above canvas
        ctrl = tk.Frame(win, bg="#c0c0c0")
        ctrl.place(x=8, y=6)  # place at top-left area

        tk.Label(ctrl, text="X (0-100):", bg="#c0c0c0").grid(row=0, column=0, padx=4)
        x_entry = tk.Entry(ctrl, width=6)
        x_entry.grid(row=0, column=1, padx=4)

        tk.Label(ctrl, text="Y (0-100):", bg="#c0c0c0").grid(row=0, column=2, padx=4)
        y_entry = tk.Entry(ctrl, width=6)
        y_entry.grid(row=0, column=3, padx=4)

        points = set()  # set of (x,y) pairs

        # draw grid lines (100x100 -> draw every cell as 4px)
        cell = canvas_size / 100.0  # float cell size
        # draw faint grid every 5 units for readability
        for i in range(0, 101):
            x = i * cell
            y = i * cell
            color = "#eee" if i % 5 != 0 else "#ddd"
            canvas.create_line(x, 0, x, canvas_size, fill=color)
            canvas.create_line(0, y, canvas_size, y, fill=color)

        def plot_point_from_entries():
            try:
                x = float(x_entry.get())
                y = float(y_entry.get())
                if not (0 <= x <= 100 and 0 <= y <= 100):
                    raise ValueError
            except Exception:
                messagebox.showerror("Invalid", "X and Y must be numbers between 0 and 100.")
                return
            ix = int(round(x))
            iy = int(round(y))
            if (ix, iy) in points:
                return
            if len(points) >= 10000:  # 100x100 maximum unique cells
                messagebox.showwarning("Limit", "Maximum points reached.")
                return
            points.add((ix, iy))
            cx = ix * cell
            cy = (100 - iy) * cell
            # draw small filled rectangle (pixel)
            canvas.create_rectangle(cx, cy, cx + cell, cy + cell, fill="red", outline="")

        def on_canvas_click(event):
            # event.x,event.y for canvas coordinate
            # map to 0..100
            ix = int(event.x // cell)
            iy = int(100 - (event.y // cell))
            if ix < 0 or iy < 0 or ix > 100 or iy > 100:
                return
            if (ix, iy) in points:
                return
            points.add((ix, iy))
            cx = ix * cell
            cy = (100 - iy) * cell
            canvas.create_rectangle(cx, cy, cx + cell, cy + cell, fill="red", outline="")
            # update entries
            x_entry.delete(0, tk.END); x_entry.insert(0, str(ix))
            y_entry.delete(0, tk.END); y_entry.insert(0, str(iy))

        canvas.bind("<Button-1>", on_canvas_click)

        btn_frame = tk.Frame(win, bg="#c0c0c0")
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Plot from entries", bg="#00ff00", fg="black", command=plot_point_from_entries).pack(side="left", padx=6)
        def clear_graph():
            canvas.delete("all")
            points.clear()
            # redraw grid
            for i in range(0, 101):
                x = i * cell
                y = i * cell
                color = "#eee" if i % 5 != 0 else "#ddd"
                canvas.create_line(x, 0, x, canvas_size, fill=color)
                canvas.create_line(0, y, canvas_size, y, fill=color)
        tk.Button(btn_frame, text="Clear", bg="#ff0000", fg="white", command=clear_graph).pack(side="left", padx=6)

        # isolate keyboard input: entries should accept input without main display capturing keys.
        # The global _on_key handler checks event.widget and ignores input when focus is an Entry other than main display.

    # -------------------- Preferences --------------------
    def _open_preferences_window(self):
        win, top = self._create_window(420, 240, "Preferences")
        frame = tk.Frame(win, bg="#c0c0c0")
        frame.pack(pady=10, padx=10)

        tk.Label(frame, text="Window Width:", bg="#c0c0c0").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        width_e = tk.Entry(frame, width=10); width_e.grid(row=0, column=1, padx=6, pady=6); width_e.insert(0, str(self.window_width))

        tk.Label(frame, text="Window Height:", bg="#c0c0c0").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        height_e = tk.Entry(frame, width=10); height_e.grid(row=1, column=1, padx=6, pady=6); height_e.insert(0, str(self.window_height))

        tk.Label(frame, text="Top Border Color:", bg="#c0c0c0").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        color_e = tk.Entry(frame, width=12); color_e.grid(row=2, column=1, padx=6, pady=6); color_e.insert(0, self.top_border_color)

        def pick_color():
            c = colorchooser.askcolor()[1]
            if c:
                color_e.delete(0, tk.END)
                color_e.insert(0, c)

        tk.Button(frame, text="Pick Color", command=pick_color).grid(row=2, column=2, padx=6, pady=6)

        def apply_prefs():
            try:
                w = int(width_e.get())
                h = int(height_e.get())
                c = color_e.get().strip()
                # simple validation for color: must start with '#' and be length 7 or 4 (hex)
                if not (c.startswith("#") and len(c) in (4, 7)):
                    raise ValueError("Bad color")
                self.window_width = w
                self.window_height = h
                self.top_border_color = c
                self._center_window(self.window_width, self.window_height)
                # update main header background immediately
                self.header.config(bg=self.top_border_color)
            except Exception:
                messagebox.showerror("Invalid", "Please enter valid width, height and hex color (e.g. #000080).")

        tk.Button(win, text="Apply", bg="#00ff00", fg="black", command=apply_prefs).pack(pady=8)

    # -------------------- Settings Window --------------------
    def open_settings(self):
        win, top = self._create_window(360, 200, "Settings")
        tk.Label(win, text="Settings", bg="#c0c0c0", font=("Segoe UI", 12, "bold")).pack(pady=8)

        # Clear stored data (calculation history)
        def clear_data():
            if messagebox.askyesno("Clear data", "Clear calculation history?"):
                self.last_results.clear()
                messagebox.showinfo("Cleared", "Calculation history cleared.")

        def full_restart():
            python = sys.executable
            subprocess.Popen([python] + sys.argv)
            self.destroy()

        tk.Button(win, text="Clear Data", bg="#ff9900", fg="black", command=clear_data).pack(pady=6)
        tk.Button(win, text="Refresh (Restart)", bg="#00ff00", fg="black", command=full_restart).pack(pady=6)
        tk.Button(win, text="Open GitHub", bg="#1a1aff", fg="white", command=lambda: webbrowser.open(GITHUB_URL)).pack(pady=6)

    # -------------------- Keyboard handling --------------------
    def _on_key(self, event):
        # If focus is an Entry that's not the main display, ignore to allow typing there
        w = event.widget
        if isinstance(w, tk.Entry) and w is not self.display:
            return

        # avoid keyboard while average window open (we still allow typing in its Entry because we returned above)
        if self.average_window_open:
            return

        key = event.keysym
        if key in ("Return", "KP_Enter"):
            self._evaluate()
        elif key == "BackSpace":
            cur = self.display.get()
            if len(cur) > 1:
                self._set_display(cur[:-1])
            else:
                self._reset_display()
        elif key == "Escape":
            self._reset_display()
        else:
            ch = event.char
            if ch in "0123456789.+-*/":
                cur = self.display.get()
                if cur == "0":
                    self._set_display(ch)
                else:
                    self._set_display(cur + ch)

# -------------------- Run --------------------
if __name__ == "__main__":
    app = Calculator()
    app.mainloop()
