# encoding: utf-8
from __future__ import unicode_literals

import urwid
from .bible_handler import Bible
try:
	basestring
except:
	basestring = str

def main():
	c = Controller()
	c.run()

class Controller(object):
	def __init__(self):
		self.handler = InputHandler()
		
		# Create sections
		self.header = Header()
		self.reader = Reader(self.header.set_passage)
		self.body = urwid.Padding(self.reader, align="center", width=80) 
		self.frame = urwid.Frame(self.body, header=self.header, footer=Footer())

		self.palettes = [
			("text", "light gray", "black"),
			("note", "dark gray", "black"),
			("title", "white", "black"),
		]

		# Set up commands
		self.handler.register(name="next_chapter", action=self.reader.go_to_next_chapter, key="right")
		self.handler.register(name="prev_chapter", action=self.reader.go_to_prev_chapter, key="left")
		self.handler.register(name="toc", action=self.launch_toc, key="c")
		self.handler.register(name="goto", action=self.launch_goto, key="g")
		self.handler.register(name="quit", action=self.quit, key="q")

		# Define loop
		self.loop = urwid.MainLoop(self.frame, self.palettes, unhandled_input=self.handler.handle)

	def run(self):
		self.loop.run()

	def launch_toc(self):
		self.loop.widget = TableOfContents(self.frame, self.reader, self.close_toc)

	def close_toc(self):
		self.loop.widget = self.frame

	def quit(self):
		raise urwid.ExitMainLoop()
	
	def launch_goto(self):
		pass

class Header(urwid.Columns):
	def __init__(self):
		self.passage = urwid.Text(" Select Passage ")
		self.heading = urwid.Text("│  Sola Scriptura  │\n└──────────────────┘", align="center")
		self.version = urwid.Text("Version: ESV  ", align="right")
		super(Header, self).__init__([self.passage, self.heading, self.version])

	def set_passage(self, text):
		self.passage.set_text(" {}".format(text))
		#return "┌" + text + "┐\n" + "┴" + "─"*len(text) + "┴" + "─"*(78-len(text))


class Reader(urwid.ListBox):
	def __init__(self, notify_current_passage):
		self.bible = Bible("ESV2011", "ESV2011.zip")
		self.current_passage = None
		self.notify_current_passage = notify_current_passage
		self.text_widget = urwid.Text("")
		self.header = urwid.Text("")
		
		super(Reader, self).__init__(urwid.SimpleFocusListWalker([self.header, self.text_widget, urwid.Divider("─")]))
		
		self.go_to_passage("Revelation of John", 22)

	def go_to_passage(self, books, chapters=None, verses=None):
		self.text_widget.set_text(self.bible.get(books=books, chapters=chapters, verses=verses))
		self.set_focus(0)
		self.current_passage = (books, chapters, verses)
		chapters = "" if chapters is None else chapters
		verses = "" if verses is None else verses
		passage_name = " {} {}{} ".format(  ", ".join(books) if not isinstance(books, basestring) else books, 
											",".join(chapters) if hasattr(chapters, "__iter__") and not isinstance(chapters, basestring) else chapters, 
											":" + ",".join(verses) if hasattr(verses, "__iter__") and not isinstance(verses, basestring) else verses)
		self.header.set_text(("title", passage_name))
		self.notify_current_passage(passage_name)

	def go_to_next_chapter(self):
		# Check if the book has more chapters; if so, return the next chapter.
		# If not, get the first chapter of the next book.
		# If there is no next book, do nothing.
		book, chapter, verse = self.current_passage
		books = self.bible.get_books()
		get_next_book = False
		for t in books:
			for b in books[t]:
				if get_next_book:
					return self.go_to_passage(b.name, 1)
				if b.name_matches(book):
					if chapter+1 <= b.num_chapters:
						return self.go_to_passage(book, chapter+1)
					else:
						get_next_book = True
		# Fail silently
				
	def go_to_prev_chapter(self):
		# If there is a previous chapter in this book, return that.
		# Otherwise, get the last chapter from the previous book
		# If there is no previous book, do nothing.
		book, chapter, verse = self.current_passage
		if chapter > 1:
			return self.go_to_passage(book, chapter-1)
		books = self.bible.get_books()
		previous_book = None
		for t in books:
			for b in books[t]:
				if b.name_matches(book):
					if previous_book is not None:
						return self.go_to_passage(previous_book.name, previous_book.num_chapters)
					else:
						return # At beginning - do nothing
				previous_book = b

class TableOfContents(urwid.Overlay):
	def __init__(self, backdrop, reader, callback):
		self.reader = reader
		self.callback = callback
		self.selected = {}
		# Create internal GUI elements
		self.title = urwid.Text("Select book\n───────────────", align="center")
		book_list = self.reader.bible.get_books()
		widgets = []
		for t in book_list:
			for b in book_list[t]:
				button = urwid.Button(b.name)
				urwid.connect_signal(button, "click", self.select_book, b)
				widgets.append(button)
			widgets.append(urwid.Divider())
		self.focus_list = urwid.SimpleFocusListWalker(widgets)
		self.frame = urwid.Frame(urwid.ListBox(self.focus_list), header=self.title)
		# Populate overlay
		super(TableOfContents, self).__init__(urwid.LineBox(self.frame), backdrop,
			align="center", width=25,
			valign="middle", height=20)
	
	def select_book(self, button, book):
		self.selected["book"] = book
		del self.focus_list[:]
		self.title.set_text("Select chapter\n─────────────────")
		for c in range(1, book.num_chapters+1):
			button = urwid.Button(str(c))
			urwid.connect_signal(button, "click", self.select_chapter, c)
			self.focus_list.append(button)
	
	def select_chapter(self, button, chapter):
		self.selected["chapter"] = chapter
		self.reader.go_to_passage(books=self.selected["book"].name, chapters=chapter)
		self.callback()

	def select_verse(self, button, verse):
		# Skipping verse selection until we come up with a better control scheme
		self.selected["verse"] = verse
		self.callback()

class Footer(urwid.Pile):
	def __init__(self):
		self.divider = urwid.Divider("─")
		legend_entries = [
			urwid.Text([("text", "Prev Chapter "), ("title", "[<-]  ")], align="center"),
			urwid.Text([("text", "Switch Version "), ("title", "[v]  ")], align="center"),
			urwid.Text([("text", "Go To... "), ("title", "[g]  ")], align="center"),
			urwid.Text([("text", "Contents "), ("title", "[c]  ")], align="center"),
			#urwid.Text([("text", "Find... "), ("title", "[f]  ")], align="center"),
			urwid.Text([("text", "Next Chapter "), ("title", "[->]")], align="center"),
		]
		self.legend = urwid.Columns(legend_entries)
		super(Footer, self).__init__([self.divider, self.legend])

class InputHandler(object):
	def __init__(self):
		self.actions = {}
		self.loop = None

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
	
		


if __name__ == "__main__":
	main()
