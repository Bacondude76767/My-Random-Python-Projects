import tkinter as tk
from CoinFlipping import CoinFlipApp

root = tk.Tk()
root.withdraw()  # keep the window hidden during the test
app = CoinFlipApp(root)

print("Initial shop_tab_added:", getattr(app, 'shop_tab_added', False))

# Use the dev helper to add rebirths (simulate giving 1 rebirth)
try:
    app.dev_rebirths_var.set(1)
except Exception:
    app.dev_rebirths_var = tk.IntVar(value=1)

app._dev_add_rebirths()

print("After _dev_add_rebirths, rebirth_count:", app.rebirth_count)
print("shop_tab_added:", getattr(app, 'shop_tab_added', False))

# list notebook tabs by their displayed text
try:
    tabs = [app.notebook.tab(t, "text") for t in app.notebook.tabs()]
except Exception:
    tabs = []
print("Tabs:", tabs)

root.destroy()