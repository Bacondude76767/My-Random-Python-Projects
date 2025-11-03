import tkinter as tk
import random
from CoinFlipping import CoinFlipApp

root = tk.Tk()
root.withdraw()
app = CoinFlipApp(root)

# Ensure inventory is owned so flips can drop Rebirth cubes
app.inventory_owned = True
app.inventory_items = {}

max_flips = 500
found = False
flips_needed = None

for i in range(1, max_flips + 1):
    # simulate the end-of-animation drop check used in _animate
    if random.random() < 0.05:
        app.inventory_items['Rebirth cube'] = app.inventory_items.get('Rebirth cube', 0) + 1
        found = True
        flips_needed = i
        break

print(f"Inventory owned: {app.inventory_owned}")
print(f"Max flips attempted: {max_flips}")
if found:
    print(f"Rebirth cube obtained after {flips_needed} simulated flips.")
    print(f"Inventory now: {app.inventory_items}")
else:
    print("No Rebirth cube obtained in the simulation.")

root.destroy()
