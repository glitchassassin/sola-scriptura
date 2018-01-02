import urwid

def exit_on_q(key):
	if key in ('q', 'Q'):
		raise urwid.ExitMainLoop()
	txt.set_text(repr(key))

palette = [
   	('banner', 'black', 'light gray'),
   	('streak', 'black', 'dark blue'),
	('bg', 'white', 'black'),]

txt = urwid.Text(('banner', u" Hello World "), align='center')
map1 = urwid.AttrMap(txt, 'streak')
fill = urwid.Filler(map1)
map2 = urwid.AttrMap(fill, 'bg')
loop = urwid.MainLoop(map2, palette, unhandled_input=exit_on_q)
loop.run()
