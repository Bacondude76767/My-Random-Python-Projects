import tkinter as tk
import time
import random
from CoinFlipping import CoinFlipApp

root = tk.Tk()
root.geometry('400x480')
app = CoinFlipApp(root)

# Ensure inventory is owned and inventory tab is revealed so UI updates happen
app.inventory_owned = True
# reveal inventory tab (adds tab and builds UI) if not already
app._reveal_inventory_tab()
root.update()

print('Starting interactive popup test. This will open a visible window for a few seconds.')
print('Inventory owned:', app.inventory_owned)
print('Current inventory items:', app.inventory_items)

found = False
max_attempts = 500
for i in range(1, max_attempts + 1):
    # simulate a flip ending; only the drop logic matters here (app would normally run animation)
    if random.random() < 0.05:
        # add to inventory and trigger UI + popup
        app.inventory_items['Rebirth cube'] = app.inventory_items.get('Rebirth cube', 0) + 1
        print(f'Flip {i}: Rebirth cube dropped (simulated).')
        # show popup and update inventory UI
        app._show_item_popup('Rebirth cube')
        app._update_inventory_ui()
        root.update()
        # check for Toplevel presence
        tops = [w for w in root.winfo_children() if w.winfo_class() == 'Toplevel']
        print('Toplevel popups now present:', len(tops))
        # read inventory label text if available
        lbl_text = None
        try:
            lbl_widget = app.inventory_item_labels.get('Rebirth cube')
            if lbl_widget:
                lbl_text = lbl_widget.cget('text')
        except Exception as e:
            lbl_text = f'error reading label: {e}'
        print('Inventory label after drop:', lbl_text)
        # wait >2s to allow popup to auto-destroy
        time.sleep(2.5)
        root.update()
        tops_after = [w for w in root.winfo_children() if w.winfo_class() == 'Toplevel']
        print('Toplevel popups after 2.5s:', len(tops_after))
        found = True
        break
    # short sleep to simulate time between flips
    time.sleep(0.01)
    root.update()

if not found:
    print(f'No cube dropped after {max_attempts} simulated flips.')
else:
    print('Final inventory:', app.inventory_items)

# cleanup
try:
    root.destroy()
except Exception:
    pass
