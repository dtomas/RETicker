#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

import rox
from rox import g

from xml.dom import minidom
from xml.dom.minidom import Document
import xml.sax

import gobject
import os

import tool
import icon

"""--------------------------------------------------------------------------------------------"""
"""--------------------------- a class which holds all sources --------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### an instance of this class is hold in options. It ist always synchronized with __sources value
### and keeps a list of single sources. additionally it gives methods to get single_sources-values
### by giving a ticker-name
class Sources(gobject.GObject):
	def __init__(self, Options):
		gobject.GObject.__init__(self)
		self.__Options = Options
		self.sources = []	# a list of sources
		
		# this indicates the time to wait, if information will be changed in
		# Options Dialog (now 2 sec.)
		self.reinit_delay_call = tool.DelayCall(2, self.reinit_from_xml_)

	### returns a string which gives some information about actual sources
	def stat(self):
		source_count = len(self.sources)
		act_count = 0
		for i in self.sources:
			if i.get_active() == 1: act_count += 1
		return str(source_count) + "[all]/" + str(act_count) + "[active]"

	### this allows to change the status of a feed, feed is given
	def switch_feed_active(self, feed):
		source = self.get_by_ticker(feed.ticker)
		if not(source): return # maybe killed in between (shouldnt happen)
		if source.active == 1: source.active = 0
		else: source.active = 1
		self.get_by_ticker(feed.ticker).emit("change_active")
	
	"""----------------------------------------------------------------------------------"""
	""" 1. Methods to get special information about one source                           """
	"""----------------------------------------------------------------------------------"""
	### search the source which is described by a ticker-name (returns the first one)
	def get_by_ticker(self, ticker):
		# compare name with protocol, add it if not there
		if ticker.find("://") == -1: ticker = "http://" + ticker
		
		for source in self.sources:
			if source.get_ticker() == ticker: return source
		return None
	
	### methods to get special source fields if ticker name is known
	def get_active_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_active()
		else: return None
	def get_ticker_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_ticker()
		return None
	def get_icon_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_icon()
		return None
	def get_iconcache_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_iconcache()
		return None
	def get_iconset_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_iconset()
		return None
	def get_shownews_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_shownews()
		return None
	def get_news_age_by_date_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_news_age_by_date()
		return None
	def get_provides_date_info_by_ticker(self, ticker):
		if self.get_by_ticker(ticker): return self.get_by_ticker(ticker).get_provides_date_info()
		return None
	
	"""----------------------------------------------------------------------------------"""
	""" 2. Methods to synchronize this sources with option.value (in- and export)        """
	"""----------------------------------------------------------------------------------"""
	### export sources-information as xml-string. its the format used by options-field __sources
	### this allows reinit options.__sources field by actual sources structure
	### see options.py: self.__sources.value = self.sources.export_xml()
	def export_xml(self):
		doc = Document()
		doc_root = doc.createElement('Options')
		doc.appendChild(doc_root)
		for i in self.sources:
			root = doc.createElement('source')
			doc_root.appendChild(root)
			i._to_xml(root)
		return doc.toxml()
	
	### read sources form xml-string.
	def create_sources_from_xml(self, xml_string):
		sources = []
		try:
			doc=minidom.parseString(xml_string)
		except xml.sax.SAXParseException:
			rox.alert	("something stupid happend: your internal config is corrupt\n" \
					+ "maybe you have to remove your Config-file from\n\n" \
					+ rox.choices.save(rox.app_options.program, rox.app_options.leaf) + "\n\n" \
					+ "If this happens more than once,\n" \
					+ "please report this by email (see Readme.txt for address)")
			return sources
		xml_sources = doc.getElementsByTagName("source")
		for xml_source in xml_sources:
			new_source = one_source(self.__Options)
			new_source._from_xml(xml_source)
			sources.append(new_source)
		return sources
		
	### read sources, given by options-field __sources (first initialisation)
	### see options.py: self.sources.init_from_xml(self.__sources.value)
	def init_from_xml(self, xml_string):
		self.sources = self.create_sources_from_xml(xml_string)
	
	### copy (options)sources into used sources, if they keep stable for a while
	def reinit_from_xml(self, xml_string):
		self.reinit_delay_call.set_value(xml_string)
	def reinit_from_xml_(self, xml_string):
		tmp_sources = self.create_sources_from_xml(xml_string)
		# now tmp_sources holds the new configuration, its time to copy this into old one
		
		# go through all existing sources
		i = 0
		while (i < len(self.sources)):
			found = False
			# try to find them in new sources
			for tmp_source in tmp_sources:
				if tmp_source.get_ticker() == self.sources[i].get_ticker():
					found = True
					self.sources[i].copy(tmp_source);
					break
			# actual source is not in new sources, kill it
			if not(found):
					#print "source killed"
					self.sources[i].emit("source_killed", self.sources[i].get_ticker())
					self.sources.pop(i)
			else: i += 1
		
		# now its time to add new sources
		for source in tmp_sources:
			if self.get_by_ticker(source.get_ticker()): continue
			source.set_provides_date_info(0)
			self.sources.append(source)
			#print "source added"
			self.emit("source_added", self.sources[i])
		
gobject.signal_new("source_added", Sources, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,  (gobject.TYPE_PYOBJECT,))


"""--------------------------------------------------------------------------------------------"""
"""--------------------------- a class which holds one source ---------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### this class hold all the information of one source, see Options-Dialog to chekout what this
### means. Additionally it holds the iconset of the icon (see icon.py)
class one_source(gobject.GObject):
	def __init__(self, Options):
		gobject.GObject.__init__(self)
		self.__Options = Options
		self.active = None
		self.ticker = None
		self.icon = None
		self.iconcache = None
		self.iconset = None  		# stores the icon as a IconSet with different states
		self.shownews = None
		self.news_age_by_date = None
		self.provides_date_info = None
	
	"""----------------------------------------------------------------------------------"""
	""" 1. Methods to get special information about one source                           """
	"""----------------------------------------------------------------------------------"""
	### its better to access field by the get_* methods, values might be changed on access
	def get_active(self): return self.active
	def get_ticker(self):
		if self.ticker.find("://") == -1: return "http://" + self.ticker
		else: return self.ticker
	def get_icon(self):
		icon = self.icon
		if icon == "":
			pos = self.ticker[8:].find("/")
			if pos <> -1: pos = pos + 8
			if pos <> -1: icon =  self.ticker[:pos] + "/favicon.ico"
			else:	icon =  self.ticker + "/favicon.ico"
		else:
			if icon.find("://") == -1: icon = "http://" + icon
		return icon
	def get_iconcache(self):
		iconcache = self.iconcache
		if iconcache == "":
			iconcache = tool.cache_filename(self.__Options.icon_cache_dir.value, self.get_icon())
		return iconcache
	def get_iconset(self): 
		if not(self.iconset):
			self.iconset = icon.IconBuffer(self.get_iconcache(), self.get_icon())
			self.connect("icon_changed", lambda x,y: self.emit("change_iconset"))
		return self.iconset
	def get_shownews(self): return self.shownews
	def get_news_age_by_date(self): return self.news_age_by_date
	def get_provides_date_info(self): return self.provides_date_info
	
	"""----------------------------------------------------------------------------------"""
	""" 2. Methods to set value of one source                                            """
	"""----------------------------------------------------------------------------------"""
	def set_provides_date_info(self, value):
		if self.provides_date_info == None or self.provides_date_info <> value:
			self.provides_date_info = value;
			return True
		return False

	### copy information from one source to another. this is better than replacing the source
	### cause anywhere else there might be a reference to this instance.
	def copy(self, source):
		if self.active <> source.active: self.active = source.active; self.emit("change_active")
		refresh_icon = (self.icon <> source.icon or self.iconcache <> source.iconcache)
		if self.icon <> source.icon: self.icon = source.icon; self.emit("change_icon")
		if self.iconcache <> source.iconcache: self.iconcache = source.iconcache; self.emit("change_iconcache")
		if refresh_icon:
			if self.iconset: self.iconset.reinit(self.get_iconcache(), self.get_icon())
		if self.shownews <> source.shownews: self.shownews = source.shownews; self.emit("change_shownews")
		if self.news_age_by_date <> source.news_age_by_date: self.news_age_by_date = source.news_age_by_date; self.emit("change_news_age_by_date")
		if self.provides_date_info <> source.provides_date_info: self.provides_date_info = source.provides_date_info; self.emit("change_provides_date_info")


	"""----------------------------------------------------------------------------------"""
	""" 3. Methods to synchronize this sources with option.value (in- and export)        """
	"""----------------------------------------------------------------------------------"""
	def _to_xml(self, parent):
		def createNode(doc, name, data):
			node = doc.createElement(name)
			node.appendChild(doc.createTextNode(data))
			return node
		doc = parent.ownerDocument
		parent.appendChild(createNode(doc, 'active', str(self.active)))
		parent.appendChild(createNode(doc, 'ticker', self.ticker))
		parent.appendChild(createNode(doc, 'icon', self.icon))
		parent.appendChild(createNode(doc, 'iconcache', self.iconcache))
		parent.appendChild(createNode(doc, 'shownews', str(self.shownews)))
		parent.appendChild(createNode(doc, 'news_age_by_date',\
			str(self.news_age_by_date)))
		parent.appendChild(createNode(doc, 'provides_date_info',\
			str(self.provides_date_info)))
		return doc
	
	def _from_xml(self, xml_source):
		self.active = tool.getintdata(xml_source, "active")
		self.ticker = tool.getdata(xml_source, "ticker")
		self.icon  = tool.getdata(xml_source, "icon")
		self.iconcache = tool.getdata(xml_source, "iconcache")
		self.shownews = tool.getintdata(xml_source, "shownews")
		self.news_age_by_date = tool.getintdata(xml_source, "news_age_by_date")
		self.provides_date_info = tool.getintdata(xml_source, "provides_date_info")

gobject.signal_new("source_killed", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE,  (gobject.TYPE_PYOBJECT,))

gobject.signal_new("change_active", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_ticker", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_icon", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_iconcache", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_iconset", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_shownews", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_news_age_by_date", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("change_provides_date_info", one_source, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())

