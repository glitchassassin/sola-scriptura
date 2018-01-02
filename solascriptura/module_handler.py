import os

from pysword.modules import SwordModules

from .bible_handler import Bible

class Library(object):
    def __init__(self, library_path=None):
        self.library_path = library_path or os.path.join(os.path.dirname(os.path.realpath(__file__)), "modules")
        self.modules = {}
        for filename in os.listdir(self.library_path):
            if filename.endswith(".zip"):
                try:
                    zip_modules = SwordModules(os.path.join(self.library_path, filename))
                except:
                    raise # DEBUG - Remove when issues have been sorted out
                    continue
                discovered = zip_modules.parse_modules()
                for m in discovered:
                    self.modules[m] = Bible(m, zip_modules.get_bible_from_module(m))
                    if discovered[m]["feature"] == "NoParagraphs":
                        self.modules[m].use_paragraphs = False
    
    def get_bible(self, bible):
        return self.modules[bible]

    def list_bibles(self):
        return list(self.modules.keys())