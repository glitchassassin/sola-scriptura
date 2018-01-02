import urwid

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
		