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

import os
import tool
import gobject


"""--------------------------------------------------------------------------------------------"""
"""--------------------------- a class which stores an iconset --------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### if we like to use an ticker icon, it will be used by this program as an iconset. The actual
### image is then create dfrom this iconset (usualy by event_image). On my machine, it took to long
### to render the icons on every access, thatswhy this class buffers the iconset. Cause it usually
### holds the icon of a newsticker, the instances are placed in the sources (see one_source). See
### event_image._set how to use this class.
### the rendering is done, if you ask for the iconset by get(). Cause it might happen, that we have to
### get the icon first from the net, it takes time - maybe you have to wait for signal "icon_changed" or
### "icon_at_url_not_retrieved" till you could use it.
class IconBuffer(gobject.GObject):
	def __init__(self, filename= None, url = None, Stock = g.STOCK_MISSING_IMAGE):
		gobject.GObject.__init__(self)
		self.stock_iconsets = Stock_IconSets()
		self.__filename = filename
		self.__url = url
		self.__stock = Stock
		self.__iconset = None
		self.__pixbuf = None
		self.__pixbuf_active = None
		self.status = None ### Indicates the status: One of None, get_file, get_url or done
		self.t = None
	
	### you like to refresh the whole iconset, please do so.
	def reinit(self, filename= None, url = None, Stock = g.STOCK_MISSING_IMAGE):
		self.__filename = filename
		self.__url = url
		self.__stock = Stock
		self.__iconset = None
		self.get()
	
	### ask for the iconset, if not initialized, create one
	def get(self):
		if not(self.__iconset):
			self.__initialize()
		if not(self.__iconset):
			if self.status == 'get_url': return self.stock_iconsets.get(g.STOCK_CONVERT)
			else: return self.stock_iconsets.get(self.__stock)
		return self.__iconset
	
	### try to read the icon from file or fetch it from the net
	def __initialize(self):
		if self.__filename:
			if (self.__set_from_file()): return
		if self.__url:
			self.status = 'get_url'
			tasks.Task(self.__set_from_url_task())
	
	### read icon from cached file, create iconset, return True if successfully
	def __set_from_file(self):
		# check if actually trying to fetch icon from url, if true, kill task
		if self.t and self.t.Status() == None: self.t.Kill()
		self.status = 'get_file'
		if os.path.isfile(self.__filename):
			if self.__pixbuf: del self.__pixbuf; self.__pixbuf = None
			try:
				self.__pixbuf = g.gdk.pixbuf_new_from_file(self.__filename)
				self.__set_image()
			except (gobject.GError): return False
		else: return False
		self.status = 'done'; return True
	
	####fetch icon from url, if successfully, call __set_from_file
	def __set_from_url_task(self):
		#prog = tool.Win_ProgBar()
		#prog.start_pulse()
		
		# if there is another process still running, kill it
		if self.t and self.t.Status() == None: self.t.Kill(); self.t.Wait()
		if self.t and self.t.Status() == None: import signal; self.t.Kill(signal.SIGKILL); self.t.Wait()
		
		self.t = tool.urlretrieve(self.__url, self.__filename)
		yield None
		
		### wait a little bit till icon might be cached locally
		from news import HTTP_TIMEOUT
		for tick in range (0, HTTP_TIMEOUT):
			if self.t.Done() == 1: break
			yield tasks.TimeoutBlocker(1);
		
		### get rid of the started child-prozess
		if self.t.Status() == None: self.t.Kill(); self.t.Wait()
		if self.t.Status() == None: import signal; self.t.Kill(signal.SIGKILL); self.t.Wait()

		#prog.rem()
		
		if not(os.path.isfile(self.__filename)):
			self.emit("icon_at_url_not_retrieved")
			#rox.alert("Icon could not retrieved from url:\n" + self.__url)
				
		#### try to set from file
		self.__set_from_file()
	
	### creates self.__iconset out of self.__pixbuf
	def __set_image(self):
		#print "pixbuf " + str(self.__pixbuf)
		self.__iconset = g.IconSet(self.__pixbuf)
		tmp_pixbuf = self.__pixbuf.copy()
		tmp_pixbuf.saturate_and_pixelate(tmp_pixbuf, 5, g.FALSE)
		iconsrc = g.IconSource()
		iconsrc.set_pixbuf(tmp_pixbuf)
		iconsrc.set_state_wildcarded(g.FALSE)
		iconsrc.set_state(g.STATE_PRELIGHT)
		self.__iconset.add_source(iconsrc)
		self.emit("icon_changed")
	
gobject.signal_new("icon_changed", IconBuffer, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("icon_at_url_not_retrieved", IconBuffer, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())


"""--------------------------------------------------------------------------------------------"""
"""--------------------------- a class which stores all rendered Stock-Iconsets ---------------"""
"""--------------------------------------------------------------------------------------------"""
### Cause it took to long to render the iconsets everytime i needed them, i builded this class
### to keep iconsets, if once needed
class Stock_IconSets:
	def __init__(self):
		self.__sets = []

	### searches for the sotck-iconset, if not found, renders a new one
	def get(self, Stock):
		for set in self.__sets:
			if set['Stock'] == Stock: return set['iconset']
		new_iconset = self.__create_iconset_from_stock(Stock)
		self.__sets.append({'Stock' : Stock, 'iconset' : new_iconset})
		return new_iconset
	
	### as named, this method creates a new iconset form a stock icon
	def __create_iconset_from_stock(self, Stock):
		tmp_ebuf = g.EventBox()
		pixbuf = tmp_ebuf.render_icon(Stock, g.ICON_SIZE_SMALL_TOOLBAR, "")
		iconset = g.IconSet(pixbuf)
		tmp_pixbuf = pixbuf.copy()
		tmp_pixbuf.saturate_and_pixelate(tmp_pixbuf, 5, g.FALSE)
		iconsrc = g.IconSource()
		iconsrc.set_pixbuf(tmp_pixbuf)
		iconsrc.set_state_wildcarded(g.FALSE)
		iconsrc.set_state(g.STATE_PRELIGHT)
		iconset.add_source(iconsrc)
		return iconset
