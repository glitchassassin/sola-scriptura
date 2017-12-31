from picotui.screen import *
from picotui.widgets import *

s = Screen()

try:
	s.init_tty()
	s.enable_mouse()
	s.attr_color(C_WHITE, C_BLUE)
	s.cls()
	s.attr_reset()
	d = Dialog(5, 5, 20, 12)
	# DropDown and ListBox widgets
	d.add(1, 1, "Dropdown:")
	w_dropdown = WDropDown(10, ["All", "Red", "Green", "Yellow"])
	d.add(11, 1, w_dropdown)
	d.add(1, 3, "List:")
	w_listbox = WListBox(16, 4, ["%s" % i for i in fchoices])
	d.add(1, 4, w_listbox)
	# Filter the ListBox based on the DropDown selection
	def dropdown_changed(w):
		fchoices.clear()
		for i in range(0, len(choices)):
			if w.items[w.choice] == "All" or w.items[w.choice] in choices[i]:
				fchoices.append(choices[i])
				w_listbox.top_line = 0
				w_listbox.cur_line = 0
				w_listbox.row = 0
				w_listbox.items = ["%s" % items for items in fchoices]
except:
	raise
