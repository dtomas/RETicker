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

import gobject

import statuslines
import contents
import tool

"""--------------------------------------------------------------------------------------------"""
"""------ a class for the overview window -----------------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""				
### The overview window shows all messages from all feeds, its konda combination of many
### active tooltips and uses the same child-calsses
class overview(gobject.GObject):
	def __init__(self, Options, show_list):
		self.__Options = Options
		self.__show_list = show_list
		######################
		gobject.GObject.__init__(self)
		self.win = None		# to remember if there is still a window
		self.feed_wins = {}	# list of (stat, overview) for all feeds
		self.Cons = tool.Connections()

	### cleanup the place if window gets destroyed
	def destroy(self, dummy = None):
		self.win = None
		
		# This is needed to really remove all references to overview and stats,
		# i do not really know why ;)
		self.feed_wins = {}
		
		self.disconnect_all()
	
	### remove all connections if destroyed
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()

	### set size form Option Values
	def refresh_size(self, dummy=None):
		#self.set_size_request(self.__Options.ov_hor_size.int_value,self.__Options.ov_ver_size.int_value)
		self.win.resize(self.__Options.ov_hor_size.int_value,self.__Options.ov_ver_size.int_value)
		
	### if we recognize a new size, we should tell it to update the Options
	def change_size(self, dummy, event):
		width, height = self.win.get_size()
		if width <> self.__Options.ov_hor_size.int_value or height <> self.__Options.ov_ver_size.int_value:
			self.emit("size_changed_ov", width, height)

	### set colors from Option Values
	def refresh_colors(self, dummy=None):
		self.viewport.modify_bg(g.STATE_NORMAL,self.viewport.get_colormap().alloc_color(self.__Options.ov_bg_stat.value))
		self.win.modify_bg(g.STATE_NORMAL,self.win.get_colormap().alloc_color(self.__Options.ov_bg.value))		
	
	###  if the content of one feed might have changed, reinit the stat and overview
	def reinit(self, dummy, feed):
		if not(self.win): return
		ticker = feed.get_ticker()
		sep, stat, overview = self.feed_wins[ticker]
		stat.reinit(feed)
		overview.reinit(feed)

	### source killed, remove it from list
	def feed_killed(self, source, dummy):
		self.Cons.disconnect(source, "source_killed")
		ticker = source.get_ticker()
		self.feed_wins[ticker][0].destroy()	# destroy separator
		self.feed_wins[ticker][1].destroy()	# destroy stat line
		self.feed_wins[ticker][2].destroy()	# destroy overview
		self.feed_wins.pop(ticker)
	
	# add a source to the window
	def add_source(self, sources, source):
		self.Cons.connect(source, "source_killed", self.feed_killed)
		feed = self.__show_list.get_by_ticker(source.get_ticker())
		
		sep = g.HSeparator()
		
		stat = statuslines.StatusLine(self.__Options, True)
		stat.reinit(feed)
		stat.connect("switch_active", self.switch_feed_active)
		stat.connect("refresh_feed", self.refresh_feed)
		
		overview = contents.ov_feed(self.__Options, self.__tooltips, True)
		overview.reinit(feed)
		
		self.vbox_in.pack_start(sep, g.FALSE, g.FALSE, 0)
		self.vbox_in.pack_start(stat, g.FALSE, g.FALSE, 0)
		self.vbox_in.pack_start(overview, g.FALSE, g.FALSE, 0)
		
		# check if called by signal "source_added"
		if sources:
			sep.show()
			stat.show()
			overview.show()
			
		self.feed_wins[source.get_ticker()] = (sep, stat, overview)
	
	### the window is created and shown - if its still there, it will be presented to you
	def recreate_window(self, dummy = None):
		#import sys; import gc; gc.collect();
		#print "recreate window overview --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		# check if window is still shown, then re-present
		if self.win: self.win.present(); return
		self.win = g.Window()
		self.win.connect("destroy", self.destroy)
		self.win.set_title(" " + self.__Options.Version + " ")
		
		self.__tooltips = g.Tooltips()
		self.__tooltips.enable()
		
		self.vbox = g.VBox()
		self.swin=g.ScrolledWindow()
		self.swin.set_shadow_type(g.SHADOW_NONE)
		self.swin.set_policy(g.POLICY_AUTOMATIC, g.POLICY_AUTOMATIC)
		self.win.add(self.vbox)
		self.vbox_in = g.VBox()
		self.viewport = g.Viewport()
		self.viewport.add(self.vbox_in)
		self.viewport.set_shadow_type(g.SHADOW_NONE)
		self.swin.add(self.viewport)
		self.vbox.add(self.swin)
		
		self.win.set_size_request(50,40)
		self.refresh_size()
		self.refresh_colors()
		
		self.Cons.connect(self.__Options, "refresh_ov_colors", self.refresh_colors)
		self.Cons.connect(self.__Options, "refresh_ov_size", self.refresh_size)
		self.Cons.connect(self.__Options.sources, "source_added", self.add_source)
		
		
		self.win.set_events(g.gdk.CONFIGURE)
		self.win.connect('configure-event',self.change_size)
		self.feed_wins = {}
		for feed in self.__show_list.feeds:
			source = self.__Options.sources.get_by_ticker(feed.get_ticker())
			self.add_source(None, source)
		self.win.show_all()

	### callbacks for elems of the statuslines
	def switch_feed_active(self, dummy, feed): self.emit("switch_active_slave", feed)
	def refresh_feed(self, dummy, feed): self.emit("refresh_feed_slave", feed)


gobject.signal_new("switch_active_slave", overview, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("refresh_feed_slave", overview, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("size_changed_ov", overview, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,))

