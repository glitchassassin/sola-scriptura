# encoding: utf-8
from __future__ import unicode_literals
import re

import urwid
from .bible_handler import Bible
from .custom_widgets import AlertPopup, QuestionBox
from .config import Config
from .module_handler import Library
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
		self.config = Config()
		self.library = Library()
		# Create sections
		self.header = Header()
		self.reader = Reader(self.config, self.header.set_version, self.header.set_passage)
		last_passage = "{} {}{}".format(self.config.last_read["book"], 
										self.config.last_read["chapter"], 
										(":" + self.config.last_read["verse"]) if self.config.last_read["verse"] else "")
		self.reader.set_bible(self.library.get_bible("KJV"))
		self.reader.go_to_passage_string(last_passage)
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
		self.handler.register(name="version", action=self.launch_version, key="v")
		self.handler.register(name="quit", action=self.quit, key="q")

		# Define loop
		self.loop = urwid.MainLoop(self.frame, self.palettes, unhandled_input=self.handler.handle)


	def run(self):
		self.loop.run()

	def launch_toc(self):
		self.loop.widget = TableOfContentsPopup(self.frame, self.reader, self.close_toc)
	def close_toc(self):
		self.loop.widget = self.frame

	def launch_version(self):
		self.loop.widget = VersionPopup(self.frame, self.reader, self.library, self.close_version)
	def close_version(self):
		self.loop.widget = self.frame
	
	def launch_goto(self):
		self.loop.widget = GoToPopup(self.frame, self.reader, self.close_goto)
	def close_goto(self, error=None):
		self.loop.widget = self.frame
		if error:
			self.launch_alert(error)
	
	def launch_alert(self, message):
		self.loop.widget = AlertPopup(self.frame, message, self.close_alert)
	def close_alert(self):
		self.loop.widget = self.frame

	def quit(self):
		raise urwid.ExitMainLoop()

class Header(urwid.Columns):
	def __init__(self):
		self.passage = urwid.Text(" Select Passage ")
		self.heading = urwid.Text("│  Sola Scriptura  │\n└──────────────────┘", align="center")
		self.version = urwid.Text("Version: Select  ", align="right")
		super(Header, self).__init__([self.passage, self.heading, self.version])

	def set_passage(self, text):
		self.passage.set_text(" {}".format(text))
		#return "┌" + text + "┐\n" + "┴" + "─"*len(text) + "┴" + "─"*(78-len(text))

	def set_version(self, text):
		self.version.set_text("Version: {}  ".format(text))


class Reader(urwid.ListBox):
	def __init__(self, config, notify_current_version, notify_current_passage):
		self.config = config
		self.bible = None
		self.current_passage = None
		self.notify_current_version = notify_current_version
		self.notify_current_passage = notify_current_passage
		self.text_widget = urwid.Text("")
		self.header = urwid.Text("")
		
		super(Reader, self).__init__(urwid.SimpleFocusListWalker([self.header, self.text_widget, urwid.Divider("─")]))

	def go_to_passage(self, books, chapters=None, verses=None):
		self.text_widget.set_text(self.bible.get(books=books, chapters=chapters, verses=verses))
		self.set_focus(0)
		self.current_passage = (books, chapters, verses)
		books = self.bible.get_canonical_name(books)
		chapters = "" if chapters is None else chapters
		chapters = ",".join(chapters) if hasattr(chapters, "__iter__") and not isinstance(chapters, basestring) else chapters
		verses = "" if verses is None else verses
		verses = ",".join([str(v) for v in verses]) if hasattr(verses, "__iter__") and not isinstance(verses, basestring) else verses
		verses = ":" + verses if verses else verses
		passage_name = " {} {}{} ".format(books, chapters, verses)
		self.header.set_text(("title", passage_name))
		self.config.last_read["book"] = books
		self.config.last_read["chapter"] = chapters
		self.config.last_read["verse"] = verses
		self.config.save_config()
		
		self.notify_current_passage(passage_name)

	def go_to_passage_string(self, passage):
		regex = re.compile("(.*)? (\d+)(:?([0-9\-,]+))?")
		results = regex.match(passage)
		if results:
			books = results.group(1)
			chapters = int(results.group(2))
			verses = results.group(4)
			# Parse verses, e.g. John 3:14-17 or John 3:1,2,5
			if verses and "," in verses:
				verses = [int(x) for x in verses.split(",")]
			elif verses and "-" in verses:
				beginning, end = verses.split("-")
				verses = range(int(beginning), int(end)+1)
			elif verses:
				verses = int(verses)
			return self.go_to_passage(books=books, chapters=chapters, verses=verses)
		raise ValueError("Invalid passage: {}".format(passage))

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
	
	def set_bible(self, bible):
		self.bible = bible
		self.notify_current_version(bible.name)
		if self.current_passage:
			books, chapters, verses = self.current_passage
			self.go_to_passage(books=books, chapters=chapters, verses=verses)

class TableOfContentsPopup(urwid.Overlay):
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
		super(TableOfContentsPopup, self).__init__(urwid.LineBox(self.frame), backdrop,
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

class GoToPopup(urwid.Overlay):
	def __init__(self, backdrop, reader, callback):
		self.reader = reader
		self.callback = callback
		# Create internal GUI elements
		self.title = urwid.Text("Open passage:", align="center")
		self.textbox = QuestionBox("> ", self.select_passage)
		#urwid.connect_signal(self.textbox, "change", self.check_done)
		#self.submit = urwid.Button("Go", on_press=self.select_passage)
		self.frame = urwid.ListBox(urwid.SimpleFocusListWalker([self.title, self.textbox]))
		# Populate overlay
		super(GoToPopup, self).__init__(urwid.LineBox(self.frame), backdrop,
			align="center", width=50,
			valign="middle", height=5)
	
	def select_passage(self, passage):
		if passage == "":
			return self.callback() # Do nothing
		try:
			self.reader.go_to_passage_string(passage)
			return self.callback()
		except ValueError:
			return self.callback("Invalid passage: {}".format(passage))
			raise

class VersionPopup(urwid.Overlay):
	def __init__(self, backdrop, reader, library, callback):
		self.reader = reader
		self.library = library
		self.callback = callback
		self.selected = {}
		# Create internal GUI elements
		self.title = urwid.Text("Select version\n─────────────────", align="center")
		bible_list = self.library.list_bibles()
		widgets = []
		for b in bible_list:
			button = urwid.Button(b)
			urwid.connect_signal(button, "click", self.select_bible, b)
			widgets.append(button)
		self.focus_list = urwid.SimpleFocusListWalker(widgets)
		self.frame = urwid.Frame(urwid.ListBox(self.focus_list), header=self.title)
		# Populate overlay
		super(VersionPopup, self).__init__(urwid.LineBox(self.frame), backdrop,
			align="center", width=25,
			valign="middle", height=20)
	
	def select_bible(self, button, bible):
		self.reader.set_bible(self.library.get_bible(bible))
		return self.callback()

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
