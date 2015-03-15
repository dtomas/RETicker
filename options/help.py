#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information
import rox
from rox import g
import os
import tool

"""--------------------------------------------------------------------------------------------"""
"""----------------------------- Help Book (different pages contain different languages) ------"""
"""--------------------------------------------------------------------------------------------"""
### this class may show you some help - its a new version with a link to open a local browser.
class Help_Book(g.VBox):
	def __init__(self, Options):
		self.__Options = Options
		g.VBox.__init__(self)
		button = g.Button("Open html-formatted Help-Files")
		button.connect("clicked", self.open_page)
		self.pack_start(button, g.FALSE, g.FALSE, 3)
		notebook = Help_Book_orig()
		self.add(notebook)
		self.show_all()
		
	def open_page(self, dummy):
		localHelpPage = os.path.join(rox.app_dir, "Help/index.html")
		tool.openPage(localHelpPage, self.__Options)


### this class may show you some help. Help files are in Help directory named like Help_de.txt
class Help_Book_orig(g.Notebook):
	def __init__(self):
		g.Notebook.__init__(self)
		self.set_scrollable(True)
		
		#~ # search all Help_XX.txt files in dir and use them as pages in HelpBook
		#~ a = os.listdir(os.path.join( rox.app_dir, "Help/"))
		#~ for name in a:
			#~ filename = os.path.join(rox.app_dir, "Help/", name)
			#~ if not(os.path.isfile(filename)): continue
			#~ if not(name[:5] == "Help_"): continue
			#~ new_help = Help_Container(open(filename))
			#~ self.add(new_help)
			#~ self.set_tab_label_text(new_help, name[name.find('_')+1:name.find('.')])
		
		# I't easyer to set them directly, it will be changed later
		def add_help(filename, labeltext):
			new_help = Help_Container(open(os.path.join(rox.app_dir, "Help/", filename)))
			self.add(new_help)
			self.set_tab_label_text(new_help, labeltext)
		
		add_help("Help_de.txt", "Anleitung v.0.4.5")
		add_help("Help_en.txt", "Manual v.0.4.3")
		
		self.show_all()

### this class contains the actual help-message
class Help_Container(g.Frame):
	def __init__(self, file):
		g.Frame.__init__(self)
		
		swin=g.ScrolledWindow()
		swin.set_policy(g.POLICY_AUTOMATIC,g.POLICY_AUTOMATIC)
		swin.show()
		self.add(swin)
		
		ebox = g.EventBox()
		ebox.show()
		ebox.modify_bg(g.STATE_NORMAL,ebox.get_colormap().alloc_color('white'))
		swin.add_with_viewport(ebox)
		
		# use some boxes to get some borders around the text
		vbox = g.VBox()
		vbox.show()
		ebox.add(vbox)
		
		hbox = g.HBox()
		hbox.show()
		vbox.pack_start(hbox,g.FALSE,g.FALSE,0)
		
		label = g.Label()
		hbox.pack_start(label,g.FALSE,g.FALSE,15)
		
		#  get and set the text
		textbuf = g.TextBuffer(None)
 		text = unicode(file.read(), 'iso-8859-1')
		file.close()
		
		label.set_markup(text)
		label.set_line_wrap(True)
		label.set_size_request(280,-1)
		label.show()

		# and now its time to present it
		self.set_size_request(345,345)
		self.show()
