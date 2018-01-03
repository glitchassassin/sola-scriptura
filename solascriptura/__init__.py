import urwid

from .gui_handler import Header, Reader, Footer, TableOfContentsPopup, VersionPopup, GoToPopup, SetupPopup, AlertPopup
from .config import Config
from .library import Library

def main():
	c = Controller()
	c.run()

class Controller(object):
	def __init__(self):
		self.handler = InputHandler()
		self.config = Config()
		self.library = Library(self.config.modules["default_path"])
		# Create sections
		self.header = Header()
		self.reader = Reader(self.config, self.header.set_version, self.header.set_passage)
		if self.config.last_read["version"]: # Remembered last version used
			self.reader.set_bible(self.library.get_bible(self.config.last_read["version"]))
		elif len(self.library.list_bibles()): # Otherwise, use first available version
			self.reader.set_bible(self.library.get_bible(self.library.list_bibles()[0]))
		last_passage = "{} {}{}".format(self.config.last_read["book"], 
										self.config.last_read["chapter"], 
										(":" + self.config.last_read["verse"]) if self.config.last_read["verse"] else "")
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
		self.handler.register(name="setup", action=self.launch_setup, key="f5")

		# Define loop
		self.loop = urwid.MainLoop(self.frame, self.palettes, unhandled_input=self.handler.handle)

		# Begin with setup, if necessary
		if len(self.library.modules) == 0:
			self.launch_setup()

	def run(self):
		self.loop.run()

	def quit(self):
		raise urwid.ExitMainLoop()

	# Popup controllers

	def launch_toc(self):
		if self.reader.bible is None:
			return # No TOC anyways - ignore
		self.loop.widget = TableOfContentsPopup(self.frame, self.reader, self.close_toc)
	def close_toc(self):
		self.loop.widget = self.frame

	def launch_version(self):
		if len(self.library.modules) == 0:
			return # No versions to pick from - ignore
		self.loop.widget = VersionPopup(self.frame, self.reader, self.library, self.close_version)
	def close_version(self):
		self.loop.widget = self.frame
	
	def launch_goto(self):
		if self.reader.bible is None:
			return # No TOC anyways - ignore
		self.loop.widget = GoToPopup(self.frame, self.reader, self.close_goto)
	def close_goto(self, error=None):
		self.loop.widget = self.frame
		if error:
			self.launch_alert(error)
	
	def launch_alert(self, message):
		self.loop.widget = AlertPopup(self.frame, message, self.close_alert)
	def close_alert(self):
		self.loop.widget = self.frame

	def launch_setup(self):
		self.loop.widget = SetupPopup(self.frame, self.config.modules["default_path"], self.close_setup)
	def close_setup(self, error=None):
		self.loop.widget = self.frame
		self.library = Library(self.config.modules["default_path"])
		if self.config.last_read["version"]: # Remembered last version used
			self.reader.set_bible(self.library.get_bible(self.config.last_read["version"]))
		elif len(self.library.list_bibles()): # Otherwise, use first available version
			self.reader.set_bible(self.library.get_bible(self.library.list_bibles()[0]))
		last_passage = "{} {}{}".format(self.config.last_read["book"], 
										self.config.last_read["chapter"], 
										(":" + self.config.last_read["verse"]) if self.config.last_read["verse"] else "")
		self.reader.go_to_passage_string(last_passage)
		if error:
			self.launch_alert(error)


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
	