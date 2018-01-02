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
            "book": "Matthew",
            "chapter": "1",
            "verse": ""
        }
        self.versions = {
            "default_path": ""
        }

        try:
            self.load_config() # Load config file, if it exists...
        except:
            self.save_config() # Otherwise, initialize a new one.

    def save_config(self):
        self.config = configparser.SafeConfigParser()
        self.config.add_section("last_read")
        self.config.set("last_read", "book", self.last_read["book"])
        self.config.set("last_read", "chapter", str(self.last_read["chapter"]))
        self.config.set("last_read", "verse", str(self.last_read["verse"]))
        self.config.add_section("versions")
        self.config.set("versions", "default_path", self.versions["default_path"]) # If none, PySword will search the SWORD data path

        with open(self.config_path, "wb") as cfg:
            self.config.write(cfg)
    
    def load_config(self):
        self.config = configparser.SafeConfigParser()
        self.config.read(self.config_path)

        self.last_read["book"] = self.config.get("last_read", "book")
        self.last_read["chapter"] = self.config.getint("last_read", "chapter")
        self.last_read["verse"] = (self.config.getint("last_read", "verse") or None)

        self.versions["default_path"] = self.config.get("versions", "default_path")
