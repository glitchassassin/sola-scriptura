import urwid

overlay = None

def key_handler(key):
	if key == "g":
		 loop.widget = urwid.Overlay(frame, urwid.LineBox(urwid.Filler(urwid.Text("POPUP!"))), "center", 60, "middle", 10)
	elif key == "q":
		raise urwid.ExitMainLoop()
	elif key == "esc":
		loop.widget = frame

frame_text = urwid.Text("Test", align="center")
frame = urwid.Frame(urwid.Filler(frame_text))
loop = urwid.MainLoop(frame, unhandled_input=key_handler)

loop.run()
