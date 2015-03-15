#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information
from __future__ import generators
import rox
from rox import g, tasks
import rox.OptionsBox
from rox.OptionsBox import data

import os

import event_image

"""--------------------------------------------------------------------------------------------"""
"""--------------------------- My extensions to ROX.OptionsBox --------------------------------"""
"""--------------------------------------------------------------------------------------------"""
class OptionsBox(rox.OptionsBox.OptionsBox):
	def __init__(self, Options, options_group, options_xml, translation = None):
		self.__Options = Options
		rox.OptionsBox.OptionsBox.__init__(self, options_group, options_xml, translation = None)

	### just to show a image
	def build_image(self, node, image):
		"""<image>Filename</image>"""
		image = g.Image()
		Filename = rox.app_dir + "/" + data(node)
    		if os.path.exists(Filename):
    			image.set_from_file(Filename)
		else:
			image.set_from_stock(g.STOCK_MISSING_IMAGE,g.ICON_SIZE_SMALL_TOOLBAR)
		return [image]	
	
	### the follwing toggles are directly connected to some images, you have to use them if you
	### use the toggles too
	def build_activetip(self, node, image):
		"""<activetip>Text</activetip>"""
		self.activetip = ActiveTip()
		return [self.activetip]	
	def build_toggle_atip(self, node, label, option):
		"<toggle_atip name='...' label='...'>Tooltip</toggle_atip>"
		toggle = g.CheckButton(label)
		self.may_add_tip(toggle, node)
		def get():
			self.activetip.refresh(option, toggle.get_active())
			return str(toggle.get_active())
		def set():
			toggle.set_active(option.int_value)
			self.activetip.refresh(option, toggle.get_active())
		self.handlers[option] = (get, set)
		toggle.connect('toggled', lambda w: self.check_widget(option))
		return [toggle]

	def build_imagetip(self, node, image):
		"""<imagetip>Text</imagetip>"""
		self.imagetip = ImageTip()
		return [self.imagetip]	
	def build_toggle_itip(self, node, label, option):
		"<toggle_itip name='...' label='...'>Tooltip</toggle_itip>"
		toggle = g.CheckButton(label)
		self.may_add_tip(toggle, node)
		def get():
			self.imagetip.refresh(option, toggle.get_active())
			return str(toggle.get_active())
		def set():
			toggle.set_active(option.int_value)
			self.imagetip.refresh(option, toggle.get_active())
		self.handlers[option] = (get, set)
		toggle.connect('toggled', lambda w: self.check_widget(option))
		return [toggle]

	def build_labeltip(self, node, image):
		"""<labeltip>Text</labeltip>"""
		self.labeltip = LabelTip()
		return [self.labeltip]	
	def build_toggle_ltip(self, node, label, option):
		"<toggle_ltip name='...' label='...'>Tooltip</toggle_ltip>"
		toggle = g.CheckButton(label)
		self.may_add_tip(toggle, node)
		def get():
			self.labeltip.refresh(option, toggle.get_active())
			return str(toggle.get_active())
		def set():
			toggle.set_active(option.int_value)
			self.labeltip.refresh(option, toggle.get_active())
		self.handlers[option] = (get, set)
		toggle.connect('toggled', lambda w: self.check_widget(option))
		return [toggle]

	### the next section contains the main configuration,
	### see sources_dialog for more information.
	def build_tickerconf(self, node, label, option):
		"""<tickerconf>all tags as xml</tickerconf>"""
		import sources_dialog
		PrefTab = sources_dialog.SourcesDialog(self.__Options)
		self.may_add_tip(PrefTab, node)
		PrefTab.connect('changed_Conti', lambda w: self.check_widget(option))
		def get():
			return PrefTab.get_xml()
		def set():
			tasks.Task(PrefTab.set_from_xml(option.value))
		self.handlers[option] = (get, set)
		return [PrefTab]
	
	### shows the help
	def build_help(self, node, label):
		"""<help>gib ein Infofenster aus</help>"""
		import help
		HelpTab = help.Help_Book(self.__Options)
		return [HelpTab]
	
	### its a entry with an stock-icon to choose the file
	def build_fileentry(self, node, label, option):
		"<fileentry name='...' label='...'>Tooltip</fileentry>"
		# the open_file_dialog
		def open_file(widget, event):
			def set_file(widget):
				sel.hide()
				entry.set_text(sel.get_filename())
			def exit(widget):
				sel.hide()
			if event.button == 1:
				sel = g.FileSelection()
				sel.set_filename(entry.get_text())
				sel.connect("destroy", exit)
				sel.ok_button.connect("clicked", set_file)
				sel.cancel_button.connect("clicked", exit)
				sel.show()
		# the whole box
		box = g.HBox(False, 4)
		entry = g.Entry()
		button = event_image.EventImage(self.__Options, g.STOCK_OPEN, open_file, g.ICON_SIZE_SMALL_TOOLBAR, "choose file")
		
		if label:
			label_wid = g.Label(label)
			box.pack_start(label_wid, False, False, 0)
		
		box.pack_start(entry, False, False, 0)
		box.pack_start(button, False, False, 0)
		
		self.may_add_tip(entry, node)

		entry.connect('changed', lambda e: self.check_widget(option))

		def get():
			return entry.get_chars(0, -1)
		def set():
			entry.set_text(option.value)
		self.handlers[option] = (get, set)

		return [box]




