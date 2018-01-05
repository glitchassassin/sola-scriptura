# encoding: utf-8
#from __future__ import unicode_literals
import re
import os
try:
	from urllib2 import urlopen
except:
	from urllib.request import urlopen

import urwid

from .messages import NO_MODULES_DETECTED, SETUP
try:
	basestring
except:
	basestring = str


## Main Widgets ##

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
		self.text_widget = urwid.Text(NO_MODULES_DETECTED.format(self.config.modules["default_path"]))
		self.header = urwid.Text("No Modules Detected")
		
		super(Reader, self).__init__(urwid.SimpleFocusListWalker([self.header, self.text_widget, urwid.Divider("─")]))

	def go_to_passage(self, book=None, chapters=None, verses=None):
		if self.bible is None:
			return # Do nothing
		
		try:
			self.text_widget.set_text(self.bible.get(book=book, chapters=chapters, verses=verses))
		except ValueError:
			books = self.bible.get_books()
			for t in books:
				for b in books[t]:
					return self.go_to_passage(book=b.name, chapters=1)

		self.set_focus(0)
		self.current_passage = (book, chapters, verses)
		book = self.bible.get_canonical_name(book)
		chapters = "" if chapters is None else chapters
		chapters = ",".join(chapters) if hasattr(chapters, "__iter__") and not isinstance(chapters, basestring) else chapters
		verses = "" if verses is None else verses
		verses = ",".join([str(v) for v in verses]) if hasattr(verses, "__iter__") and not isinstance(verses, basestring) else verses
		verses = ":" + verses if verses else verses
		passage_name = " {} {}{} ".format(book, chapters, verses)
		self.header.set_text(("title", passage_name))
		self.config.last_read["book"] = book
		self.config.last_read["chapter"] = chapters
		self.config.last_read["verse"] = verses
		self.config.save_config()
		
		self.notify_current_passage(passage_name)

	def go_to_passage_string(self, passage):
		if self.bible is None:
			return # Do nothing
		regex = re.compile("(.*)? (\d+)(:?([0-9\-,]+))?")
		results = regex.match(passage)
		if results:
			book = results.group(1)
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
			return self.go_to_passage(book=book, chapters=chapters, verses=verses)
		raise ValueError("Invalid passage: {}".format(passage))

	def go_to_next_chapter(self):
		# Check if the book has more chapters; if so, return the next chapter.
		# If not, get the first chapter of the next book.
		# If there is no next book, do nothing.
		if self.bible is None:
			return # Do nothing
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
		if self.bible is None:
			return # Do nothing
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
		if bible is None:
			return # Do nothing
		self.bible = bible
		self.notify_current_version(bible.name)
		self.config.last_read["version"] = bible.name
		self.config.save_config()
		if self.current_passage:
			book, chapters, verses = self.current_passage
			self.go_to_passage(book=book, chapters=chapters, verses=verses)
				

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

## Popup Overlays ##

class TableOfContentsPopup(urwid.Overlay):
	def __init__(self, backdrop, reader, callback):
		self.reader = reader
		self.callback = callback
		self.selected = {}
		# Create internal GUI elements
		self.title = urwid.Text("Select book\n───────────────", align="center")

		widgets = []
		if self.reader.bible is not None:
			book_list = self.reader.bible.get_books()
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
		self.reader.go_to_passage(book=self.selected["book"].name, chapters=chapter)
		self.callback()

	def select_verse(self, button, verse):
		# Skipping verse selection until we come up with a better control scheme
		self.selected["verse"] = verse
		self.callback()

	def keypress(self, size, key):
		if key == "esc":
			self.callback()
		else:
			return super(TableOfContentsPopup, self).keypress(size, key)


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

	def keypress(self, size, key):
		if key == "esc":
			self.callback()
		else:
			return super(GoToPopup, self).keypress(size, key)


class VersionPopup(urwid.Overlay):
	def __init__(self, backdrop, reader, library, callback):
		self.reader = reader
		self.library = library
		self.callback = callback
		self.selected = {}
		# Create internal GUI elements
		self.title = urwid.Text("Select version\n─────────────────", align="center")
		bible_list = sorted(self.library.list_bibles())
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

	def keypress(self, size, key):
		if key == "esc":
			self.callback()
		else:
			return super(VersionPopup, self).keypress(size, key)


class SetupPopup(urwid.Overlay):
	def __init__(self, backdrop, module_path, callback):
		self.module_path = module_path
		self.callback = callback

		# Create internal GUI elements
		self.title = urwid.Text(("title", "Setup Wizard"), align="center")
		self.instructions = urwid.Text(SETUP)
		self.ok_button = urwid.Padding(urwid.Button("Ok", on_press=self.run_setup), align="center", width=("relative", 33))
		self.cancel_button = urwid.Padding(urwid.Button("Cancel", on_press=self.close), align="center", width=("relative", 33))
		#self.focus_list = urwid.Pile([self.instructions]) #
		self.frame = urwid.Frame(urwid.Filler(urwid.Padding(self.instructions, align="center", left=1, right=1)), header=self.title, footer=urwid.Columns([self.ok_button, self.cancel_button]))
		self.frame.focus_position = "footer"
		# Populate overlay
		super(SetupPopup, self).__init__(urwid.LineBox(self.frame), backdrop,
			align="center", width=70,
			valign="middle", height=14)

	def keypress(self, size, key):
		if key == "esc":
			self.callback()
		else:
			return super(SetupPopup, self).keypress(size, key)
	
	def close(self, button):
		self.callback()
	
	def run_setup(self, button):
		# Sample modules to start with:
		modules = [
			"ftp://ftp.crosswire.org/pub/sword/packages/rawzip/ESV2011.zip",
			"ftp://ftp.crosswire.org/pub/sword/packages/rawzip/KJV.zip",
			"ftp://ftp.crosswire.org/pub/sword/packages/rawzip/TR.zip",
			#"ftp://ftp.crosswire.org/pub/sword/packages/rawzip/SBLGNT.zip",
		]

		self.instructions.set_text("Downloading modules...")

		for module in modules:
			resp = urlopen(module)
			with open(os.path.join(self.module_path, module.split("/")[-1]), "wb") as f:
				f.write(resp.read())
		self.callback("{} modules downloaded".format(len(modules)))

## Building Blocks ##

class AlertPopup(urwid.Overlay):
	def __init__(self, backdrop, message, callback):
		self.callback = callback
		self.title = urwid.Text(("title", "Alert"), align="center")
		self.message = urwid.Text(message, align="center")
		self.ok = urwid.Button("Ok", on_press=self.close)
		self.ok = urwid.Padding(self.ok, align="center", width=("relative", 33))

		self.frame = urwid.ListBox(urwid.SimpleFocusListWalker([self.title, urwid.Divider(), self.message, urwid.Divider(), self.ok]))

		# Populate overlay
		super(AlertPopup, self).__init__(urwid.LineBox(self.frame), backdrop,
			align="center", width=50,
			valign="middle", height=7)

	def close(self, button):
		self.callback()

	def keypress(self, size, key):
		if key == "esc":
			self.callback()
		else:
			return super(AlertPopup, self).keypress(size, key)


class QuestionBox(urwid.Edit):
	def __init__(self, caption, callback):
		self.callback = callback
		super(QuestionBox, self).__init__(caption)

	def keypress(self, size, key):
		if key == "enter":
			self.callback(self.get_edit_text())
		elif key == "esc":
			self.callback("")
		else:
			return super(QuestionBox, self).keypress(size, key)
