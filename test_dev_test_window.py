import tkinter as tk
from CoinFlipping import CoinFlipApp

root = tk.Tk()
root.withdraw()
app = CoinFlipApp(root)
# simulate entering dev code
app.dev_code_var.set("Kendall07232012!")
app._try_dev_code()

print('dev_tab_added:', getattr(app,'dev_tab_added',False))
print('test_win_added:', getattr(app,'test_win_added',False))
# list tabs
try:
    tabs = [app.notebook.tab(t, 'text') for t in app.notebook.tabs()]
except Exception:
    tabs = []
print('Tabs:', tabs)
# check Toplevels
tops = [w for w in root.winfo_children() if w.winfo_class() == 'Toplevel']
print('Toplevel count:', len(tops))
root.destroy()