"""--------------------------------------------------------------------------------------------"""
"""--------------------------- Changable images -----------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### The foollowing classes are vboxes, which contain images. These are connected to some
### options. If the Option-value is changed, refresh is called and image is modified
class LabelTip(g.VBox):
	def __init__(self):
		g.VBox.__init__(self)
		self.show()
		self.images = []
		self.images.append(Tip_Image(self, "label_tip_1.png", "always"))
		self.images.append(Tip_Image(self, "label_tip_2.png", "tt_l_frame"))
		self.images.append(Tip_Image(self, "label_tip_3.png", "tt_l_title"))
		self.images.append(Tip_Image(self, "label_tip_4.png", "tt_l_frame"))
		self.images.append(Tip_Image(self, "label_tip_5.png", "tt_l_desc"))
		self.images.append(Tip_Image(self, "label_tip_6.png", "tt_l_frame"))
		self.images.append(Tip_Image(self, "label_tip_7.png", "tt_l_link"))
		self.images.append(Tip_Image(self, "label_tip_8.png", "tt_l_ver"))
		self.images.append(Tip_Image(self, "label_tip_9.png", "always"))
	def refresh(self, option, state):
		for img in self.images:
			if option.name == "tt_l": img.saturate(state)
			else: img.check(option, state)

class ImageTip(g.VBox):
	def __init__(self):
		g.VBox.__init__(self)
		self.show()
		self.images = []
		self.images.append(Tip_Image(self, "image_tip_1.png", "always"))
		self.images.append(Tip_Image(self, "image_tip_2.png", "tt_i_frame"))
		self.images.append(Tip_Image(self, "image_tip_3.png", "tt_i_title"))
		self.images.append(Tip_Image(self, "image_tip_4.png", "tt_i_frame"))
		self.images.append(Tip_Image(self, "image_tip_5.png", "tt_i_desc"))
		self.images.append(Tip_Image(self, "image_tip_6.png", "tt_i_frame"))
		self.images.append(Tip_Image(self, "image_tip_7.png", "tt_i_src"))
		self.images.append(Tip_Image(self, "image_tip_8.png", "tt_i_link"))
		self.images.append(Tip_Image(self, "image_tip_9.png", "tt_i_ver"))
		self.images.append(Tip_Image(self, "image_tip_10.png", "always"))
	def refresh(self, option, state):
		for img in self.images:
			if option.name == "tt_i": img.saturate(state)
			else: img.check(option, state)

class ActiveTip(g.VBox):
	def __init__(self):
		g.VBox.__init__(self)
		self.show()
		self.image = Tip_Image(self, "active_tooltip.png", "always")
	def refresh(self, option, state):
		if option.name == "tt_a": self.image.saturate(state)
		else: self.image.check(option, state)

class Tip_Image(g.Image):
	def __init__(self, vbox, file, name):
		g.Image.__init__(self)
    		# first create a pixbuf from the image
		self.pxbuf = g.gdk.pixbuf_new_from_file(rox.app_dir + "/images/" + file)
		# then create a grey one for deactivated view
		self.sat_pxbuf = g.gdk.pixbuf_new_from_file(rox.app_dir + "/images/" + file)
		self.sat_pxbuf.saturate_and_pixelate(self.sat_pxbuf, 0.01, True)
		
		self.set_from_pixbuf(self.pxbuf)
		
		self.option = name	# remember connected option
		
		self.show()
		vbox.add(self)
	
	### check if option is active, then show or hide self
	def check(self, option, state):
		if option.name == self.option:
			if state == 1: self.show()
			else: self.hide()
	
	### check if value is active or not and show apropriate image
	def saturate(self, value):
		if value == 1: self.set_from_pixbuf(self.pxbuf)
		else: self.set_from_pixbuf(self.sat_pxbuf)
