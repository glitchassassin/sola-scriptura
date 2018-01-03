import os
import re

from bs4 import BeautifulSoup
from pysword.modules import SwordModules

class Library(object):
	def __init__(self, library_path):
		self.library_path = library_path
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
		if bible in self.modules:
			return self.modules[bible]
		return None

	def list_bibles(self):
		return list(self.modules.keys())

class Bible(object):
	def __init__(self, name, bible):
		self._bible = bible
		self.name = name
		self.use_paragraphs = True

	def get_books(self):
		return self._bible.get_structure().get_books()

	def get_canonical_name(self, book):
		books = self.get_books()
		for t in books:
			for b in books[t]:
				if b.name_matches(book):
					return b.name
		raise ValueError("{} does not match any books".format(book))

	def get(self, books, chapters=None, verses=None):
		xml = list(self._bible.get_iter(books, chapters, verses, clean=False))
		if verses is None:
			verses = range(1, len(xml)+1)
		elif isinstance(verses, int):
			verses = [verses]

		to_return = []

		for v, n in zip(xml, verses):
			soup = BeautifulSoup(v, "html.parser")
			#print(str(soup))
			title = None
			n = " {:d}. ".format(n)
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
				#if self.use_paragraphs:
					#n = "\n{}".format(n)
				div.decompose()
			# Eliminate paragraph tags (and create spacing)
			for para in soup.findAll("div", {"type": "paragraph"}):
				if "sid" in para.attrs and self.use_paragraphs:
					#n = "\n\n   {}".format(n)
					para.replaceWith("\n\n")
				else:
					para.decompose()
			for m in soup.findAll("milestone", {"type": "x-p"}):
				m.replaceWith("\n\n")
			# Eliminate milestone tags
			for div in soup.findAll("div", {"type": "x-milestone"}):
				div.decompose()
			# Eliminate chapter tags
			for chapter in soup.findAll("chapter"):
				chapter.decompose()
			# Eliminate book tags
			for div in soup.findAll("div", {"type": "book"}):
				div.decompose()
			# Parse quote marks
			for q in soup.findAll("q"):
				if q["marker"] != "":
					q.replaceWith(q["marker"])
				else:
					q.replaceWithChildren() # Words of Jesus are wrapped in <q> tags
			# Parse indents
			for l in soup.findAll("l"):
				if "eid" in l.attrs:
					l.decompose()
				else:
					l.replaceWith("\n" + "      "*int(l["level"]))
			for lg in soup.findAll("lg"):
				if "sid" in lg.attrs:
					lg.replaceWith("\n")
				else:
					lg.decompose()
			# Eliminate extraneous tags
			for d in soup.findAll("divinename"):
				d.replaceWith("".join(d.findAll(text=True)))
			for m in soup.findAll("milestone"):
				if m["type"] == "cQuote":
					m.replaceWith(m["marker"])
			for t in soup.findAll("transchange"):
				t.decompose()

			if title is not None:
				to_return.append(("title", "\n\n  {}\n".format(title)))
			verse_regex = re.compile("([ \n]*?)(\n*)( *)([^ \n].*)", re.DOTALL)
			results = verse_regex.match(str(soup))
			try:
				verse_text = results.group(4)
			except AttributeError:
				print("\"" + str(soup).replace(" ", ".") + "\"")
				raise
			n = results.group(1).replace(" ", "") + results.group(2) + results.group(3)[:max(len(results.group(3)) - len(n), 0)] + n
			to_return.append(("note", n))
			to_return.append(("text", "{}{}".format(verse_text, "\n" if not self.use_paragraphs else "")))

		return to_return
	
