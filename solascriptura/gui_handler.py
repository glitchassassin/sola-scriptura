import urwid
from .bible_handler import Bible

def main():
	handler = InputHandler()
	handler.register(name="quit", action=quit, key="q")

	# Create sections
	body = urwid.Padding(Reader(), align="center", width=80) 
	frame = urwid.Frame(body, header=Header(), footer=Footer())

	palettes = [
		("text", "light gray", "black"),
		("note", "dark gray", "black"),
		("title", "white", "black"),
	]
	loop = urwid.MainLoop(frame, palettes, unhandled_input=handler.handle)
	loop.run()

class Header(urwid.Columns):
	def __init__(self):
		self.menus = urwid.Columns([
			urwid.Text("File", align="center"),
			urwid.Text("Edit", align="center"),
			urwid.Text("Search", align="center"),
			urwid.Text("Help", align="center")
		])
		self.heading = urwid.Text("│  Sola Scriptura  │\n└──────────────────┘", align="center")
		self.version = urwid.Text("Version: ESV  ", align="right")
		super(Header, self).__init__([self.menus, self.heading, self.version])

class Reader(urwid.Frame):
	def __init__(self):
		self.bible = Bible("ESV2011", "ESV2011.zip")
		self.tab = urwid.Text(self.format_tab(" Select Passage "))
		self.text_widget = urwid.Text("")
		self.go_to_passage("Matt", 1)
		self.scroller = urwid.ListBox(urwid.SimpleFocusListWalker([self.text_widget, urwid.Divider("─"), urwid.Text("[End of Selection]", align="center")]))
		
		super(Reader, self).__init__(self.scroller, header=self.tab)

	def format_tab(self, text):
		return "┌" + text + "┐\n" + "┴" + "─"*len(text) + "┴" + "─"*(78-len(text))

	def go_to_passage(self, books, chapters=None, verses=None):
		self.text_widget.set_text(self.bible.get(books=books, chapters=chapters, verses=verses))
		chapters = "" if chapters is None else chapters
		verses = "" if verses is None else verses
		tab_name = " {} {}{} ".format(", ".join(books) if not isinstance(books, str) else books, 
									",".join(chapters) if hasattr(chapters, "__iter__") and not isinstance(chapters, str) else chapters, 
									":" + ",".join(verses) if hasattr(verses, "__iter__") and not isinstance(verses, str) else verses)
		self.tab.set_text(self.format_tab(tab_name))
	
class Footer(urwid.Pile):
	def __init__(self):
		self.divider = urwid.Divider("─")
		legend_entries = [
			urwid.Text([("text", "Prev Chapter "), ("title", "[<-]  ")], align="center"),
			urwid.Text([("text", "Switch Version "), ("title", "[v]  ")], align="center"),
			urwid.Text([("text", "Go To... "), ("title", "[g]  ")], align="center"),
			urwid.Text([("text", "Find... "), ("title", "[f]  ")], align="center"),
			urwid.Text([("text", "Next Chapter "), ("title", "[->]")], align="center"),
		]
		self.legend = urwid.Columns(legend_entries)
		super(Footer, self).__init__([self.divider, self.legend])

class InputHandler(object):
	def __init__(self):
		self.actions = {}

	def handle(self, key):
		for a in self.actions:
			if key == self.actions[a]["key"]:
				self.actions[a]["action"]()
				return
	
	def register(self, name, action, key, modifiers=[]):
		self.actions[name] = {
			"key": key,
			"modifiers": modifiers,
			"action": action
		}
	def unregister(self, name):
		del self.actions[name]
	

def quit():
	raise urwid.ExitMainLoop()

if __name__ == "__main__":
	main()
