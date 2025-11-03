import tkinter as tk
from CoinFlipping import CoinFlipApp

root = tk.Tk()
root.withdraw()
app = CoinFlipApp(root)
# simulate entering dev code
app.dev_code_var.set("Kendall07232012!")
app._try_dev_code()

print('dev_tab_added:', getattr(app,'dev_tab_added',False))
print('test_tab_added:', getattr(app,'test_tab_added',False))
# list tabs
try:
    tabs = [app.notebook.tab(t, 'text') for t in app.notebook.tabs()]
except Exception:
    tabs = []
print('Tabs:', tabs)
root.destroy()
