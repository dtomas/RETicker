#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

from __future__ import generators

import rox
from rox import g

import gobject
from xml.dom import Node, minidom
from xml.dom.minidom import Document
				
import event_image
import tool
import sources_dialog_page

"""--------------------------------------------------------------------------------------------"""
"""--------------------------- The Sources Dialog ---------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### Thsi class gives you a container, which is included in Standrad rox Options-Dialog to edit
### the sources. All Information about the sources are stored in xml. The xml-string itself is
### stored as a single variable in rox-options.
class SourcesDialog(g.VBox):
	def __init__(self, Options):
		self.__Options = Options
		self.pageCount = 0
		
		g.VBox.__init__(self, g.FALSE, 3)
		self.tooltip = g.Tooltips(); self.tooltip.enable()
		
		hbox = g.HBox(g.FALSE, 0)

		self.button_new = rox.ButtonMixed(g.STOCK_NEW, "New Source")
		self.button_new.connect('clicked', self.add_Page)
		self.tooltip.set_tip(self.button_new, "click to create a new source")
		
		self.button_kill = rox.ButtonMixed(g.STOCK_DELETE, "Kill Source")
		self.button_kill.connect('clicked', self.kill_Page)
		self.tooltip.set_tip(self.button_kill, "click to kill actual source without further questions")
		
		hbox.pack_start(self.button_new, g.FALSE, g.FALSE, 0)
		hbox.pack_start(self.button_kill, g.FALSE, g.FALSE, 3)
		self.pack_start(hbox, g.FALSE, g.FALSE, 3)
		
		self.notebook = g.Notebook()
		self.notebook.set_scrollable(True)
		
		self.pack_start(self.notebook, g.FALSE, g.FALSE, 0)
		
		self.show_all()
		
		self.Cons = tool.Connections()
		self.connect("destroy", self.disconnect_all)
	
	### remove all connection if destroyed
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()
	
	### kill page if button was pressed
	def kill_Page(self, dummy):
		killpage = self.notebook.get_nth_page(self.notebook.get_current_page())
		
		# if there was not ticker or icon, it is'nt really a changing of options
		change = (killpage.ticker <> "" or killpage.icon <> "")
		
		self.Cons.disconnect(killpage, 'changed_Page')
		self.Cons.disconnect(killpage, 'refresh_icon_Page')
		self.Cons.disconnect(killpage, 'refresh_feed_Page')
		self.notebook.remove_page(self.notebook.get_current_page())
		
		self.pageCount -= 1
		# if there is no page left, hide the kill_page button
		if self.pageCount == 0: self.button_kill.hide()
		
		if change: self.emit('changed_Conti')
	
	### next method is used as a callback (without value) and to set sources
	### the dummy variable is given if button new_page is pressed, just ignore it
	def add_Page(self, dummy, value = None):
		newpage = sources_dialog_page.SourcesDialogPage(self.__Options)
		newpage.show()
		self.notebook.append_page(newpage, newpage.icon_image_tab)
		self.pageCount += 1
		self.button_kill.show()
		
		newpage.set(value)
		
		self.Cons.connect(newpage, 'changed_Page', self.changed_Page)
		self.Cons.connect(newpage, 'refresh_icon_Page', self.refresh_icon_Page)
		self.Cons.connect(newpage, 'refresh_feed_Page', self.refresh_feed_Page)
	
		if not(value):
			self.notebook.set_current_page(self.notebook.page_num(newpage))	
			newpage.ticker_entry.grab_focus()		
	
	### some callbacks from SourcesDialogPages, just emit signals further
	def changed_Page(self, dummy):
		if self.__Options.v: print "SIGNAL: changed Page " + str(self.notebook.get_current_page())
		self.emit('changed_Conti')
	def refresh_icon_Page(self, dummy, ticker): self.emit('refresh_icon_Conti', ticker)
	def refresh_feed_Page(self, dummy, ticker): self.emit('refresh_feed_Conti', ticker)
	
	### export sources definitions to xml-string, thisone is stored in Options
	def get_xml(self):
		doc = Document()
		doc_root = doc.createElement('Options')
		doc.appendChild(doc_root)
		for i in range(0, self.pageCount):
			root = doc.createElement('source')
			doc_root.appendChild(root)
			self.notebook.get_nth_page(i)._to_xml(root)
		return doc.toxml()

	### import sources from xml-string
	def set_from_xml(self, config):
		# try to remember current page
		currentPage = self.notebook.get_current_page()
		
		# remove all pages, if there where some
		for i in range(0,self.pageCount):
			self.notebook.remove_page(0)
		self.disconnect_all()
		self.pageCount = 0
		self.button_kill.hide()
		yield None
		
		# now add pages found in xml-string
		doc = minidom.parseString(tool.unxml_wo_tags(config))
		for i in doc.getElementsByTagName("source"):
			self.add_Page(None, i); yield None
		
		# restore current page
		if currentPage <> -1: self.notebook.set_current_page(currentPage)
		
gobject.signal_new("changed_Conti", SourcesDialog, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_feed_Conti", SourcesDialog, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("refresh_icon_Conti", SourcesDialog, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
