from pysword.modules import SwordModules

modules = SwordModules("../ESV2011.zip")
found_modules = modules.parse_modules()

bible = modules.get_bible_from_module("ESV2011")
#print(dir(bible.get_structure().get_books()))
#print(bible.get_structure().get_books())
output = bible.get(books=["john"], chapters=[1], verses=range(1,3), clean=False)
print(output)
