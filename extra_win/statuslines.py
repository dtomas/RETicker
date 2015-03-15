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

import tool
import event_image

"""--------------------------------------------------------------------------------------------"""
"""------ a class which gives you to buttons to activeate or refresh --------------------------"""
"""--------------------------------------------------------------------------------------------"""				
class StatusLine(g.HBox):
	def __init__(self, Options, overview = None):
		self.__overview = overview
		self.__Options = Options
		g.HBox.__init__(self)
		self.__feed = None
		
		# creating the two buttons in minsize, emitting signals to use anywhere else
		from RETicker import minsize
		self.__i_act = event_image.EventImage(self.__Options, g.STOCK_NO, lambda x,y: self.emit("switch_active", self.__feed), minsize, "inactive (click to change)")
		self.pack_start(self.__i_act, g.FALSE, g.FALSE, 1)

		self.__i_ref = event_image.EventImage(self.__Options, g.STOCK_REFRESH, lambda x,y: self.emit("refresh_feed", self.__feed), minsize, "refresh this source")
		self.pack_start(self.__i_ref, g.FALSE, g.FALSE, 1)
		
		# creating a label
		self.__label=g.Label()
		self.__label.set_size_request(-1,-1)
		self.__label.set_alignment(0,0)
		self.__label.set_padding(3,0)
		self.__label.show()
		self.add(self.__label)
		self.sig_switch_active = None
		self.refresh_colors()
		self.show
		
		self.Cons = tool.Connections()
		self.connect("destroy", self.disconnect_all)
		self.Cons.connect(self.__Options, "refresh_ov_colors", self.refresh_colors)
	
	### if destroyed, remove all connections
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()
	
	### set color values from appropriate Options
	def refresh_colors(self, dummy = None):
		if self.__overview: bg_color = self.__Options.ov_bg_stat.value; fg_color = self.__Options.ov_color_old_msg.value
		else: bg_color = self.__Options.tt_a_bg_stat.value; fg_color = self.__Options.tt_a_color_old_msg.value
		self.__i_act.modify_bg(g.STATE_NORMAL,self.__i_act.get_colormap().alloc_color(bg_color))
		self.__i_ref.modify_bg(g.STATE_NORMAL,self.__i_ref.get_colormap().alloc_color(bg_color))
		self.__label.modify_fg(g.STATE_NORMAL,self.__label.get_colormap().alloc_color(fg_color))
	
	### init the statusline, set connections and set the label-text
	def reinit(self, feed):
		# first remove old connections
		if self.__feed:
			self.Cons.disconnect(self.__Options.sources.get_by_ticker(self.__feed.ticker), "change_active")
	
		self.__feed = feed
		if self.__feed:
			self.Cons.connect(self.__Options.sources.get_by_ticker(self.__feed.ticker), "change_active", self.reset_active)
			self.reset_active()
			text = self.__feed.title
			if not(text) or text == "": text = self.__feed.ticker
		else: text = "no messages to show"
		self.__label.set_text(text)
	
	### update the active switch with actual state (image and tooltip)
	def reset_active(self, dummy = None):
		if self.__feed:
			if self.__feed.get_active() == 1:
				self.__i_act.set(g.STOCK_YES); self.__i_act.set_tip("active (click to change)")
			else:
				self.__i_act.set(g.STOCK_NO); self.__i_act.set_tip("inactive (click to change)")
		else: self.__i_act = event_image.EventImage(self.__Options, g.STOCK_MISSING_IMAGE)

