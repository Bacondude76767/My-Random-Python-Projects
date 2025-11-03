import tkinter as tk
from tkinter import ttk
import random
import math
from tkinter import messagebox
from typing import Any
import threading
import time
import tkinter.font as tkfont


class CoinFlipApp:
    # Class-level attribute declarations to help static analyzers / editors
    master: Any = None
    width: Any = None
    height: Any = None
    notebook: Any = None
    tab_flip: Any = None
    tab_settings: Any = None
    tab_achievements: Any = None
    tab_shop: Any = None
    tab_inventory: Any = None
    tab_dev: Any = None
    tab_test: Any = None
    test_win: Any = None
    shop_tab_added: bool = False
    inventory_tab_added: bool = False
    test_tab_added: bool = False
    test_win_added: bool = False
    inventory_owned: bool = False
    inventory_items: Any = None
    inventory_items_frame: Any = None
    inventory_item_labels: Any = None
    item_values: Any = None
    flip_label: Any = None
    rebirth_label: Any = None
    rebirth_counter_label: Any = None
    ach_labels: Any = None
    achievements: Any = None
    dev_code_var: Any = None
    dev_tab_added: bool = False
    dev_ach_vars: Any = None
    dev_item_name_var: Any = None
    dev_item_count_var: Any = None
    fullscreen_var: Any = None
    borderless_var: Any = None
    dev_rebirths_var: Any = None
    dev_flips_var: Any = None
    canvas: Any = None
    instr: Any = None
    oval: Any = None
    text: Any = None
    anim_steps_default: Any = None
    rotations_default: Any = None
    win_editor: Any = None
    win_editor_added: bool = False
    win_width_var: Any = None
    win_height_var: Any = None
    win_color_var: Any = None
    win_bounce_job: Any = None
    win_bouncing: bool = False
    def __init__(self, master):
        self.master = master
        master.title("Coin Flipper")
        master.resizable(False, False)

        self.width = 320
        self.height = 360
        # remember initial size so we can restore when leaving fullscreen
        self.initial_width = self.width
        self.initial_height = self.height

        # Create tabs: Flip, Settings and Achievements
        self.notebook = ttk.Notebook(master)
        self.tab_flip = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_achievements = ttk.Frame(self.notebook)
    # Shop tab exists but is not added until rebirth_count >= 1
        self.tab_shop = ttk.Frame(self.notebook)
        self.shop_tab_added = False
        # Inventory tab (purchased in shop)
        self.tab_inventory = ttk.Frame(self.notebook)
        self.inventory_tab_added = False
        self.inventory_owned = False
        # inventory contents: item name -> count
        self.inventory_items = {}
        # references for inventory UI widgets (populated when inventory tab is revealed)
        self.inventory_items_frame = None
        self.inventory_item_labels = {}
        # values for items (rebirths per unit)
        self.item_values = {
            "Rebirth cube": 5,
        }
        self.notebook.add(self.tab_flip, text="Flip")
        self.notebook.add(self.tab_settings, text="Settings")
        self.notebook.add(self.tab_achievements, text="Achievements")
        self.notebook.pack(fill="both", expand=True)

        # Flip tab UI: flip counter (above the canvas) and the canvas itself
        # initialize counter label (start at 0)
        # rebirth count (initialize before creating rebirth label)
        self.rebirth_count = 0
        self.flip_label = ttk.Label(self.tab_flip, text="Flips: 0")
        self.flip_label.pack(pady=(8, 2))

        # rebirth counter visible on Flip tab
        self.rebirth_counter_label = ttk.Label(self.tab_flip, text=f"Rebirths: {self.rebirth_count}")
        self.rebirth_counter_label.pack(pady=(0, 6))

        # Canvas lives in the Flip tab
        self.canvas = tk.Canvas(self.tab_flip, width=self.width, height=self.height, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack()

        # keep canvas responsive to window size changes (used for fullscreen)
        try:
            self.master.bind('<Configure>', lambda e: self._on_window_configure(e))
        except Exception:
            pass

        # Draw coin (circle) and text
        pad = 30
        self.pad = pad
        # available area for the coin: from pad .. (height - 120 - pad)
        available_width = self.width - 2 * pad
        available_height = (self.height - 120) - 2 * pad
        diameter = min(available_width, available_height)
        radius = diameter / 2
        cx = self.width / 2
        cy = pad + available_height / 2
        # store center & base radius for consistent scaling
        self.cx = cx
        self.cy = cy
        self.base_radius = radius
        x0 = cx - radius
        y0 = cy - radius
        x1 = cx + radius
        y1 = cy + radius
        self.oval = self.canvas.create_oval(x0, y0, x1, y1, fill="#E6B800", outline="#c68f00", width=4)
        self.text = self.canvas.create_text(cx, cy, text="Heads", font=("Arial", 28, "bold"), fill="#222")
        # instruction text
        self.instr = self.canvas.create_text(self.width // 2, self.height - 60,
                                             text="Press Enter to flip the coin", font=("Arial", 12), fill="#333")

        self.animating = False
        master.bind("<Return>", self.start_flip)

        # Default animation settings (background-only settings kept)
        self.base_frame_delay = 50        # ms per frame (base, adjusted by rebirths)
        self.anim_steps_default = 24 # default number of frames per flip
        self.rotations_default = 3   # default rotations during flip
    # force_mode removed — flips are always random

        # Achievements state
        self.flip_count = 0
        # achievements mapping name -> earned(bool) -- order matters for display
        self.achievements = {
            "1st Coin Flip": False,
            "5th Coin Flip": False,
            "20th Coin Flip": False,
            "50th Coin Flip": False,
            "100th Coin Flip": False,
            "Visited everything": False,
            "I Like Heads": False,
        }
        self.ach_labels = {}

        # track visited tabs for the "Visited everything" achievement
        self.visited_tabs = set()
        self.all_tabs = {"Flip", "Settings", "Achievements"}
        # track consecutive heads for the "I Like Heads" achievement
        self.consec_heads = 0

        # Settings variables (only background is exposed)
        self.bg_var = tk.StringVar(value="white")
        # Developer unlock code (hidden tab)
        self.dev_code_var = tk.StringVar(value="")
        self.dev_tab_added = False
        # Window options
        self.fullscreen_var = tk.BooleanVar(value=False)
        self.borderless_var = tk.BooleanVar(value=False)
    # force_var removed — flips are always random

        # Build settings UI
        self._build_settings_ui()

        # Build achievements UI
        self._build_achievements_ui()

        # Bind notebook tab change to track visits
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        # mark the initially visible tab as visited
        self._on_tab_changed()

        # print welcome message to console when app opens
        try:
            print("Welcome to coin flipping simulator! This is a game that i try to cram as much things as possible! go through the levels and have fun!")
        except Exception:
            pass

        # ensure we print a message when the window is closed
        try:
            master.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass

    def _build_settings_ui(self):
        # Background color options
        frm_bg = ttk.LabelFrame(self.tab_settings, text="Background")
        frm_bg.pack(fill="x", padx=10, pady=8)
        rb_white = ttk.Radiobutton(frm_bg, text="White", variable=self.bg_var, value="white", command=self._apply_bg)
        rb_black = ttk.Radiobutton(frm_bg, text="Black", variable=self.bg_var, value="black", command=self._apply_bg)
        rb_white.pack(side="left", padx=8, pady=6)
        rb_black.pack(side="left", padx=8, pady=6)

        # SDN code unlock (enter SDN code to reveal SDN tab)
        frm_dev = ttk.LabelFrame(self.tab_settings, text="SDN")
        frm_dev.pack(fill="x", padx=10, pady=8)
        lbl_dev = ttk.Label(frm_dev, text="SDN Code:")
        lbl_dev.pack(side="left", padx=(6, 4))
        ent_dev = ttk.Entry(frm_dev, textvariable=self.dev_code_var, width=28)
        ent_dev.pack(side="left", padx=(0, 6))
        btn_dev = ttk.Button(frm_dev, text="Unlock SDN Tab", command=self._try_dev_code)
        btn_dev.pack(side="left")

        # Window options (fullscreen / borderless)
        frm_win = ttk.LabelFrame(self.tab_settings, text="Window")
        frm_win.pack(fill="x", padx=10, pady=8)
        cb_full = ttk.Checkbutton(frm_win, text="Fullscreen", variable=self.fullscreen_var, command=self._toggle_fullscreen)
        cb_border = ttk.Checkbutton(frm_win, text="Borderless (no titlebar)", variable=self.borderless_var, command=self._toggle_borderless)
        cb_full.pack(side="left", padx=8, pady=6)
        cb_border.pack(side="left", padx=8, pady=6)

    # (Force result UI removed — flips are always random)

        # Apply current bg at startup
        self._apply_bg()

    def _build_achievements_ui(self):
        frm = ttk.LabelFrame(self.tab_achievements, text="Achievements")
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        for name, earned in self.achievements.items():
            lbl_text = ("✓ " + name) if earned else ("🔒 " + name)
            lbl = tk.Label(frm, text=lbl_text, anchor="w")
            lbl.pack(fill="x", padx=8, pady=6)
            # style locked items as gray
            if earned:
                lbl.configure(fg="#0a0")
            else:
                lbl.configure(fg="#666")
            self.ach_labels[name] = lbl

        # Rebirth area (hidden until all achievements earned)
        self.rebirth_frame = ttk.Frame(self.tab_achievements)
        self.rebirth_label = ttk.Label(self.rebirth_frame, text=f"Rebirths: {self.rebirth_count}")
        self.rebirth_btn = ttk.Button(self.rebirth_frame, text="Rebirth", command=self._do_rebirth)
        self.rebirth_label.pack(side="left", padx=(4, 12))
        self.rebirth_btn.pack(side="left")

        # Show the rebirth button only if all achievements already earned
        if all(self.achievements.values()):
            self.rebirth_frame.pack(pady=8)


    def _on_tab_changed(self, event=None):
        # called when the notebook tab changes; record the visited tab
        try:
            tab_id = self.notebook.select()
            tab_text = self.notebook.tab(tab_id, "text")
        except Exception:
            return
        self.visited_tabs.add(tab_text)
        # award if all visited
        if self.visited_tabs >= self.all_tabs:
            self.award_achievement("Visited everything")

    def award_achievement(self, name: str):
        # mark earned and update UI; show popup
        if name not in self.achievements:
            return
        if self.achievements[name]:
            return
        self.achievements[name] = True
        lbl = self.ach_labels.get(name)
        if lbl:
            lbl.configure(text="✓ " + name, fg="#0a0")
        # show popup notification for 3 seconds
        self._show_achievement_popup(name)
        # if now all achievements are earned, reveal the rebirth button
        try:
            if all(self.achievements.values()):
                # show rebirth frame if not already visible
                if not self.rebirth_frame.winfo_ismapped():
                    self.rebirth_frame.pack(pady=8)
        except Exception:
            pass

    def _show_achievement_popup(self, name: str):
        # small borderless top-level window centered over the main window
        top = tk.Toplevel(self.master)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        msg = tk.Label(top, text=f"New Achievement:\n{name}", font=("Arial", 14, "bold"), bg="#222", fg="#fff")
        msg.pack(padx=12, pady=12)
        # position it centered over the main window
        self.master.update_idletasks()
        mw = self.master.winfo_width()
        mh = self.master.winfo_height()
        mx = self.master.winfo_rootx()
        my = self.master.winfo_rooty()
        top.update_idletasks()
        tw = top.winfo_width()
        th = top.winfo_height()
        x = mx + (mw - tw) // 2
        y = my + (mh - th) // 2
        top.geometry(f"{tw}x{th}+{x}+{y}")
        # destroy after 3 seconds
        top.after(3000, top.destroy)

    def _get_effective_frame_delay(self):
        """Return the effective frame delay in ms after applying rebirth speed multiplier.

        Uses the configured base frame delay and divides it by 2^rebirth_count.
        Clamps to minimum 5 ms to avoid zero/negative delays.
        """
        try:
            base = int(self.base_frame_delay)
        except Exception:
            base = 50
        factor = 2 ** self.rebirth_count if self.rebirth_count > 0 else 1
        eff = max(5, int(base / factor))
        return eff

    def _update_rebirth_ui(self):
        """Update all rebirth display widgets to match current rebirth_count."""
        try:
            if hasattr(self, 'rebirth_label'):
                try:
                    self.rebirth_label.configure(text=f"Rebirths: {self.rebirth_count}")
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if hasattr(self, 'rebirth_counter_label'):
                try:
                    self.rebirth_counter_label.configure(text=f"Rebirths: {self.rebirth_count}")
                except Exception:
                    pass
        except Exception:
            pass

    def _do_rebirth(self):
        """Reset achievements/counters and increase rebirth count (which speeds up flips)."""
        # increment rebirth counter
        self.rebirth_count += 1
        # update rebirth displays
        try:
            self._update_rebirth_ui()
        except Exception:
            pass

        # reset achievements state and UI
        for name in list(self.achievements.keys()):
            self.achievements[name] = False
            lbl = self.ach_labels.get(name)
            if lbl:
                lbl.configure(text=("🔒 " + name), fg="#666")

        # hide rebirth button until achievements are earned again
        try:
            if self.rebirth_frame.winfo_ismapped():
                self.rebirth_frame.pack_forget()
        except Exception:
            pass

        # reset counters and UI
        self.flip_count = 0
        try:
            self.flip_label.configure(text=f"Flips: {self.flip_count}")
        except Exception:
            pass
        self.consec_heads = 0
        self.visited_tabs = set()

        # update internal frame_delay using new rebirth multiplier
        self.frame_delay = self._get_effective_frame_delay()

        # if player has reached 5 rebirths, reveal the Shop tab
        try:
            if self.rebirth_count >= 1:
                self._reveal_shop_tab()
        except Exception:
            pass

    def _apply_bg(self):
        # map selection to actual color
        val = self.bg_var.get()
        if val == "black":
            col = "#000000"
            text_col = "#fff"
        else:
            col = "#ffffff"
            text_col = "#222"
        self.canvas.configure(bg=col)
        # update instruction text color for readability
        self.canvas.itemconfigure(self.instr, fill=text_col)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode on the main window."""
        try:
            val = bool(self.fullscreen_var.get())
            # use tkinter attribute for fullscreen
            try:
                self.master.attributes("-fullscreen", val)
            except Exception:
                # fallback: maximize if attributes unsupported
                if val:
                    try:
                        self.master.state('zoomed')
                    except Exception:
                        pass
                else:
                    try:
                        self.master.state('normal')
                    except Exception:
                        pass
            self.master.update_idletasks()
            # reflow layout so the coin scales to the new size
            try:
                self._reflow_layout()
            except Exception:
                pass
        except Exception:
            pass

    def _toggle_borderless(self):
        """Toggle borderless (titlebar/decorations) on the main window.

        Note: on some platforms removing decorations also affects window controls; use Alt+F4 to close if necessary.
        """
        try:
            val = bool(self.borderless_var.get())
            try:
                self.master.overrideredirect(val)
            except Exception:
                pass
            # ensure window layout refresh
            try:
                self.master.update_idletasks()
            except Exception:
                pass
            try:
                # also reflow in case decorations changed available space
                self._reflow_layout()
            except Exception:
                pass
        except Exception:
            pass

    def _on_window_configure(self, event=None):
        """Handler for window configure events; reflows layout when size changes.

        This keeps the coin scaled to the visible canvas when the window is resized or when entering fullscreen.
        """
        try:
            # only adjust while fullscreen or when the window size actually changed
            if getattr(self, 'fullscreen_var', None) and self.fullscreen_var.get():
                self._reflow_layout()
        except Exception:
            pass

    def _reflow_layout(self):
        """Recompute canvas and coin geometry to fit the current window size.

        When in fullscreen, expand the canvas to fill available window space and scale the coin accordingly.
        When not fullscreen, revert to the initial design size.
        """
        try:
            # determine target canvas size
            is_full = getattr(self, 'fullscreen_var', None) and self.fullscreen_var.get()
            if is_full:
                mw = max(200, self.master.winfo_width())
                mh = max(200, self.master.winfo_height())
                # leave some space for tabs/other UI; keep the coin area slightly smaller than full window
                new_w = mw - 40
                new_h = mh - 140
            else:
                new_w = getattr(self, 'initial_width', 320)
                new_h = getattr(self, 'initial_height', 360)

            # apply new canvas size
            self.width = max(200, int(new_w))
            self.height = max(200, int(new_h))
            try:
                self.canvas.config(width=self.width, height=self.height)
            except Exception:
                pass

            # recompute coin geometry (reuse pad)
            pad = getattr(self, 'pad', 30)
            available_width = self.width - 2 * pad
            available_height = (self.height - 120) - 2 * pad
            diameter = min(max(20, available_width), max(20, available_height))
            radius = diameter / 2
            cx = self.width / 2
            cy = pad + max(0, available_height) / 2
            self.cx = cx
            self.cy = cy
            self.base_radius = radius

            # update oval and text positions/sizes
            x0 = cx - radius
            y0 = cy - radius
            x1 = cx + radius
            y1 = cy + radius
            try:
                self.canvas.coords(self.oval, x0, y0, x1, y1)
            except Exception:
                pass
            try:
                self.canvas.coords(self.text, self.cx, self.cy)
            except Exception:
                pass
            try:
                self.canvas.coords(self.instr, self.width // 2, self.height - 60)
            except Exception:
                pass

            # ensure we show a full coin after reflow
            try:
                self._set_coin_ellipse(1.0, 1.0)
            except Exception:
                pass
        except Exception:
            pass

    def _reveal_shop_tab(self):
        """Add the Shop tab to the notebook (placeholder) the first time it's unlocked."""
        if getattr(self, 'shop_tab_added', False):
            return
        try:
            self.notebook.add(self.tab_shop, text="Shop")
            # build simple shop UI with one item: Inventory (cost 5 rebirths)
            frm = ttk.LabelFrame(self.tab_shop, text="Items")
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            lbl = ttk.Label(frm, text="Inventory — Cost: 5 rebirths", padding=8)
            lbl.pack(anchor="w", padx=8, pady=(6, 2))
            # buy button
            self.buy_inventory_btn = ttk.Button(frm, text="Buy Inventory (5)", command=self._buy_inventory)
            self.buy_inventory_btn.pack(anchor="w", padx=8, pady=(0, 8))
            # if already owned, disable button and reveal inventory
            if getattr(self, 'inventory_owned', False):
                try:
                    self.buy_inventory_btn.configure(text="Inventory (Owned)", state="disabled")
                    self._reveal_inventory_tab()
                except Exception:
                    pass
            self.shop_tab_added = True
        except Exception:
            pass

    def _buy_inventory(self):
        """Purchase the Inventory if the player has enough rebirths (cost 5)."""
        try:
            if getattr(self, 'inventory_owned', False):
                return
            cost = 5
            if self.rebirth_count < cost:
                try:
                    messagebox.showwarning("Shop", "Not enough rebirths to buy Inventory.")
                except Exception:
                    pass
                return
            # deduct cost
            self.rebirth_count -= cost
            try:
                self._update_rebirth_ui()
            except Exception:
                pass
            # mark owned and update UI
            self.inventory_owned = True
            try:
                self.buy_inventory_btn.configure(text="Inventory (Owned)", state="disabled")
            except Exception:
                pass
            # reveal inventory tab
            self._reveal_inventory_tab()
        except Exception:
            pass

    def _reveal_inventory_tab(self):
        """Add the Inventory tab (initially empty) if not already added."""
        if getattr(self, 'inventory_tab_added', False):
            return
        try:
            self.notebook.add(self.tab_inventory, text="Inventory")
            # build inventory UI: a frame listing items and sell buttons
            frm = ttk.LabelFrame(self.tab_inventory, text="Inventory")
            frm.pack(fill="both", expand=True, padx=10, pady=10)
            self.inventory_items_frame = frm
            # populate current items (will show 'empty' if none)
            self._update_inventory_ui()
            self.inventory_tab_added = True
        except Exception:
            pass

    def _update_inventory_ui(self):
        """Refresh the inventory tab UI to reflect current items and counts."""
        try:
            frm = self.inventory_items_frame
            if frm is None:
                return
            # clear existing children
            for child in list(frm.winfo_children()):
                child.destroy()

            if not self.inventory_items:
                lbl = ttk.Label(frm, text="Inventory is empty.", padding=12)
                lbl.pack(padx=10, pady=10)
                return

            # For each item, show name, count, and sell button where applicable
            for name, count in list(self.inventory_items.items()):
                row = ttk.Frame(frm)
                row.pack(fill="x", padx=8, pady=6)
                lbl = ttk.Label(row, text=f"{name}: {count}")
                lbl.pack(side="left")
                self.inventory_item_labels[name] = lbl
                # selling behavior depends on item value
                val = self.item_values.get(name, 0)
                if val > 0:
                    # Sell One
                    btn_one = ttk.Button(row, text=f"Sell One ({val}R)", command=lambda n=name: self._sell_item(n, 1))
                    btn_one.pack(side="right", padx=(4,0))
                    # Sell All
                    btn_all = ttk.Button(row, text=f"Sell All ({val}R ea)", command=lambda n=name: self._sell_all(n))
                    btn_all.pack(side="right")
                else:
                    # not sellable
                    lbl_ns = ttk.Label(row, text="(not sellable)")
                    lbl_ns.pack(side="right")
        except Exception:
            pass

    def _show_item_popup(self, name: str):
        """Brief popup to show when an item is found."""
        try:
            top = tk.Toplevel(self.master)
            top.overrideredirect(True)
            top.attributes("-topmost", True)
            msg = tk.Label(top, text=f"Found: {name}", font=("Arial", 12, "bold"), bg="#222", fg="#fff")
            msg.pack(padx=8, pady=8)
            # center
            self.master.update_idletasks()
            mw = self.master.winfo_width()
            mh = self.master.winfo_height()
            mx = self.master.winfo_rootx()
            my = self.master.winfo_rooty()
            top.update_idletasks()
            tw = top.winfo_width()
            th = top.winfo_height()
            x = mx + (mw - tw) // 2
            y = my + (mh - th) // 2
            top.geometry(f"{tw}x{th}+{x}+{y}")
            top.after(2000, top.destroy)
        except Exception:
            try:
                messagebox.showinfo("Item", f"Found: {name}")
            except Exception:
                pass

    def _sell_rebirth_cube(self, item_name: str):
        """Sell one Rebirth cube for 5 rebirths if available."""
        try:
            # delegate to generic sell handler (1 unit)
            self._sell_item(item_name, 1)
        except Exception:
            pass

    def _sell_item(self, item_name: str, qty: int):
        """Generic seller: remove qty units of item_name and award rebirths based on item_values."""
        try:
            if qty <= 0:
                return
            cnt = self.inventory_items.get(item_name, 0)
            if cnt <= 0:
                try:
                    messagebox.showwarning("Inventory", f"No {item_name} to sell.")
                except Exception:
                    pass
                return
            to_sell = min(qty, cnt)
            # compute value
            val = self.item_values.get(item_name, 0)
            if val <= 0:
                try:
                    messagebox.showwarning("Inventory", f"{item_name} is not sellable.")
                except Exception:
                    pass
                return
            # remove
            remaining = cnt - to_sell
            if remaining > 0:
                self.inventory_items[item_name] = remaining
            else:
                del self.inventory_items[item_name]
            # award rebirths
            gained = to_sell * val
            self.rebirth_count += gained
            try:
                self._update_rebirth_ui()
            except Exception:
                pass
            # update UI
            try:
                self._update_inventory_ui()
            except Exception:
                pass
            # reveal shop if threshold reached
            try:
                if self.rebirth_count >= 1:
                    self._reveal_shop_tab()
            except Exception:
                pass
        except Exception:
            pass

    def _sell_all(self, item_name: str):
        """Sell all units of the given item for rebirths."""
        try:
            cnt = self.inventory_items.get(item_name, 0)
            if cnt <= 0:
                try:
                    messagebox.showwarning("Inventory", f"No {item_name} to sell.")
                except Exception:
                    pass
                return
            self._sell_item(item_name, cnt)
        except Exception:
            pass

    def _on_close(self):
        # print closing note and then destroy the main window
        try:
            print("This dosnt save by the way sorry")
        except Exception:
            pass
        try:
            self.master.destroy()
        except Exception:
            try:
                self.master.quit()
            except Exception:
                pass

    def _try_dev_code(self):
        code = (self.dev_code_var.get() or "").strip()
        if code == "Kendall07232012!":
            if not getattr(self, 'dev_tab_added', False):
                self._add_dev_tab()
            try:
                messagebox.showinfo("SDN", "SDN tab unlocked.")
            except Exception:
                pass
        else:
            try:
                messagebox.showerror("SDN", "Invalid SDN code.")
            except Exception:
                pass

    def _add_dev_tab(self):
        if getattr(self, 'dev_tab_added', False):
            return
        try:
            self.tab_dev = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_dev, text="SDN")
            self.dev_tab_added = True

            # Achievements granting
            frm_ach = ttk.LabelFrame(self.tab_dev, text="Grant Achievements")
            frm_ach.pack(fill="x", padx=10, pady=8)
            self.dev_ach_vars = {}
            for name in self.achievements.keys():
                var = tk.BooleanVar(value=False)
                cb = ttk.Checkbutton(frm_ach, text=name, variable=var)
                cb.pack(anchor="w", padx=6, pady=2)
                self.dev_ach_vars[name] = var
            btn_grant = ttk.Button(frm_ach, text="Grant Selected", command=self._grant_selected_achievements)
            btn_grant.pack(padx=6, pady=(4,8))

            # Items (SDN): give arbitrary items
            frm_items = ttk.LabelFrame(self.tab_dev, text="Items")
            frm_items.pack(fill="x", padx=10, pady=8)
            lbl_item_name = ttk.Label(frm_items, text="Item name:")
            lbl_item_name.pack(side="left", padx=(6,4))
            self.dev_item_name_var = tk.StringVar(value="Rebirth cube")
            ent_item_name = ttk.Entry(frm_items, textvariable=self.dev_item_name_var, width=20)
            ent_item_name.pack(side="left", padx=(0,6))
            lbl_item_count = ttk.Label(frm_items, text="Count:")
            lbl_item_count.pack(side="left", padx=(6,4))
            self.dev_item_count_var = tk.IntVar(value=1)
            ent_item_count = ttk.Entry(frm_items, textvariable=self.dev_item_count_var, width=6)
            ent_item_count.pack(side="left", padx=(0,6))
            btn_give_item = ttk.Button(frm_items, text="Give Item(s)", command=self._dev_give_item)
            btn_give_item.pack(side="left", padx=(6,0))

            # Rebirths
            frm_reb = ttk.LabelFrame(self.tab_dev, text="Give Rebirths")
            frm_reb.pack(fill="x", padx=10, pady=8)
            self.dev_rebirths_var = tk.IntVar(value=0)
            ent_reb = ttk.Entry(frm_reb, textvariable=self.dev_rebirths_var, width=8)
            ent_reb.pack(side="left", padx=6)
            btn_reb = ttk.Button(frm_reb, text="Add Rebirths", command=self._dev_add_rebirths)
            btn_reb.pack(side="left", padx=6)

            # Flips
            frm_flips = ttk.LabelFrame(self.tab_dev, text="Give Flips")
            frm_flips.pack(fill="x", padx=10, pady=8)
            self.dev_flips_var = tk.IntVar(value=0)
            ent_flips = ttk.Entry(frm_flips, textvariable=self.dev_flips_var, width=8)
            ent_flips.pack(side="left", padx=6)
            btn_flips = ttk.Button(frm_flips, text="Add Flips", command=self._dev_add_flips)
            btn_flips.pack(side="left", padx=6)

            # Revoke area (SDN-only): wipe all progress
            frm_rev = ttk.LabelFrame(self.tab_dev, text="Revoke")
            frm_rev.pack(fill="x", padx=10, pady=8)
            btn_revoke = ttk.Button(frm_rev, text="Revoke All (reset everything)", command=self._revoke_all)
            btn_revoke.pack(padx=6, pady=6)

            # Test window (dev-only): quick access to popups and animations for testing
            try:
                # create a separate Toplevel window instead of a notebook tab
                self.test_win = tk.Toplevel(self.master)
                self.test_win.title("Test")
                self.test_win.transient(self.master)
                # when closed, clear the flag
                def _on_test_close():
                    try:
                        self.test_win.destroy()
                    except Exception:
                        pass
                    try:
                        self.test_win_added = False
                    except Exception:
                        pass
                try:
                    self.test_win.protocol("WM_DELETE_WINDOW", _on_test_close)
                except Exception:
                    pass
                self.test_win_added = True
                frm_test = ttk.LabelFrame(self.test_win, text="Animations & Tests")
                frm_test.pack(fill="both", expand=True, padx=10, pady=10)
                # Achievement popups
                lbl = ttk.Label(frm_test, text="Show Achievement Popup:", padding=6)
                lbl.pack(anchor="w", padx=6, pady=(4,2))
                for name in self.achievements.keys():
                    btn = ttk.Button(frm_test, text=name, command=lambda n=name: self._show_achievement_popup(n))
                    btn.pack(fill="x", padx=8, pady=2)

                # Other quick tests
                ttk.Separator(frm_test).pack(fill="x", pady=6)
                btn_flip = ttk.Button(frm_test, text="Simulate Coin Flip (animation)", command=lambda: self.start_flip())
                btn_flip.pack(fill="x", padx=8, pady=4)
                btn_item = ttk.Button(frm_test, text="Show Item Popup (Rebirth cube)", command=lambda: self._show_item_popup('Rebirth cube'))
                btn_item.pack(fill="x", padx=8, pady=4)
                btn_reflow = ttk.Button(frm_test, text="Reflow Layout (resize coin)", command=lambda: self._reflow_layout())
                btn_reflow.pack(fill="x", padx=8, pady=4)
                # open the Window Editor automatically for SDN users
                try:
                    self._open_window_editor()
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

    def _grant_selected_achievements(self):
        for name, var in getattr(self, 'dev_ach_vars', {}).items():
            try:
                if var.get():
                    # award (award_achievement is safe if already earned)
                    self.award_achievement(name)
            except Exception:
                pass

    def _dev_give_item(self):
        """Dev helper: give the player an arbitrary item and count."""
        try:
            name = (self.dev_item_name_var.get() or "").strip()
            if not name:
                try:
                    messagebox.showerror("SDN", "Enter an item name.")
                except Exception:
                    pass
                return
            try:
                cnt = int(self.dev_item_count_var.get())
            except Exception:
                try:
                    messagebox.showerror("SDN", "Invalid item count.")
                except Exception:
                    pass
                return
            if cnt <= 0:
                try:
                    messagebox.showerror("SDN", "Count must be positive.")
                except Exception:
                    pass
                return
            # add to inventory
            self.inventory_items[name] = self.inventory_items.get(name, 0) + cnt
            # ensure inventory is available to view/sell
            self.inventory_owned = True
            try:
                self._reveal_inventory_tab()
            except Exception:
                pass
            try:
                self._update_inventory_ui()
            except Exception:
                pass
            try:
                messagebox.showinfo("SDN", f"Added {cnt} x {name} to inventory.")
            except Exception:
                pass
        except Exception:
            pass

    def _dev_add_rebirths(self):
        try:
            n = int(self.dev_rebirths_var.get())
        except Exception:
            return
        if n <= 0:
            return
        self.rebirth_count += n
        try:
            self._update_rebirth_ui()
        except Exception:
            pass
        if self.rebirth_count >= 1:
            self._reveal_shop_tab()
        # update frame delay
        self.frame_delay = self._get_effective_frame_delay()

    def _dev_add_flips(self):
        try:
            n = int(self.dev_flips_var.get())
        except Exception:
            return
        if n <= 0:
            return
        prev = self.flip_count
        self.flip_count += n
        try:
            self.flip_label.configure(text=f"Flips: {self.flip_count}")
        except Exception:
            pass
        # award milestone achievements if crossed
        for milestone, name in ((1, "1st Coin Flip"), (5, "5th Coin Flip"), (20, "20th Coin Flip"), (50, "50th Coin Flip"), (100, "100th Coin Flip")):
            if prev < milestone <= self.flip_count:
                self.award_achievement(name)

    def _revoke_all(self):
        """Revoke all progress: confirmation, then reset achievements, flips, rebirths, visited tabs,
        hide shop tab and remove Dev tab. This button is available only in Dev mode."""
        try:
            ok = messagebox.askyesno("Revoke All", "This will reset achievements, flips, rebirths, and hide SDN/Shop tabs. Continue?")
        except Exception:
            # If messagebox fails for some reason, require a simple confirmation prompt via dialog
            ok = True
        if not ok:
            return

        # Reset achievements and UI
        for name in list(self.achievements.keys()):
            self.achievements[name] = False
            lbl = self.ach_labels.get(name)
            if lbl:
                lbl.configure(text=("🔒 " + name), fg="#666")

        # Reset counts and UI labels
        self.flip_count = 0
        try:
            self.flip_label.configure(text=f"Flips: {self.flip_count}")
        except Exception:
            pass
        self.consec_heads = 0
        self.visited_tabs = set()

        self.rebirth_count = 0
        try:
            self._update_rebirth_ui()
        except Exception:
            pass

        # hide rebirth frame
        try:
            if self.rebirth_frame.winfo_ismapped():
                self.rebirth_frame.pack_forget()
        except Exception:
            pass

        # remove Shop tab if present
        try:
            if getattr(self, 'shop_tab_added', False):
                # notebook.forget requires the tab widget
                self.notebook.forget(self.tab_shop)
                self.shop_tab_added = False
        except Exception:
            pass

        # remove Inventory tab if present and reset ownership
        try:
            if getattr(self, 'inventory_tab_added', False):
                self.notebook.forget(self.tab_inventory)
                self.inventory_tab_added = False
            # reset owned flag
            if getattr(self, 'inventory_owned', False):
                self.inventory_owned = False
            # clear stored items
            try:
                self.inventory_items = {}
            except Exception:
                pass
        except Exception:
            pass

        # Additional cleanup: ensure all non-core tabs are removed and internal state reset
        try:
            # remove any notebook tabs that aren't the core three
            for tab_id in list(self.notebook.tabs()):
                try:
                    txt = self.notebook.tab(tab_id, 'text')
                except Exception:
                    continue
                if txt not in ("Flip", "Settings", "Achievements"):
                    try:
                        self.notebook.forget(tab_id)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            # reset flip/rebirth counters & UI
            self.flip_count = 0
            try:
                self.flip_label.configure(text=f"Flips: {self.flip_count}")
            except Exception:
                pass
            self.rebirth_count = 0
            try:
                self._update_rebirth_ui()
            except Exception:
                pass
            self.consec_heads = 0
            self.visited_tabs = set()

            # clear inventory and related flags
            try:
                self.inventory_items = {}
            except Exception:
                pass
            try:
                self.inventory_owned = False
            except Exception:
                pass
            try:
                self.inventory_tab_added = False
            except Exception:
                pass
            try:
                self.shop_tab_added = False
            except Exception:
                pass

            # cancel and remove window editor if present
            try:
                if getattr(self, 'win_bounce_job', None):
                    try:
                        self.master.after_cancel(self.win_bounce_job)
                    except Exception:
                        pass
                    self.win_bounce_job = None
            except Exception:
                pass
            try:
                if getattr(self, 'win_editor_added', False):
                    try:
                        self._close_window_editor()
                    except Exception:
                        pass
                    self.win_editor_added = False
            except Exception:
                pass

            # ensure SDN/dev tab state is cleared
            try:
                self.dev_tab_added = False
            except Exception:
                pass
            try:
                self.dev_code_var.set("")
            except Exception:
                pass

            # select the Flip tab
            try:
                for tid in self.notebook.tabs():
                    try:
                        if self.notebook.tab(tid, 'text') == 'Flip':
                            self.notebook.select(tid)
                            break
                    except Exception:
                        pass
            except Exception:
                pass

        except Exception:
            pass

        try:
            messagebox.showinfo("Revoke", "Thank you for using SDN")
        except Exception:
            pass

    # Window Editor: Toplevel allowing manual window size/color/animation/bounce controls
    def _open_window_editor(self):
        if getattr(self, 'win_editor_added', False):
            return
        try:
            self.win_editor = tk.Toplevel(self.master)
            self.win_editor.title("Window Editor")
            self.win_editor.transient(self.master)

            def _on_close():
                try:
                    self._close_window_editor()
                except Exception:
                    pass

            try:
                self.win_editor.protocol("WM_DELETE_WINDOW", _on_close)
            except Exception:
                pass

            # variables
            self.win_width_var = tk.IntVar(value=getattr(self, 'initial_width', 320))
            self.win_height_var = tk.IntVar(value=getattr(self, 'initial_height', 360))
            self.win_color_var = tk.StringVar(value=self.bg_var.get() if hasattr(self, 'bg_var') else 'white')
            self.win_anim_speed_var = tk.IntVar(value=getattr(self, 'base_frame_delay', 50))
            self.win_anim_steps_var = tk.IntVar(value=getattr(self, 'anim_steps_default', 24))

            frm_size = ttk.LabelFrame(self.win_editor, text="Size")
            frm_size.pack(fill="x", padx=8, pady=6)
            lbl_w = ttk.Label(frm_size, text="Width:")
            lbl_w.pack(side="left", padx=(6,4))
            ent_w = ttk.Entry(frm_size, textvariable=self.win_width_var, width=8)
            ent_w.pack(side="left", padx=(0,6))
            lbl_h = ttk.Label(frm_size, text="Height:")
            lbl_h.pack(side="left", padx=(6,4))
            ent_h = ttk.Entry(frm_size, textvariable=self.win_height_var, width=8)
            ent_h.pack(side="left", padx=(0,6))
            btn_apply_size = ttk.Button(frm_size, text="Apply Size", command=self._apply_window_size)
            btn_apply_size.pack(side="left", padx=6)

            frm_color = ttk.LabelFrame(self.win_editor, text="Background Color")
            frm_color.pack(fill="x", padx=8, pady=6)
            for col in ("white", "black", "#E6B800", "#cfcfcf"):
                r = ttk.Radiobutton(frm_color, text=col, variable=self.win_color_var, value=col)
                r.pack(side="left", padx=6, pady=4)
            btn_apply_color = ttk.Button(frm_color, text="Apply Color", command=self._apply_window_color)
            btn_apply_color.pack(side="left", padx=6)

            frm_anim = ttk.LabelFrame(self.win_editor, text="Animation")
            frm_anim.pack(fill="x", padx=8, pady=6)
            lbl_speed = ttk.Label(frm_anim, text="Frame delay (ms):")
            lbl_speed.pack(side="left", padx=(6,4))
            ent_speed = ttk.Entry(frm_anim, textvariable=self.win_anim_speed_var, width=6)
            ent_speed.pack(side="left", padx=(0,6))
            lbl_steps = ttk.Label(frm_anim, text="Frames:")
            lbl_steps.pack(side="left", padx=(6,4))
            ent_steps = ttk.Entry(frm_anim, textvariable=self.win_anim_steps_var, width=6)
            ent_steps.pack(side="left", padx=(0,6))
            btn_apply_anim = ttk.Button(frm_anim, text="Apply Animation", command=self._apply_anim_settings)
            btn_apply_anim.pack(side="left", padx=6)

            # Bounce control removed per user request (feature kept internally)

            # internal bounce state
            self.win_bouncing = False
            self.win_bounce_job = None
            self._bounce_dx = 8
            self._bounce_dy = 6

            self.win_editor_added = True
        except Exception:
            pass

    def _close_window_editor(self):
        try:
            if getattr(self, 'win_bounce_job', None):
                try:
                    self.master.after_cancel(self.win_bounce_job)
                except Exception:
                    pass
                self.win_bounce_job = None
            if getattr(self, 'win_editor', None):
                try:
                    self.win_editor.destroy()
                except Exception:
                    pass
            self.win_editor_added = False
        except Exception:
            pass

    def _apply_window_size(self):
        try:
            w = max(200, int(self.win_width_var.get()))
            h = max(200, int(self.win_height_var.get()))
        except Exception:
            return
        try:
            # clamp to screen size
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            w = min(w, sw - 50)
            h = min(h, sh - 80)
            # keep current position
            x = self.master.winfo_x()
            y = self.master.winfo_y()
            try:
                self.master.geometry(f"{w}x{h}+{x}+{y}")
            except Exception:
                try:
                    self.master.geometry(f"{w}x{h}")
                except Exception:
                    pass
            # update stored initial size and reflow
            self.initial_width = w
            self.initial_height = h
            try:
                self._reflow_layout()
            except Exception:
                pass
        except Exception:
            pass

    def _apply_window_color(self):
        try:
            col = self.win_color_var.get()
            try:
                self.bg_var.set(col)
            except Exception:
                pass
            try:
                self._apply_bg()
            except Exception:
                pass
        except Exception:
            pass

    def _apply_anim_settings(self):
        try:
            ms = int(self.win_anim_speed_var.get())
            steps = int(self.win_anim_steps_var.get())
        except Exception:
            return
        try:
            # clamp sensible ranges
            ms = max(5, min(1000, ms))
            steps = max(4, min(240, steps))
            self.base_frame_delay = ms
            self.anim_steps_default = steps
            # update current frame delay if not animating
            try:
                self.frame_delay = self._get_effective_frame_delay()
            except Exception:
                pass
        except Exception:
            pass

    def _toggle_bounce(self):
        try:
            if getattr(self, 'win_bouncing', False):
                # stop
                self.win_bouncing = False
                try:
                    if self.win_bounce_job:
                        self.master.after_cancel(self.win_bounce_job)
                except Exception:
                    pass
                self.win_bounce_job = None
                try:
                    btn = getattr(self, '_btn_bounce', None)
                    if btn is not None:
                        btn.configure(text="Start Bounce")
                except Exception:
                    pass
            else:
                # start bouncing
                self.win_bouncing = True
                try:
                    btn = getattr(self, '_btn_bounce', None)
                    if btn is not None:
                        btn.configure(text="Stop Bounce")
                except Exception:
                    pass
                try:
                    self._bounce_step()
                except Exception:
                    pass
        except Exception:
            pass

    def _bounce_step(self):
        try:
            if not getattr(self, 'win_bouncing', False):
                return
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            w = self.master.winfo_width()
            h = self.master.winfo_height()
            x = self.master.winfo_x()
            y = self.master.winfo_y()
            dx = getattr(self, '_bounce_dx', 8)
            dy = getattr(self, '_bounce_dy', 6)

            nx = x + dx
            ny = y + dy
            # bounce off edges
            if nx < 0 or (nx + w) > sw:
                self._bounce_dx = -dx
                nx = max(0, min(nx, sw - w))
            if ny < 0 or (ny + h) > sh:
                self._bounce_dy = -dy
                ny = max(0, min(ny, sh - h))

            try:
                # preserve current size when moving the window to avoid platform-specific side-effects
                try:
                    cw = int(w)
                    ch = int(h)
                    self.master.geometry(f"{cw}x{ch}+{int(nx)}+{int(ny)}")
                except Exception:
                    self.master.geometry(f"+{int(nx)}+{int(ny)}")
            except Exception:
                pass

            # schedule next step
            try:
                # slower tick to reduce CPU and visual jumpiness
                self.win_bounce_job = self.master.after(50, self._bounce_step)
            except Exception:
                self.win_bounce_job = None
        except Exception:
            pass

        # remove Dev tab itself
        try:
            if getattr(self, 'dev_tab_added', False):
                # forget the dev tab and mark as not added
                self.notebook.forget(self.tab_dev)
                self.dev_tab_added = False
                # also clear dev_code_var so user must re-enter code to re-add
                try:
                    self.dev_code_var.set("")
                except Exception:
                    pass
        except Exception:
            pass
        # remove Test window if present
        try:
            if getattr(self, 'test_win_added', False):
                try:
                    self.test_win.destroy()
                except Exception:
                    pass
                self.test_win_added = False
        except Exception:
            pass

        # remove Window Editor if present
        try:
            if getattr(self, 'win_editor_added', False):
                try:
                    self._close_window_editor()
                except Exception:
                    pass
                self.win_editor_added = False
        except Exception:
            pass

        # reset effective frame delay
        try:
            self.frame_delay = self._get_effective_frame_delay()
        except Exception:
            pass

        try:
            messagebox.showinfo("Revoke", "Thank you for using SDN")
        except Exception:
            pass


    def start_flip(self, event=None):
        if self.animating:
            return
        self.animating = True
        # prepare a spinning animation using the default settings
        self.anim_steps = self.anim_steps_default
        self.anim_frame = 0
        self.rotations = self.rotations_default
        self.frame_delay = self._get_effective_frame_delay()
        # choose final outcome now (always random)
        self.final = random.choice(["Heads", "Tails"])
        # increment flip count and award achievements at milestones
        self.flip_count += 1
        # update flip counter UI
        try:
            self.flip_label.configure(text=f"Flips: {self.flip_count}")
        except Exception:
            pass
        # award milestone achievements in order
        if self.flip_count == 1:
            self.award_achievement("1st Coin Flip")
        if self.flip_count == 5:
            self.award_achievement("5th Coin Flip")
        if self.flip_count == 20:
            self.award_achievement("20th Coin Flip")
        if self.flip_count == 50:
            self.award_achievement("50th Coin Flip")
        if self.flip_count == 100:
            self.award_achievement("100th Coin Flip")
        self._animate()

    def _animate(self):
        # spin animation using a cosine to simulate rotation (width goes to thin edge and back)
        if self.anim_frame >= self.anim_steps:
            # finish on the predetermined final face
            final = self.final
            self.canvas.itemconfigure(self.text, text=final, fill="#222")
            # optional color change per result
            if final == "Heads":
                self.canvas.itemconfigure(self.oval, fill="#E6B800", outline="#c68f00")
            else:
                self.canvas.itemconfigure(self.oval, fill="#cfcfcf", outline="#9e9e9e")
            # restore full circular size
            self._set_coin_ellipse(1.0, 1.0)
            # update consecutive-heads counter and award if needed
            if final == "Heads":
                self.consec_heads += 1
            else:
                self.consec_heads = 0

            if self.consec_heads == 4:
                self.award_achievement("I Like Heads")

            # small chance to find a Rebirth cube if player owns an Inventory
            try:
                if getattr(self, 'inventory_owned', False):
                    if random.random() < 0.05:
                        # add to inventory
                        self.inventory_items['Rebirth cube'] = self.inventory_items.get('Rebirth cube', 0) + 1
                        # show a brief popup and update UI if visible
                        try:
                            self._show_item_popup('Rebirth cube')
                        except Exception:
                            pass
                        try:
                            if getattr(self, 'inventory_tab_added', False):
                                self._update_inventory_ui()
                        except Exception:
                            pass
            except Exception:
                pass

            self.animating = False
            return

        # compute progress and angle
        t = self.anim_frame / max(1, self.anim_steps)
        rotations = getattr(self, 'rotations', self.rotations_default)
        theta = t * rotations * 2 * math.pi
        # horizontal scale simulates the coin turning edge-on
        x_scale = abs(math.cos(theta))
        # avoid completely zero width
        x_scale = max(x_scale, 0.05)

        # determine which face is visible based on rotation half-cycles
        side_index = int(theta / math.pi) % 2
        display = "Heads" if side_index == 0 else "Tails"

        # set face color based on which side is currently visible
        if display == "Heads":
            face_fill = "#E6B800"
            face_outline = "#c68f00"
        else:
            face_fill = "#cfcfcf"
            face_outline = "#9e9e9e"

        # apply the face color while it's visible; when edge-on it's still okay
        self.canvas.itemconfigure(self.oval, fill=face_fill, outline=face_outline)

        # hide text when the coin is near edge (very thin)
        if x_scale < 0.12:
            self.canvas.itemconfigure(self.text, text="", fill="")
        else:
            self.canvas.itemconfigure(self.text, text=display, fill="#222")

        # slightly vary vertical size for a little perspective feel
        y_scale = 0.98 + 0.02 * x_scale
        self._set_coin_ellipse(x_scale, y_scale)

        self.anim_frame += 1
        # schedule next frame using configured speed
        self.master.after(self.frame_delay, self._animate)

    def _scale_coin(self, scale):
        # kept for backward compatibility: uniform scaling
        radius = self.base_radius * scale
        x0 = self.cx - radius
        y0 = self.cy - radius
        x1 = self.cx + radius
        y1 = self.cy + radius
        self.canvas.coords(self.oval, x0, y0, x1, y1)
        # ensure text stays centered
        self.canvas.coords(self.text, self.cx, self.cy)

    def _set_coin_ellipse(self, x_scale, y_scale=1.0):
        # set the coin as an ellipse centered at (cx,cy) with separate x/y scales
        rx = self.base_radius * x_scale
        ry = self.base_radius * y_scale
        # ensure a minimum visible width to avoid zero-size geometry
        rx = max(rx, 2)
        x0 = self.cx - rx
        y0 = self.cy - ry
        x1 = self.cx + rx
        y1 = self.cy + ry
        self.canvas.coords(self.oval, x0, y0, x1, y1)
        # keep text centered
        self.canvas.coords(self.text, self.cx, self.cy)


