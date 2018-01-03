import os
from os.path import expanduser
try:
	import configparser
except:
	import ConfigParser as configparser

class Config(object):
	def __init__(self):
		self.config_path = expanduser("~/.solascriptura")

		# Default configuration options
		self.last_read = {
			"version": "",
			"book": "Matthew",
			"chapter": "1",
			"verse": ""
		}
		self.modules = {
			"default_path": os.path.join(os.path.dirname(os.path.realpath(__file__)), "modules")
		}

		try:
			self.load_config() # Load config file, if it exists...
		except:
			self.save_config() # Otherwise, initialize a new one.

	def save_config(self):
		self.config = configparser.SafeConfigParser()
		self.config.add_section("last_read")
		self.config.set("last_read", "version", self.last_read["version"])
		self.config.set("last_read", "book", self.last_read["book"])
		self.config.set("last_read", "chapter", str(self.last_read["chapter"]))
		self.config.set("last_read", "verse", str(self.last_read["verse"]))
		self.config.add_section("modules")
		self.config.set("modules", "default_path", self.modules["default_path"]) # If none, PySword will search the SWORD data path

		with open(self.config_path, "w") as cfg:
			self.config.write(cfg)
	
	def load_config(self):
		self.config = configparser.SafeConfigParser()
		self.config.read(self.config_path)

		self.last_read["version"] = self.config.get("last_read", "version")
		self.last_read["book"] = self.config.get("last_read", "book")
		self.last_read["chapter"] = self.config.getint("last_read", "chapter")
		self.last_read["verse"] = (self.config.getint("last_read", "verse") or None)

		self.modules["default_path"] = self.config.get("modules", "default_path")