gobject.signal_new("switch_active", StatusLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("refresh_feed", StatusLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
	
		

"""--------------------------------------------------------------------------------------------"""
"""------ a class which gives you to buttons to navigate (used by active tooltip) -------------"""
"""--------------------------------------------------------------------------------------------"""				
class NavLine(g.HBox):
	def __init__(self, Options, overview = None):
		self.__Options = Options
		self.__overview = overview
		g.HBox.__init__(self)
		
		self.i_prev = event_image.EventImage(self.__Options, g.STOCK_GO_BACK, lambda x,y: self.emit("prev_feed"), g.ICON_SIZE_SMALL_TOOLBAR, "previous feed")
		self.i_next = event_image.EventImage(self.__Options, g.STOCK_GO_FORWARD, lambda x,y: self.emit("next_feed"), g.ICON_SIZE_SMALL_TOOLBAR, "next feed")
		self.__i_icon = event_image.EventImage(self.__Options, g.STOCK_MISSING_IMAGE, lambda x,y: self.emit("open_feed_page"))
		self.i_refresh = event_image.EventImage(self.__Options, g.STOCK_REFRESH, lambda x,y: self.emit("refresh_all"), g.ICON_SIZE_SMALL_TOOLBAR, "refresh news")
		
		self.i_options = event_image.EventImage(self.__Options, g.STOCK_PREFERENCES, lambda x,y: self.emit("open_options"), g.ICON_SIZE_SMALL_TOOLBAR, "Preferences")
		self.i_window = event_image.EventImage(self.__Options, g.STOCK_INDEX, lambda x,y: self.emit("open_overview_window"), g.ICON_SIZE_SMALL_TOOLBAR, "Overview")
		self.i_help = event_image.EventImage(self.__Options, g.STOCK_HELP, lambda x,y: self.emit("help"), g.ICON_SIZE_SMALL_TOOLBAR, "Help")
		self.__i_info = event_image.EventImage(self.__Options, g.STOCK_DIALOG_INFO, lambda x,y: self.emit("info"))
		self.i_quit = event_image.EventImage(self.__Options, g.STOCK_QUIT, lambda x,y: self.emit("quit"), g.ICON_SIZE_SMALL_TOOLBAR, "Exit NewsTicker")
		
		self.pack_start(self.i_prev, g.FALSE, g.FALSE, 0)
		self.pack_start(self.__i_icon, g.FALSE, g.FALSE, 0)
		self.pack_start(self.i_next, g.FALSE, g.FALSE, 0)
		self.pack_start(self.i_refresh, g.FALSE, g.FALSE, 10)
		
		self.pack_end(self.i_quit, g.FALSE, g.FALSE, )
		self.pack_end(self.i_help, g.FALSE, g.FALSE, 0)
		self.pack_end(self.__i_info, g.FALSE, g.FALSE, 0)
		self.pack_end(self.i_options, g.FALSE, g.FALSE, 5)
		self.pack_end(self.i_window, g.FALSE, g.FALSE, 5)
		
		self.refresh_colors()
		self.show()
		
		self.Cons = tool.Connections()
		self.connect("destroy", self.disconnect_all)
		self.Cons.connect(self.__Options, "refresh_ov_colors", self.refresh_colors)
	
	### remove all connections if destroyed
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()
	
	### set background of all navigatiuon-icons to choosen value
	def refresh_colors(self, dummy = None):
		if self.__overview: bg_color = self.__Options.ov_bg_stat.value
		else: bg_color = self.__Options.tt_a_bg_stat.value
		self.i_prev.modify_bg(g.STATE_NORMAL,self.i_prev.get_colormap().alloc_color(bg_color))
		self.__i_icon.modify_bg(g.STATE_NORMAL,self.__i_icon.get_colormap().alloc_color(bg_color))
		self.i_next.modify_bg(g.STATE_NORMAL,self.i_next.get_colormap().alloc_color(bg_color))
		self.i_refresh.modify_bg(g.STATE_NORMAL,self.i_refresh.get_colormap().alloc_color(bg_color))
		self.i_options.modify_bg(g.STATE_NORMAL,self.i_options.get_colormap().alloc_color(bg_color))
		self.i_help.modify_bg(g.STATE_NORMAL,self.i_help.get_colormap().alloc_color(bg_color))
		self.__i_info.modify_bg(g.STATE_NORMAL,self.__i_info.get_colormap().alloc_color(bg_color))
		self.i_quit.modify_bg(g.STATE_NORMAL,self.i_quit.get_colormap().alloc_color(bg_color))
		self.modify_bg(g.STATE_NORMAL,self.get_colormap().alloc_color(bg_color))
	
	### update the navigationline for the next feed
	def reinit(self, feed, stat):
		# update statistical information
		self.__i_info.set_tip(stat)
		
		# update feed-icon and tip
		if feed:
			self.__i_icon.set(feed.get_ticker())
			if feed.title: title = tool.unxml(feed.title).encode("utf-8")
			else: title = ""
			if feed.desc: desc = tool.unxml(feed.desc).encode("utf-8")
			else: desc = ""
			if title <> "": tip = title
			else: tip = ""
			if desc <> "":
				if tip <> "": tip += "\n"
				tip += desc
			if tip == "": tip = "No Information about feed available,\nyou have to refresh this feed."
			self.__i_icon.set_tip(tip)
		else:
			self.__i_icon.set(g.STOCK_MISSING_IMAGE)
		
gobject.signal_new("next_feed", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("prev_feed", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("open_feed_page", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_all", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("open_options", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("open_overview_window", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("help", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("info", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("quit", NavLine, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())

