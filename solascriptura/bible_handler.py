from pysword.modules import SwordModules
from bs4 import BeautifulSoup

class Bible(object):
	def __init__(self, version="KJV", path=None):
		self._modules = SwordModules(path)
		found_modules = self._modules.parse_modules()
		self._bible = self._modules.get_bible_from_module(version)
		self._verse_spacing = False
		self._paragraph_spacing = True

	def normalize(self, books, chapters=None, verses=None):
		_, book = self._bible.find_book(books)
		

	def get(self, books, chapters=None, verses=None):
		xml = list(self._bible.get_iter(books, chapters, verses, clean=False))
		if verses is None:
			verses = range(1, len(xml)+1)

		to_return = []

		for v, n in zip(xml, verses):
			soup = BeautifulSoup(v, "html.parser")
			#print(str(soup))
			title = None
			n = "  {:d}".format(n)
			# Eliminate notes
			for note in soup.findAll("note"):
				note.decompose()
			# Eliminate Strongs references
			for w in soup.findAll("w"):
				w.replaceWithChildren()
			# Capture titles
			for t in soup.findAll("title"):
				title = "".join(t.findAll(text=True))
				t.decompose()
			# Eliminate section tags
			for div in soup.findAll("div", {"type": "section"}):
				#if self._paragraph_spacing:
					#n = "\n{}".format(n)
				div.decompose()
			# Eliminate paragraph tags (and create spacing)
			for div in soup.findAll("div", {"type": "paragraph"}):
				if self._paragraph_spacing:
					#n = "\n\n   {}".format(n)
					div.replaceWith("\n")
				div.decompose()
			# Eliminate milestone tags
			for div in soup.findAll("div", {"type": "x-milestone"}):
				div.decompose()
			for chapter in soup.findAll("chapter"):
				chapter.decompose()
			# Parse quote marks
			for q in soup.findAll("q"):
				q.replaceWith(q.attrs["marker"])
			# Parse indents
			for l in soup.findAll("l"):
				if "eid" in l:
					l.decompose()
					continue
				else:
					l.replaceWith("\n" + ("    "*int(l["level"])))
			for lg in soup.findAll("lg"):
				lg.decompose()

			if title is not None:
				to_return.append(("title", "\n  {}\n\n".format(title)))
			verse_text = str(soup)
			if len(verse_text) != len(verse_text.lstrip()):
				n = verse_text[:len(verse_text) != len(verse_text.lstrip())] + n
			to_return.append(("note", "{}. ".format(n)))
			to_return.append(("text", "{}{}".format(verse_text.lstrip(), "\n" if self._verse_spacing else "")))

		return to_return
	
