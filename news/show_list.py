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
import gobject

import news
import tool

allrefs = 0


"""--------------------------------------------------------------------------------------------"""
"""------------------------------ The Container Which holds the News --------------------------"""
"""--------------------------------------------------------------------------------------------"""
### ShowList Class holds the news, ore better, it gives a view to the news. They are actually
### hold in news, whoich is now part of show_list. Maybe they are going together in future Versions
### or they will be really separated, like originally planned, to enable different views of the
### same sources
### For the moment show-list is more the connection to the ticker (switch to next msg etc.) while
### news is the connection to the real world :=)


"""--------------------------------------------------------------------------------------------"""
"""------------------------------ Show_List The View of the News ------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### The Class contains 3 main sections
### 1. Methods for communication with Parent and Childs, or to open pages etc.
### 2. Methods to move forwards or backwards in Ticker, give next/prev message by regularily 
### 		updates and get aktual Ticker-message etc
### 3. Methods to move forwards or backwards in ActiveTooltip

class show_list(gobject.GObject):  			# has to be a gobject to enable signals
	def __init__(self, Options, box):		# gets Options an for the Output also a box
		gobject.GObject.__init__(self)
		
		self.__Options = Options		# given as params
		self.__box = box
		
		self.__news = news.news(Options, box)	# create a news object, which hold the news
		self.feeds = self.__news.feeds		# and connect to feeds there
		
		### some local values to recognize, where we are
		self.__fd_count = None			# Positon in news.feeds
		self.__msg_index = None			# msg-number in this feed
		
		self.__error = ""			# holds the last error msg
		
		self.__updatetimeout = None		# holds timeout for next update
		
		self.__updating = False			# blocks updating if still in process
		
		self.__news.connect("cached_news_read", self.cached_news_read)
		self.__news.connect("refresh_feed_done", self.refresh_feed_done)
		self.__news.connect("feed_killed", self.feed_killed)



	"""----------------------------------------------------------------------------------"""	
	""" 1. Methods for communication with Parent and Childs, or to open pages etc        """
	"""----------------------------------------------------------------------------------"""
	### connect some methods directly to methods of the self.__news instance
	def refresh_feed(self, dummy, feed): tasks.Task(self.__news.refresh_feed(feed))
	
	def start_refresh(self, dummy): self.__news.start_refresh()
	
	def export_xml(self): return self.__news.export_xml()
	
	def stat(self): return self.__news.stat()
		
	def get_by_ticker(self, ticker): return self.__news.get_by_ticker(ticker)


	### if Options have changed, this methods are called to update the timeouts
	def refresh_update(self, dummy): self.rem_update(); self.add_update()
	def refresh_refresh(self, dummy): self.__news.rem_refresh(); self.__news.add_refresh()


	### if a feed was killed, check if it was the actual one and change the actual one if needed
	def feed_killed(self, dummy, number_of_killed_feed):
		if number_of_killed_feed == self.__fd_count:
			self.__fd_count = None; self.next_feed()
		

	### some signals which arrive from self.__news will be send to a higher level
	def cached_news_read(self, event):
		self.emit("cached_news_read_slave")	# send slave signal to higher level
		self.update_ticker()			# messages are there, show them in box
		self.__news.start_refresh()		# and then try to refresh the news

	def refresh_feed_done(self, dummy, feed):
		if (self.__msg_index == None):
				self.update_ticker()	# if still no msg for ticker, update it
		self.emit("refresh_feed_done_slave", feed)
		
	
	### methods to open the actual page or the actual feed (started as task)
	def open_page(self, dummy = None):	tasks.Task(self.open_page_task())
	def open_page_task(self):		# open message shown in ticker
		msg = self.akt_msg(); yield None
		if msg == None:
			### This shouldnt happen, where from you reached this point?
			### but its here for safety reasons ;)
			print "ERROR: no actual message, how should i open this in browser?"
			self.__box.status("ERROR: no actual message to open", g.STOCK_DIALOG_ERROR); yield None;
			return
		self.__box.status("opening page in browser", g.STOCK_CONVERT); yield None
		msg.read = 1 ### dont forget to mark the message as read
		tool.openPage(msg.link, self.__Options)

	def open_page_feed(self, dummy = None):	tasks.Task(self.open_page_feed_task())
	def open_page_feed_task(self):		# open homepage of the ticker
		feed = self.akt_feed()
		if feed == None:
			### This shouldnt happen, where from you reached this point?
			### but its here for safety reasons ;)
			print "ERROR: no actual feed, how should i open this in browser?"
			self.__box.status("ERROR: no actual feed-page to open", g.STOCK_DIALOG_ERROR); yield None;
			return
		self.__box.status("opening feed-page in browser", g.STOCK_CONVERT); yield None
		tool.openPage(feed.link, self.__Options)

	
	
	"""----------------------------------------------------------------------------------"""
	""" 2. Methods to move forwards or backwards in Ticker and update the Ticker         """
	"""----------------------------------------------------------------------------------"""
	### two methods to add and remove the update-timeouts
	def add_update(self, dummy = None):
		if self.__updatetimeout == None:
			self.__updatetimeout = g.timeout_add(1000*self.__Options.update_time.int_value, self.update_ticker)
			#~ self.__updatetimeout = g.timeout_add(10*self.__Options.update_time.int_value, self.update_ticker)
	def rem_update(self, dummy = None):
		if self.__updatetimeout <> None:
			g.timeout_remove(self.__updatetimeout); self.__updatetimeout = None
	
	### the regularly called update-method: first remove the update to prevent
	### double-updates and after updating (forward), add timeout again
	def update_ticker(self):
		self.rem_update()
		if self.__Options.v: print "update Ticker"
		import gc; gc.collect();
		self.show_next_msg_in_ticker()
		self.add_update()
		return True
	
	### a callback which enables scrolling in messages
	def scroll_msg(self, widget, event):
		import sys; import gc; gc.collect();
		if (self.__Options.debug_mode.int_value):
			import sys; import gc; gc.collect();
			try: print "scroll_msg show_list --> DEBUG  TotalRefCount: " + str(sys.gettotalrefcount());
			except:print "scroll_msg show_list --> DEBUG configure python with-pydebug to find memory leaks";
		if event.direction == 1: self.show_next_msg_in_ticker()
		elif event.direction == 0: self.show_prev_msg_in_ticker()
	
	### a callback which enables scrolling in feeds
	def scroll_feed(self, widget, event):
		print "scroll_feed"
		if event.direction == 1: self.show_first_msg_from_next_feed()
		elif event.direction == 0: self.show_first_msg_from_prev_feed()
		
	### two methods to show next or previous message in Ticker, those are called manually
	### Usually Signals (think for istance of scroll signals) are usually stored till they
	### could done - this might result in storing 100 go forward events and blocking your
	### CPU doing the job. Tasks allow to disable such fast-following signals
	def show_next_msg_in_ticker(self, dummy = None): tasks.Task(self.show_next_msg_in_ticker_task())
	def show_next_msg_in_ticker_task(self):
		if self.__updating: return
		import sys; import gc; gc.collect();
		if (self.__Options.debug_mode.int_value):
			import sys; import gc; gc.collect();
			try: print "next_msg show_list --> DEBUG  TotalRefCount: " + str(sys.gettotalrefcount());
			except:print "next_msg show_list --> DEBUG configure python with-pydebug to find memory leaks";
		self.__updating = True;	yield None; i = self.next_msg();
		yield None; self.show_msg(i); yield None; self.__updating = False

	def show_prev_msg_in_ticker(self, dummy = None): tasks.Task(self.show_prev_msg_in_ticker_task())
	def show_prev_msg_in_ticker_task(self):
		if self.__updating: return
		self.__updating = True; yield None; i = self.prev_msg();
		yield None; self.show_msg(i); yield None; self.__updating = False
	
	### two methods to show next message in next feed or prev message in prev feed
	def show_first_msg_from_next_feed(self, dummy = None):
		if self.next_feed():
			self.__msg_index = -1
			tasks.Task(self.show_next_msg_in_ticker_task())
	def show_first_msg_from_prev_feed(self, dummy = None):
		if self.prev_feed():
			self.__msg_index = -1
			tasks.Task(self.show_next_msg_in_ticker_task())
	
	
	### Method to show the message in the box
	def show_msg(self, i):
		if not(i):
			if len(self.__news.feeds) <> 0:
				time_to_wait = self.__news.time_to_next_refresh()
				if time_to_wait == None: message = ", refreshing"
				elif int(time_to_wait) == 0: message = ", waiting " + str(int(time_to_wait*60)) + " seconds"
				else: message = ", waiting " + str(int(time_to_wait)) + " minutes"
				self.__error += message
				self.__box.image.set(g.STOCK_CANCEL)
				self.__box.label.tooltip.disable()
			else:
				self.__box.image.set(g.STOCK_DIALOG_ERROR)
				self.__box.label.set_tip("I havn't found any News Sources in your Configuration, " +\
						"you have to open the Options Dialog and add at least one source")
			
			self.__box.label.update(self.__error)
			self.__box.image.tooltip.disable()
			return False
		else:
			fd = self.akt_feed()
			name = tool.unxml(i.title).encode("utf-8")
			self.__box.label.update(name)
			
			#self.__box.image.get_from_file(fd.get_iconcache())
			self.__box.image.set(fd.ticker)
			
			self.__box.label.addTip(i)
			self.__box.image.addTip(fd, self.__news)
			return True



	### returns the actual feed shown in ticker or none, if no actual feed available
	### return None might happen if there are no (new) feed in self.__news or if
	### the actually in ticker shown feed was killed recently or set inactive
	def akt_feed(self):
		try:
			aktfeed = self.__news.feeds[self.__fd_count]
			if aktfeed.get_active(): return aktfeed
			#else: print "feed "+ aktfeed.get_ticker() + " not active"
		except: return None
		return None
	
	### returns the actual message. as above, there might be no actual message, if there
	### is no new message or if actual feed was killed recently
	def akt_msg(self):
		try:	return self.akt_feed().msg[self.__msg_index]
		except: return None
		return None
		
	### returns the Status of the actual message. As above, there might be no actual message
	### if there is no new message or if actual feed was killed recently, then lets say this
	### no-message isnt new ;)
	def akt_msg_is_new(self):
		try:	return self.akt_feed().msg_is_new(self.akt_msg())
		except: return False
		return False

	### checks if there are no messages left to show as new in ticker by user criteria
	### this must be checked bevor going in recursion
	### Cause time happens between checking of so called 'new messages' and using them,
	### it might be a different situation later, but i think its ok to do so
	def no_msg(self):
		no_sources = True
		no_active_feeds = True
		no_msg_in_active_feeds = True
		no_msg_to_show_in_active_feeds = True
		for fd in self.__news.feeds:			# check all feeds
			no_sources = False
			if fd.get_active() == 1:
				no_active_feeds = False
				if len(fd.msg) > 0:
					no_msg_in_active_feeds = False
					if fd.get_shownews() > 0:
						no_msg_to_show_in_active_feeds = False
						### There are messages, check if they are too old
						self.__error = "no new messages in active feeds"
						for i in range(0, len(fd.msg)-1):
							if fd.msg_is_new(fd.msg[i]):
								### ok, there is at least one new message
								self.__error = ""
								return False
							if i + 1 == fd.get_shownews(): break
		if no_msg_to_show_in_active_feeds: self.__error = "no new messages, showcount in active might be to low"
		if no_msg_in_active_feeds: self.__error = "no messages in active feeds"
		if no_active_feeds: self.__error = "no active feeds found"
		if no_sources: self.__error = "no sources found (use Options to add)"
		return True

	### returns the next new message to show based on user configuration. If there is no
	### new msg left, it returns None
	def next_msg(self):
		# If there were last time no mesages, try to start from 0
		if self.__msg_index == None or self.__fd_count == None:
			self.__msg_index = 0; self.__fd_count = 0
		while(1):
			akt_feed = self.akt_feed()
			if 	akt_feed and \
				self.__msg_index + 1 < min(len(akt_feed.msg), akt_feed.get_shownews()):
				self.__msg_index += 1
			else:
				if not(self.next_feed()):		# try next feed
					self.__msg_index = None; return None
				else: 	self.__msg_index = 0
			if self.akt_msg_is_new():
				self.akt_msg().showcount += 1; return self.akt_msg()
		
	### search the next 'active' feed an set self.__fd_count to feed_nr
	### Return Feed or None to indicate if it was succesful
	def next_feed(self):
		# If there is no actual feed, try 0
		if self.__fd_count == None: self.__fd_count = 0
		self.__error = ""
		while(1):
			if self.__fd_count < len(self.__news.feeds)-1:		# try next feed
				self.__fd_count += 1
			else:
				if self.no_msg():
					self.__fd_count = None
					return None
				else:	self.__fd_count = 0	# use first feed
			akt_feed = self.akt_feed()
			if akt_feed:
				self.emit("next_feed_in_showlist", akt_feed)
				return akt_feed
		
	### returns the prev new message to show based on user configuration. If there is no
	### new msg left, it returns None
	def prev_msg(self):
		# If there were last time no mesages, try to start from 0
		if self.__msg_index == None or self.__fd_count == None:
			self.__fd_count = len(self.__news.feeds)-1
		while(1):
			akt_feed = self.akt_feed()
			if 	akt_feed and self.__msg_index > 0:
				self.__msg_index -= 1
			else:
				akt_feed = self.prev_feed()
				if not(akt_feed):		# try prev feed
					self.__msg_index = None; return None
				else: 	self.__msg_index = min(len(akt_feed.msg)-1, akt_feed.get_shownews()-1)
			if self.akt_msg_is_new():
				self.akt_msg().showcount += 1; return self.akt_msg()
	
	### search the next 'active' feed an set self.__fd_count to feed_nr
	### Return Feed or None to indicate if it was succesful
	def prev_feed(self):
		self.__error = ""
		while(1):
			if self.__fd_count > 0:		# try prev feed
				self.__fd_count -= 1
			else:
				if self.no_msg():
					self.__fd_count = None
					return None
				else:
					self.__fd_count = len(self.__news.feeds)-1	# use last feed
			akt_feed = self.akt_feed()
			if akt_feed:
				self.emit("prev_feed_in_showlist", akt_feed)
				return akt_feed
		

	"""----------------------------------------------------------------------------------"""
	""" 3. Methods to move forwards or backwards in Overview/ActiveTooltip               """
	"""----------------------------------------------------------------------------------"""
	### The following method checks, if the choosen feed is a valid overviev-feed
	### on User-Options (this might be at the wrong place, should be someday at
	### part of the overview-classes
	### If the overview-feed, which is choosen from user by asking for the next
	### or the previous feed, is an actual feed with 'new' messages, then update
	### the ticker with this feed
	def is_overview_feed(self, feed):
		if feed.get_active() == 1:
			for msg in feed.msg:
				if feed.msg_is_new(msg):   # if there are new messages in this feed
					self.__fd_count = feed.feed_nr	# update the ticker
					self.__msg_index = -1
					self.update_ticker()
					return True
				if self.__Options.tt_a_fd_wo_news.int_value == 1: return True
		if self.__Options.tt_a_inactive_fd.int_value == 1: return True
		return False
	
	### check if there are still feeds which are valid by user criteria for overview
	### its importend to check this bevor recursion
	def no_ov_feed(self):
		for fd in self.__news.feeds:
			if self.is_overview_feed(fd): return False
		return True
	
	### return the next feed by user criteria for overview (and update ticker,
	### see self.is_overview_feed
	def ov_next_feed(self, feed):
		if not(feed): # if feed = None, restart at the first feed
			feed_nr = -1
		else: feed_nr = feed.feed_nr
		while feed_nr < len(self.__news.feeds)-1:
			feed_nr += 1
			if self.is_overview_feed(self.__news.feeds[feed_nr]):
				return self.__news.feeds[feed_nr]
		if self.no_ov_feed(): return None
		else: return self.ov_next_feed(None)
	
	### return the next feed by user criteria for overview (and update ticker,
	### see self.is_overview_feed
	def ov_prev_feed(self, feed):
		if not(feed): # if feed = None, restart at the last feed
			feed_nr = len(self.__news.feeds)
		else: feed_nr = feed.feed_nr
		while feed_nr <> 0:
			feed_nr -= 1
			if self.is_overview_feed(self.__news.feeds[feed_nr]):
				return self.__news.feeds[feed_nr]
		if self.no_msg(): return None
		else: return self.ov_prev_feed(None)



gobject.signal_new("cached_news_read_slave", show_list, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("next_feed_in_showlist", show_list, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("prev_feed_in_showlist", show_list, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("refresh_feed_done_slave", show_list, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
