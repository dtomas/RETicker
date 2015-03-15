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
import os

import statuslines
import contents
import tool

# I dont know why but the prog eats memory if I do the calculation directly in set_events()
configure_enter_leave_notify_mask = (g.gdk.CONFIGURE | g.gdk.ENTER_NOTIFY_MASK | g.gdk.LEAVE_NOTIFY_MASK)

"""--------------------------------------------------------------------------------------------"""
"""------ a class for the active tooltip (or menu) --------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""				
### The active tooltip is a window without a frame, wich keeps there as long you are with the mouse
### over it, if you leave it, it will be hide again. (it has status hidden after __init__)
class ActiveTooltip(g.Window):
	def __init__(self, Options, show_list):
		self.__Options = Options
		self.__show_list = show_list
		######################
		### create the window layout
		g.Window.__init__(self)
		
		self.__tooltips = g.Tooltips()
		self.__tooltips.enable()
		
		self.new_frame=g.Frame()
		self.ebox = g.EventBox() # without thisone the enter and leave-widget events dont work
		vbox = g.VBox()
		self.swin=g.ScrolledWindow()
		self.swin.set_shadow_type(g.SHADOW_NONE)
				
		self.viewport = g.Viewport()
		self.viewport.set_shadow_type(g.SHADOW_NONE)
		self.viewport.set_border_width(2)
		self.swin.add(self.viewport)

		### create a one-feed overview
		self.__overview = contents.ov_feed(self.__Options, self.__tooltips)
		self.viewport.add(self.__overview)
		### create a statusline
		self.stat = statuslines.StatusLine(self.__Options)
		### create a NavigationLine
		self.nav = statuslines.NavLine(self.__Options)
		vbox.pack_start(self.stat, g.FALSE, g.FALSE, 0)
		vbox.pack_end(self.nav, g.FALSE, g.FALSE, 0)
		
		vbox.add(self.swin)
		self.new_frame.add(vbox)
		self.ebox.add(self.new_frame)
		self.add(self.ebox)
		
		### set Layout
		self.set_decorated(g.FALSE)
		self.set_size_request(50,40)
		self.refresh_size()
		self.refresh_colors()
		self.set_scrollbars()
		
		### connect all things to react on
		self.set_events(configure_enter_leave_notify_mask)
		self.connect("enter-notify-event", self.enter_widget)
		self.connect("leave-notify-event", self.leave_widget)
		self.connect('configure-event',self.change_size)
		self.connect("destroy", self.disconnect_all)

		self.nav.connect("next_feed", self.next_feed)
		self.nav.connect("prev_feed", self.prev_feed)
		self.nav.connect("open_feed_page", self.open_feed)

		self.Cons = tool.Connections()
		self.Cons.connect(self.__Options, "refresh_ov_colors", self.refresh_colors)
		self.Cons.connect(self.__Options, "refresh_tt_a_size", self.refresh_size)

                self.set_property("skip-taskbar-hint", True)
                self.set_property("skip-pager-hint", True)

		### some local variables
		self.__initialized = False     	### window is created (after getting some news)
		self.__active = False		### Mouse is or was over window
		self.__tip = False		### shown as tip
		self.__menu = False		### shown as menu
		self.__feed = None
		self.__source = None
		
	### to remove all left connections while destroying the instance
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()
	
	### set size or colors or scrollbar-layout from appropriate Option Values
	def refresh_size(self, dummy=None):
		self.resize(self.__Options.tt_a_hor_size.int_value, self.__Options.tt_a_ver_size.int_value)
	def refresh_colors(self, dummy=None):
		self.new_frame.modify_bg(g.STATE_NORMAL,self.new_frame.get_colormap().alloc_color('black'))
		self.ebox.modify_bg(g.STATE_NORMAL,self.ebox.get_colormap().alloc_color(self.__Options.tt_a_bg_stat.value))
	def set_scrollbars(self, dummy=None):
		if self.__Options.tt_a_hor_scrollbar.int_value == 1: hor_bar = g.POLICY_AUTOMATIC
		else: hor_bar = g.POLICY_NEVER
		if self.__Options.tt_a_ver_scrollbar.int_value == 1: ver_bar = g.POLICY_AUTOMATIC
		else: ver_bar = g.POLICY_NEVER
		self.swin.set_policy(hor_bar, ver_bar)

	### if size has changed, send an event to change size in Options
	def change_size(self, dummy, event):
		width, height = self.get_size()
		if width <> self.__Options.tt_a_hor_size.int_value or height <> self.__Options.tt_a_ver_size.int_value:
			self.emit("size_changed_tt_a", width, height)
	
	### create window for the first time after news found in cache, set initialized true
	def create_window(self, widget = None, dummy = None):
		#import sys; import gc; gc.collect();
		#print "create_window ov_akfeed --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		#self.Cons.disconnect(self.__source, "source_killed")
		### get actual feed
		self.__feed = self.__show_list.akt_feed()
		### if there is no actual one, try if there are lighter options for active-tooltip
		if self.__feed == None: self.__feed = self.__show_list.ov_next_feed(None)
		### if still no feed, try it again later
		if self.__feed == None: return ### init later
		self.refresh()
		self.__initialized = True
		#print "create_window ov_akfeed  done --> refrences to Options: " + str(sys.getrefcount(self.__Options))
	
	### init window contents but don't show it now
	def refresh(self):
		#import sys; import gc; gc.collect();
		#print "refresh ov_akfeed --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		self.Cons.disconnect(self.__source, "source_killed")
		if self.__feed:
			self.__source = self.__Options.sources.get_by_ticker(self.__feed.get_ticker())
			if not(self.__source): return # maybe source was killed recently
			self.Cons.connect(self.__source, "source_killed", self.create_window)
			self.__overview.reinit(self.__feed)
			self.stat.reinit(self.__feed)
			self.nav.reinit(self.__feed, self.__show_list.stat())
		
	### some callbacks from the navigation bar
	def open_feed(self, widget):
		if self.__feed:
			tool.openPage(self.__feed.link, self.__Options)
	def next_feed(self, widget):
		self.__active = True  # to keep tooltip
		self.__feed = self.__show_list.ov_next_feed(self.__feed); self.refresh()
	def prev_feed(self, widget):
		self.__active = True  # to keep tooltip
		self.__feed = self.__show_list.ov_prev_feed(self.__feed); self.refresh()
	
	
	### if actual shown feed was refreshed, we have to refresh the view too
	def refresh_if_actual(self, dummy, feed):
		if not(self.__feed): return
		if self.__feed.ticker <> feed.ticker: return 
		self.refresh()
	
	### callbacks for entering and leaving the tip-window
	### if left longer than a special time, it gets hidden again
	def enter_widget(self, widget, event):
		self.__active = True
	def leave_widget(self, widget = None, event = None):
		self.__active = False
		tasks.Task(self.wait_and_hide())
	
	### if after a amount of time (0.3sek) the mouse is not again over the tip, the
	### window gets hidden
	def wait_and_hide(self):
		yield tasks.TimeoutBlocker(0.3);
		if not(self.__active) and self.__initialized:
			#print "hide window"
			self.hide()
			self.__tip = False
			self.__menu = False
			self.__feed = self.__show_list.akt_feed()
			self.refresh()

	### after next feed was shown in ticker, this method is called to keep tip up to date
	def akt_feed(self, showlist, feed):
		### if actually the mouse is over the tip, dont change it
		if not(feed) or self.__active: return
		if feed.title == None: return
		self.__feed = feed
		self.refresh()

	### show window, if Options allow to show it as a tip, find right position for the tip
	def show_now_as_tip(self, x, y, w, h):
		if self.__Options.tt_a.int_value == 1 \
			and self.__Options.tt_a_as_menu.int_value == 0 and not(self.__menu): 
			scr_w = g.gdk.screen_width()
			scr_h = g.gdk.screen_height()
			width, height = self.get_size()
			# try over main window
			if y - height >= 0: y = y - height  	### try over window
			elif y + 2*h + height <= scr_h: y = y + 2*h		### try under window
			else: y = int((scr_h - height)/2)       ### try in the middle
			if x < 0 : x = 0
			if x + width > scr_w: x = scr_w - width
			if self.show_now(x, y): self.__tip = True
	
	### show window, if Options allow to show it as a menu, find right position for the menu
	def show_now_as_menu(self, widget, event):
		if self.__Options.tt_a.int_value == 1 \
			and self.__Options.tt_a_as_menu.int_value == 1 and not(self.__tip):
			x, y, mods = g.gdk.get_default_root_window().get_pointer()
			scr_w = g.gdk.screen_width()
			scr_h = g.gdk.screen_height()
			width, height = self.get_size()
			# try over main window
			if y + 8 - height >= 0:	y = y + 8 - height
			elif y - 8 + height <= scr_h: y = y - 8
			else: y = int((scr_h - height)/2)       ### try in the middle
			x -= 8
			if x < 0 : x = 0
			if x + width > scr_w: x = scr_w - width
			if self.show_now(x, y): self.__menu = True
	
	### show window by position if it was initialized before. else initialize now.
	def show_now(self, x, y):
		if not(self.__initialized): self.create_window()
		if self.__initialized:
			self.move(x, y)
			self.show_all()
			return True
		else: return False

gobject.signal_new("size_changed_tt_a", ActiveTooltip, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT,))