if __name__ == "__main__":
    root = tk.Tk()
    # start hidden while splash shows
    root.withdraw()

    # Splash window
    splash = tk.Toplevel()
    splash.title("Coin Flipper")
    splash.resizable(False, False)
    # simple content: title label and Start button
    frm = ttk.Frame(splash, padding=14)
    frm.pack(fill="both", expand=True)
    splash_font = tkfont.Font(family="Arial", size=22, weight="bold", underline=True)
    lbl = ttk.Label(frm, text="Coin Flipper", font=splash_font)
    lbl.pack(pady=(10, 14))
    btn = ttk.Button(frm, text="Start", width=20)
    btn.pack(pady=(0, 8))

    def _start_main():
        try:
            splash.destroy()
        except Exception:
            pass
        try:
            # show main window and instantiate app
            root.deiconify()
            app = CoinFlipApp(root)
            # allow geometry to settle then center the main window on the screen
            try:
                root.update_idletasks()
                w = root.winfo_width()
                h = root.winfo_height()
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                # ensure reasonable defaults
                if not w or not h:
                    # fallback to a default size if not yet measured
                    w = getattr(app, 'width', 800) or 800
                    h = getattr(app, 'height', 600) or 600
                x = max((sw - w) // 2, 0)
                y = max((sh - h) // 2, 0)
                root.geometry(f"{w}x{h}+{x}+{y}")
            except Exception:
                # ignore if centering fails on some platforms
                pass
        except Exception:
            pass

    def _show_intro():
        """Show a short introduction popup before starting the main game."""
        try:
            intro = tk.Toplevel(splash)
            intro.title("Welcome")
            intro.transient(splash)
            intro.resizable(False, False)
            frm_i = ttk.Frame(intro, padding=12)
            frm_i.pack(fill="both", expand=True)

            # Intro title
            title_font = tkfont.Font(family="Arial", size=14, weight="bold")
            lbl_i = ttk.Label(frm_i, text="Welcome to Coin Flipper", font=title_font)
            lbl_i.pack(pady=(4, 8))

            # Intro text (using the provided keywords and a playful tone)
            txt = (
                "This is a light simulation experience —\n"
                "Think incremental fun (like a hit game such as Cookie Clicker).\n\n"
                "Features: Simulation, achievements, a tiny shop, inventory, and more.\n"
                "It's an experiment: I'm trying to cram as much code as possible into a single script!\n\n"
                "Controls: Press Enter to flip the coin. Explore Settings and Achievements to unlock surprises."
            )
            lbl_txt = ttk.Label(frm_i, text=txt, justify="left", wraplength=380)
            lbl_txt.pack(padx=4, pady=(0, 8))

            # At the bottom show a prompt and bind Enter to continue
            prompt = ttk.Label(frm_i, text="Press Enter to continue", anchor="center")
            prompt.pack(pady=(6, 2))

            def _continue():
                try:
                    intro.destroy()
                except Exception:
                    pass
                try:
                    _start_main()
                except Exception:
                    pass

            # Bind Enter key to continue; ensure intro has focus
            try:
                intro.bind('<Return>', lambda e: _continue())
                intro.focus_set()
            except Exception:
                pass

            # center intro over splash
            intro.update_idletasks()
            sw_i = intro.winfo_screenwidth()
            sh_i = intro.winfo_screenheight()
            iw = 420
            ih = 220
            ix = (sw_i - iw) // 2
            iy = (sh_i - ih) // 2
            intro.geometry(f"{iw}x{ih}+{ix}+{iy}")
            try:
                intro.grab_set()
            except Exception:
                pass
        except Exception:
            # fallback: start main
            try:
                _start_main()
            except Exception:
                pass

    # Add a "Press any button to continue" hint and bind any key or click
    hint_font = tkfont.Font(size=10, slant="italic")
    lbl_hint = ttk.Label(frm, text="Press any key or click anywhere to continue", font=hint_font)
    lbl_hint.pack(pady=(4, 6))

    def _any_input_start(event=None):
        # Pressing any key/click should open the intro (not immediately start main)
        try:
            _show_intro()
        except Exception:
            try:
                # fallback: start main directly
                _start_main()
            except Exception:
                pass

    # Bind keys and mouse clicks to open the intro
    try:
        splash.bind("<Key>", _any_input_start)
        splash.bind("<Button-1>", _any_input_start)
        splash.focus_set()
    except Exception:
        pass

    btn.configure(command=_show_intro)

    # center splash on screen
    splash.update_idletasks()
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    ww = 440
    wh = 180
    x = (sw - ww) // 2
    y = (sh - wh) // 2
    splash.geometry(f"{ww}x{wh}+{x}+{y}")

    # Slide the splash in from above the screen to the centered position
    def _slide_in_splash(step_pixels=20, delay=12):
        try:
            # starting y above the top of the screen
            start_y = -wh
            target_y = y
            cur_y = start_y

            def _step(cy):
                try:
                    if cy >= target_y:
                        # ensure final anchored position
                        splash.geometry(f"{ww}x{wh}+{x}+{target_y}")
                        return
                    splash.geometry(f"{ww}x{wh}+{x}+{int(cy)}")
                except Exception:
                    try:
                        # fallback attempt
                        splash.wm_geometry(f"{ww}x{wh}+{x}+{int(cy)}")
                    except Exception:
                        pass
                try:
                    splash.after(delay, lambda: _step(cy + step_pixels))
                except Exception:
                    pass

            # place the splash at the starting off-screen position then animate
            try:
                splash.geometry(f"{ww}x{wh}+{x}+{start_y}")
            except Exception:
                try:
                    splash.wm_geometry(f"{ww}x{wh}+{x}+{start_y}")
                except Exception:
                    pass
            try:
                _step(cur_y)
            except Exception:
                pass
        except Exception:
            # if sliding fails, just ensure it's at the target position
            try:
                splash.geometry(f"{ww}x{wh}+{x}+{y}")
            except Exception:
                pass

    try:
        # use smaller step and delay for a smoother slide; tweak to taste
        _slide_in_splash(step_pixels=12, delay=12)
    except Exception:
        try:
            splash.geometry(f"{ww}x{wh}+{x}+{y}")
        except Exception:
            pass

    # ensure closing the splash exits
    def _on_splash_close():
        try:
            splash.destroy()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass

    try:
        splash.protocol("WM_DELETE_WINDOW", _on_splash_close)
    except Exception:
        pass

    # play a short melodic startup tune (~5 seconds) in background (Windows winsound if available)
    def _play_startup_beeps(sec=3):
        try:
            import winsound

            # simple scale (frequencies) for C major across two octaves
            NOTES = {
                'C4': 261, 'D4': 294, 'E4': 329, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 493,
                'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880, 'B5': 987,
            }

            # a small, pleasant motif (not a copyrighted melody) — two-bar phrase
            # shorter durations for a faster tempo
            motif = [
                ('E4', 100), ('G4', 100), ('C5', 180),
                ('G4', 100), ('E4', 100), ('C4', 180),
            ]

            # loop motif until time elapses
            end = time.time() + float(sec)
            idx = 0
            while time.time() < end:
                note, duration = motif[idx % len(motif)]
                freq = NOTES.get(note, 440)
                try:
                    winsound.Beep(freq, duration)
                except Exception:
                    # fallback: sleep for duration if beep fails
                    time.sleep(duration / 1000.0)
                # short gap between notes (faster)
                time.sleep(0.02)
                idx += 1
        except Exception:
            # winsound not available or other error: sleep silently for the duration
            try:
                time.sleep(sec)
            except Exception:
                pass

    # Startup sound removed by user request: do not start the playback thread
    # (the function _play_startup_beeps remains in case we want it later)

    root.mainloop()