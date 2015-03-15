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

from xml.dom import minidom
from xml.dom.minidom import Document
import xml.sax

import os
import time
import gobject

import tool
import feed

HTTP_TIMEOUT = 20 ### This is the timeout for http-connections in seconds
		  ### cause there are started as special Tasks by fork()
		  ### there is no blocking while trying to reach the server

"""--------------------------------------------------------------------------------------------"""
"""------------------------------ news - The Class which holds the news -----------------------"""
"""--------------------------------------------------------------------------------------------"""
### The news class is holding a list of feeds where the messages are stored. Additionally it
### holds some methods to retrieve the news
### The Class contains 5 main sections
### 1. Methods to get news structure parallel to Options.sources
### 2. common Methods
### 3. Import of xml-data into lower structures (feeds, msgs) used by 4. and 5.
### 4. Methods for xml in- or export (reading and saving news to cache)
### 5. Methods to refresh the news and the icons
### Warning: Cause module news contains a signal connection to a signal from __Options, it will
### not be removed from memory while removing any other refrence to this instance
class news(gobject.GObject):
	def __init__(self, Options, box):
		gobject.GObject.__init__(self)
		self.__Options = Options
		self.__box = box		# this is needed for directig the output
		
		self.feeds = []			# here are the news stored
		
		self.__refresh_possible = True		# to block refresh-requests
		self.__manual_refresh_possible = True	# to block manual refresh-requests
		self.__refreshtimeout = None		# pointer to the refresh-timeout
		self.__lastrefresh = time.time()	# last_refresh_time

		self.Cons = tool.Connections()
		self.Cons.connect(self.__Options.sources, "source_added", self.add_source)
		
		# first init the structure by sources, but dont refresh them (cause they willl blocking each other)
		for source in self.__Options.sources.sources:
			self.add_source(None, source, False)
		
		tasks.Task(self.import_xml())	# then fill the struture from cache
		
	def disconnect(self, dummy=None): self.Cons.disconnect_all()

	"""----------------------------------------------------------------------------------"""
	""" 1. Methods to get news structure parallel to Options.sources                     """
	"""----------------------------------------------------------------------------------"""
	### create for a specific source a (empty) feed and add this to self.feeds[]
	def add_source(self, dummy, source, refresh = True):
		fd = feed.feed(self.__Options, source)
		fd.feed_nr = len(self.feeds)
		self.Cons.connect(source, "source_killed", self.kill_feed)
		self.feeds.append(fd)
		if refresh:
			#print "####### Try to refresh new feed"
			tasks.Task(self.refresh_feed(fd))
	
	### remove a feed (or all feeds, but there should be only one) with a given
	### ticker (used as id) from self.feeds
	def kill_feed(self, source, ticker):
		self.Cons.disconnect(source, "source_killed")
		i = 0
		while i < len(self.feeds):
			if ticker == self.feeds[i].get_ticker(): self.feeds.pop(i)
			else: i += 1
		self.emit("feed_killed", i)
				
	"""----------------------------------------------------------------------------------"""
	""" 2. common Methods                                                                """
	"""----------------------------------------------------------------------------------"""
	### return a feed by the given ticker
	def get_by_ticker(self, ticker):
		for fd in self.feeds: 
			if ticker == fd.get_ticker(): return fd
		return None
		
	### stat returns some Information about the news-feeds, like number of feeds at all
	### and number of active feeds. Includes Information abaout Messages
	def stat(self):		return self.__str__()
	def __str__(self):
		stat = { \
			'all_feed_count' : len(self.feeds) , \
			'act_feed_count' : 0, \
			'all_msg_count' : 0	, \
			'act_msg_count' : 0	, \
			'new_msg_count' : 0	, \
			}
		for fd in self.feeds: stat = fd.stat(stat)
		return  "feeds: " + str(stat['all_feed_count']) + "[all]/" + \
				str(stat['act_feed_count']) + "[active] " + \
			"msg:" + str(stat['all_msg_count']) + "[all]/" + \
				str(stat['act_msg_count']) + "[active]/" + \
				str(stat['new_msg_count']) + "[new]"


	"""----------------------------------------------------------------------------------"""
	""" 3. Import of xml-data into lower structures (feeds, msgs) used by 4. and 5.      """
	"""----------------------------------------------------------------------------------"""
	### read xml-formatted data. First has to be decided, which kind of feed-format
	### the xml-doc is (it had to be changed in a more standard way)
	def read_xml(self, xmldoc, ticker = None):
		### there are different types of feed-protocols possible
		### 'news' is the cache-format, fallback is a try to get the rest
		types = ['rdf:RDF', 'rss', 'news', 'fallback']
		for type in types:
			news_feeds = xmldoc.getElementsByTagName(type)
			if len(news_feeds) > 0: break

		if type == 'news':
			feeds = xmldoc.getElementsByTagName('feed')
			for node in feeds: self.read_xml_childNode(node, type, ticker)
		elif type <> 'fallback':
			for node in news_feeds: self.read_xml_childNode(node, type, ticker)
		else: self.read_xml_childNode(xmldoc, type, ticker)

	### convert xml_data into accessible feed information; if ticker is not given, read ticker
	### information from xmldoc (happens if read from cache)
	def read_xml_childNode(self, xmldoc, type, ticker = None):
		### ticker - field to recognize the feed in sources - cached data contains ticker
		if type == 'news':
			ticker = tool.getdata(xmldoc, "ticker") # This is used to recognize the feed
		
		fd = self.get_by_ticker(ticker)
		if not(fd): return  ### feed not found in sources, might happen if reading cached data
		fd._from_xml(xmldoc, type, self.__box)

	### calculate the time till next refresh (of all sources) should happen
	def time_to_next_refresh(self):
		if self.__refreshtimeout <> None:
			return self.__Options.refresh_time.int_value - \
				(time.time() - self.__lastrefresh)/60
		else: return None
	
	"""----------------------------------------------------------------------------------"""
	""" 4. Methods for xml in- or export (reading and saving news to cache)              """
	"""----------------------------------------------------------------------------------"""
	### export actual news feeds in xml-file
	def export_xml(self):
		if not self.__Options.xml_cache.value: return	# Saving is disabled
		
		doc = Document()
		root = doc.createElement('news')
		doc.appendChild(root)
		for i in self.feeds: i._to_xml(root)
			
		file = open(self.__Options.xml_cache.value, 'w')
		doc.writexml(file)
		file.close()
		
		print "Export xml done      (" + self.stat() + ")"
	
	### import news information from previously saved xml-file (usually started as
	### Tasks) if done, emit signal and start_refresh of news
	def import_xml(self):
		if self.__Options.v: print "import cached news ..."
		if not os.path.isfile(self.__Options.xml_cache.value):
			print "No cached news found - initialising"
			self.emit("cached_news_read"); self.start_refresh(); return
		self.__box.status("import cached news ...", g.STOCK_CONVERT)
		yield None
		
		try:	doc=minidom.parse(self.__Options.xml_cache.value)
		except (xml.parsers.expat.ExpatError, xml.sax.SAXParseException):  ### only happens if saving was interrupted
			self.__box.status("parse error in cached news ...", g.STOCK_CANCEL)
			rox.alert("parse error in cached news file:\n" + self.__Options.xml_cache.value)
			yield tasks.TimeoutBlocker(2);
			self.emit("cached_news_read"); self.start_refresh(); return
		
		#root = doc.documentElement
		self.read_xml(doc)
		
		if self.__Options.v: print "Cached news imported (" + self.stat() + ")"
		print "Cached news imported (" + self.stat() + ")"
		self.emit("cached_news_read")
		self.start_refresh();

	"""----------------------------------------------------------------------------------"""
	""" 5. Methods to refresh the news and the icons                                     """
	"""----------------------------------------------------------------------------------"""
	### two methods to add and remove the refresh-timeouts
	def add_refresh(self):
		if self.__refreshtimeout == None:
			#print "refresh_timeout added"
			self.__refreshtimeout = g.timeout_add(60000*self.__Options.refresh_time.int_value, self.start_refresh)
			#~ self.__refreshtimeout = g.timeout_add(600*self.__Options.refresh_time.int_value, self.start_refresh)
	def rem_refresh(self):
		if self.__refreshtimeout <> None:
			#print "refresh_timeout removed"
			g.timeout_remove(self.__refreshtimeout);
			self.__refreshtimeout = None

	### start the tasks to refetch the icons and the news feeds
	def start_refresh(self, dumy = None):
		if self.__Options.v: print "refresh Ticker"
		
		#tasks.Task(self.get_icons_for_all_feeds())
		tasks.Task(self.get_news_for_all_feeds())
		
		self.__lastrefresh = time.time()
	
	### it's now done in icon.py - see this file
	#~ ### if the iconc still in cache this method does nothing. if not they will be fetched.
	#~ def get_icons_for_all_feeds(self):
		#~ for feed in self.feeds:
			#~ ### catch icon if feed is active and icon is not in cache
			#~ if feed.get_active() == 1 and not(os.path.isfile(feed.get_iconcache())):
				#~ icon = feed.get_icon()
				#~ self.__box.status("Getting Icon from " + icon, g.STOCK_JUMP_TO)
				#~ yield None

				#~ t = tool.urlretrieve(icon, feed.get_iconcache())
				#~ ### wait a little bit till icon might be cached locally
				#~ for tick in range (0, HTTP_TIMEOUT):
					#~ if t.Done() == 1: break
					#~ yield tasks.TimeoutBlocker(1);
				#~ ### get rid of the started child-prozess
				#~ if t.Status() == None: t.Kill(); t.Wait()
				#~ if t.Status() == None: import signal; t.Kill(signal.SIGKILL); t.Wait()
				
				#### now check if file is here
				#~ if not(os.path.isfile(feed.get_iconcache())):
					#~ iconcache = rox.app_dir+"/AppIcon.xpm"
					#~ self.__box.status("Icon at " + icon + " not retrieved",g.STOCK_CANCEL)
					#~ yield tasks.TimeoutBlocker(2)
		
	### for every feed in cache try to fetch the news
	def get_news_for_all_feeds(self):		
		### to prevent double refreshings, there is a check if (regularily)
		### refreshing is still going on
		if self.__refresh_possible:
			self.__refresh_possible = False
		else:
			self.__box.status("New refresh request blocked, refresh still going on", g.STOCK_CANCEL)
			return
		yield None
		### remove timeouts cause refreshing may take to long (shouldnt happen)
		self.rem_refresh()	### timeout is once again added after completing check_feed_task

		for feed in self.feeds:
			if feed.get_active() == 1: 
				ticker = feed.get_ticker()
				self.__box.status("Checking " + ticker + " ...", g.STOCK_CONVERT, feed.get_iconcache())
				yield None
				
				cache_file = tool.cache_filename(self.__Options.icon_cache_dir.value, ticker)
				t = tool.urlretrieve(ticker, cache_file)
				
				### wait a little bit till feed might be cached locally
				for tick in range (0, HTTP_TIMEOUT):
					if t.Done() == 1: break
					yield tasks.TimeoutBlocker(1);
				
				### get rid of the started child-prozess
				if t.Status() == None: t.Kill(); t.Wait()
				if t.Status() == None: import signal; t.Kill(signal.SIGKILL); t.Wait()
				
				### now check if file is here
				try:
					cached_feed = open(cache_file, 'r');
				except (IOError, EOFError):
					#~ print "could not open url " + ticker
					self.__box.status("Could not open url: " + ticker + " ...", g.STOCK_CANCEL, feed.get_iconcache())
					yield tasks.TimeoutBlocker(2); self.__refresh_possible = True; continue
				try:
					xmldoc = minidom.parse(cached_feed)
				except (xml.parsers.expat.ExpatError, xml.sax.SAXParseException):
					self.__box.status("No Valid xml found at " + ticker + " ...", g.STOCK_CANCEL, feed.get_iconcache())
					yield tasks.TimeoutBlocker(2);
					del cached_feed; 
					try:
						os.remove(cache_file) ### remove cache_file, no longer needed
					except (OSError):
						self.__box.status("thats strange, file " + cache_file + " not found ...", g.STOCK_CANCEL, feed.get_iconcache())
					self.__refresh_possible = True; continue
				yield None
		
				### read the contents of the locally cached news-feed
				self.read_xml(xmldoc, ticker)
				self.emit("refresh_feed_done", feed)
						
				del cached_feed; 
				try:
					os.remove(cache_file) ### remove cache_file, no longer needed
				except (OSError):
					self.__box.status("thats strange, file " + cache_file + " not found ...", g.STOCK_CANCEL, feed.get_iconcache())
			elif self.__Options.v: print str(feed) + "not refreshed cause not active"
		print "Refresh done         (" + self.stat() +")"
		yield None
		
		### Data refreshed, save it (its better to do it now then loose it later ;)
		### It is also possible to save it only while killing the prog, maybe its
		### a good place to do a consistency check ?
		self.export_xml()
		
		### allow refresh again and set timer
		self.__refresh_possible = True
		self.add_refresh()
	
	### this is nearly the same like the method above, the difference is that this method
	### refreshes only one feed
	def refresh_feed(self, feed):
		### to prevent double refreshings, there is a check if (regularily)
		### refreshing is still going on
		if self.__manual_refresh_possible:
			self.__manual_refresh_possible = False
		else:	return
		
		ticker = feed.get_ticker()
		self.__box.status("Checking " + ticker + " ...", g.STOCK_CONVERT, feed.get_iconcache())
		yield None
		
		cache_file = tool.cache_filename(self.__Options.icon_cache_dir.value, ticker) + "_manually"
		prog = tool.Win_ProgBar()
		prog.start_pulse()
		t = tool.urlretrieve(ticker, cache_file)
		
		### wait a little bit till feed might be cached locally
		for tick in range (0, HTTP_TIMEOUT):
			if t.Done() == 1: break
			yield tasks.TimeoutBlocker(1);
		
		### get rid of the started child-prozess
		if t.Status() == None: t.Kill(); t.Wait()
		if t.Status() == None: import signal; t.Kill(signal.SIGKILL); t.Wait()
		
		prog.rem()

		### now check if file is here
		try:
			cached_feed = open(cache_file, 'r');
			xmldoc = minidom.parse(cached_feed)
		except (IOError, EOFError):
			rox.alert("could not open url :\n" + ticker)
			self.__box.status("Could not open url: " + ticker + " ...", g.STOCK_CANCEL, feed.get_iconcache())
			yield tasks.TimeoutBlocker(2); self.__manual_refresh_possible = True; return
		#~ except (xml.parsers.expat.ExpatError, xml.sax.SAXParseException):
			#~ rox.alert("error in parsing feed from :\n" + ticker)
			#~ self.__box.status("No Valid xml found at " + ticker + " ...", g.STOCK_CANCEL, feed.get_iconcache())
			#~ yield tasks.TimeoutBlocker(2);
			#~ del cached_feed;
			#~ try:
				#~ os.remove(cache_file) ### remove cache_file, no longer needed
			#~ except (OSError):
				#~ self.__box.status("thats strange, file " + cache_file + " not found ...", g.STOCK_CANCEL, feed.get_iconcache())
			#~ self.__manual_refresh_possible = True; return
		yield None

		### read the contents of the locally cached news-feed
		self.read_xml(xmldoc, ticker)
		self.emit("refresh_feed_done", feed)
				
		del cached_feed
		try:
			os.remove(cache_file) ### remove cache_file, no longer needed
		except (OSError):
			self.__box.status("thats strange, file " + cache_file + " not found ...", g.STOCK_CANCEL, feed.get_iconcache())
		### allow manual refresh again
		self.__manual_refresh_possible = True

gobject.signal_new("feed_killed", news, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("refresh_feed_done", news, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("cached_news_read", news, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
