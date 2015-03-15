#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

from __future__ import generators
import rox
from rox import applet, g, tasks, InfoWin

import sys
import os

import tool
import overview	
import active_tooltip
import options
import ticker_menu
import show_list
import help

from output import Label_box

global minsize ### a Identifier for miniatur icons (see tool.EventBuffer for use)
minsize = g.icon_size_register("minimal-size-12-12", 12, 12)



"""--------------------------------------------------------------------------------------------"""
"""--------------------------- Main Program Container -----------------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### This is the Main-Container. It holds all the shown and unshown Objects of the Ticker
### and connects siganls between them for cross-actions. Only signals from Options are also
### connected directly to other instances, except this there should be no cross instance
### signalling on lower levels
class MainContainer:
	def __init__(self, V, Version, user_conf, verbose):
		
		### here are the Options (including info about the sources) stored
		self.__Options = options.Options(V, Version, user_conf, verbose)
		import sys;
		if (self.__Options.debug_mode.int_value):
			import gc; gc.collect();
			try: print "###DEBUG TotalRefCount: " + str(sys.gettotalrefcount());
			except: print "###DEBUG configure python with-pydebug to find memory leaks";
		if (self.__Options.debug_mode.int_value): print "Options created: --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		### The box holds the Ticker-Label and the Ticker-Icon
		self.__box = Label_box(self.__Options); self.add(self.__box)
		if (self.__Options.debug_mode.int_value): print "Box created: --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		### show_list is a class wich presents a view of the news
		self.__show_list = show_list.show_list(self.__Options, self.__box)
		if (self.__Options.debug_mode.int_value): print "Show_list created: --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		### this is the active-ticker-window
		self.__act_tick = active_tooltip.ActiveTooltip(self.__Options, self.__show_list)		
		if (self.__Options.debug_mode.int_value): print "act_tick created: --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		### this is the overview-window an contain
		self.__overview = overview.overview(self.__Options, self.__show_list)
		if (self.__Options.debug_mode.int_value): print "overview created: --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		### and the hole thing needs a menu
		self.__menu = ticker_menu.menu(self.__Options, self)
		if (self.__Options.debug_mode.int_value): print "menu created: --> refrences to Options: " + str(sys.getrefcount(self.__Options))
		
		### set cross-object reaction to signals
		self.__Options.connect("refresh_scrollbars", self.__act_tick.set_scrollbars)
		self.__Options.connect("refresh_update_time", self.__show_list.refresh_update)
		self.__Options.connect("refresh_refresh_time", self.__show_list.refresh_refresh)
		self.__Options.connect("refresh_win_size", self.set_size)
		self.__Options.connect("refresh_label_color", self.__box.label.set_color)
		self.__Options.connect("refresh_windowdecorations", self.set_windowdecorations)
		self.__Options.connect("refresh_transparency", self.refresh_transparency)
		self.__Options.connect("refresh_background", self.update_back_color)

		self.__box.image.connect("img_entered", self.show_overview_as_tip)
		self.__box.image.connect("img_leaved", self.__act_tick.leave_widget)
		self.__box.image.connect("img_click_button_1", self.__show_list.open_page_feed)
		#~ self.__box.image.connect("img_click_button_2", self.__show_list.show_next_msg_in_ticker)
		self.__box.image.connect("scroll_event", self.__show_list.scroll_feed)
		self.__box.image.connect("img_click_button_3", self.open_menu)
		self.__box.image.connect("img_click_button_3", self.__act_tick.show_now_as_menu)
		
		self.__box.label.connect("lab_click_button_1", self.__show_list.open_page)
		#~ self.__box.label.connect("lab_click_button_2", self.__show_list.show_next_msg_in_ticker)
		self.__box.label.connect("lab_click_button_3", self.__show_list.show_next_msg_in_ticker)
		self.__box.label.connect("lab_tickbild_entered", self.__show_list.rem_update)
		self.__box.label.connect("lab_tickbild_leaved", self.__show_list.add_update)
		self.__box.label.connect("scroll_event", self.__show_list.scroll_msg)

		self.__show_list.connect("cached_news_read_slave", self.__act_tick.create_window)
		self.__show_list.connect("next_feed_in_showlist", self.__act_tick.akt_feed)
		self.__show_list.connect("refresh_feed_done_slave", self.__act_tick.refresh_if_actual)
		self.__show_list.connect("refresh_feed_done_slave", self.__overview.reinit)

		self.__act_tick.connect("size_changed_tt_a", self.__Options.act_tick_size_changed)
		self.__act_tick.nav.connect("refresh_all", self.__show_list.start_refresh)
		self.__act_tick.nav.connect("open_options", self.__Options.show_options)
		self.__act_tick.nav.connect("open_overview_window", self.__overview.recreate_window)
		self.__act_tick.nav.connect("help", self.open_help)
		self.__act_tick.nav.connect("info", self.info)
		self.__act_tick.nav.connect("quit", self.exit_prog)
		self.__act_tick.stat.connect("switch_active", self.__Options.sources_switch_feed_active)
		self.__act_tick.stat.connect("refresh_feed", self.__show_list.refresh_feed)

		self.__overview.connect("switch_active_slave", self.__Options.sources_switch_feed_active)
		self.__overview.connect("refresh_feed_slave", self.__show_list.refresh_feed)
		self.__overview.connect("size_changed_ov", self.__Options.overview_size_changed)

		self.__menu.connect("m_quit", self.exit_prog)
		self.__menu.connect("m_help", self.open_help)
		self.__menu.connect("m_info", self.info)
		self.__menu.connect("m_show_window", self.__overview.recreate_window)
		self.__menu.connect("m_show_options", self.__Options.show_options)
		self.__menu.connect("m_refresh_ticker", self.__show_list.start_refresh)
		self.__menu.connect("m_prev_feed", self.__show_list.show_first_msg_from_prev_feed)
		self.__menu.connect("m_next_feed", self.__show_list.show_first_msg_from_next_feed)
		self.__menu.connect("m_prev_msg", self.__show_list.show_prev_msg_in_ticker)
		self.__menu.connect("m_next_msg", self.__show_list.show_next_msg_in_ticker)

		### some formatting an done !
		if self.applet:
			self.set_size_request(self.__Options.hor_size.int_value, self.__Options.ver_size.int_value)
		else: self.set_size_request(10,10)
		self.set_size()
		
		### some pixbufs for transparency -- and initialisation
		self.__pixbuf_back = None; self.__pixbuf = None
		self.__pixbuf_label = None; self.__pixbuf_image = None
		self.activate_transparency()
		self.set_windowdecorations()
		self.connect('configure-event',self.win_configure)
		self.connect("destroy", self.__del__)
		
		self.set_app_paintable(True)
		self.__box.label.set_app_paintable(True)
		self.__box.image.set_app_paintable(True)
		#if self.applet: self.connect('expose-event', self.expose)

		self.show()
	

	### Some themes draw images and stuff here, so we have to
	### override it manually.
	def expose(self, widget, event):
		self.window.draw_rectangle(self.style.bg_gc[g.STATE_NORMAL], True,
			0, 0,self.allocation.width,self.allocation.height)

	### central method to show the info-window
	def info(self, dummy = None): InfoWin.infowin(" " + self.__Options.Version + " ")
	
	### central method to show the help-window (uses the HelpContainer in Options-Dialog)
	def open_help(self, dummy = None):
		Help = g.Window()
		Help.set_title(" " + self.__Options.Version + " ")
		HelpTab = help.Help_Book(self.__Options)
		Help.add(HelpTab)
		Help.show()

	### shows usual menu, if not ActiveTooltip Choosen as a menu
	def open_menu(self, dummy, event):
		if self.__Options.tt_a.int_value == 0 \
			or self.__Options.tt_a_as_menu.int_value == 0:
			self.__menu.popup(self.__menu, event, self.position_menu)

	### get Position and size of the window an ask for showing the Tip (this willbe denied if
	### there is choosen to show it as a menu
	def show_overview_as_tip(self, dummy):
		x, y = self.window.get_position()
		w, h = self.size_request()
		self.__act_tick.show_now_as_tip(x, y, w, h)

	### set the size of the Window: If its an applet, uses requests, for a window use resize
	def set_size(self, dummy = None):
		if self.applet or self.__Options.hor_size.int_value <= 0 or self.__Options.ver_size.int_value <= 0:
			self.set_size_request(self.__Options.hor_size.int_value, self.__Options.ver_size.int_value)
		else:
			self.set_size_request(10,10)
			self.resize(self.__Options.hor_size.int_value, self.__Options.ver_size.int_value)
	
	### decide if border has to show or not
	def set_windowdecorations(self, dummy = None):
		self.set_decorated(not(self.__Options.borderless.int_value))

	### set or unset transparency of the windows
	def refresh_transparency(self, dummy):
		self.activate_transparency()
		### if transparency had changed, shake the window a little bit ;)
		### mightbe its better to tell this the win-manager directly, but its working this way
		x, y = self.window.get_position(); self.move(x+1, y); self.move(x-1, y)

	### set or unset transparency of the windows (like above und usually called,
	### 	except while initialising the window)
	def activate_transparency(self):
		if (self.__Options.transparent.int_value) == 0 or not(os.path.isfile(self.__Options.back_datei.value)):
			self.update_back_color(None)
		else:
			### read background-image from File (set in Options)
			self.__pixbuf_back = g.gdk.pixbuf_new_from_file(self.__Options.back_datei.value)

	### set's the background colors (for all states) to spezified values
	def update_back_color(self, dummy):
		self.modify_bg(g.STATE_NORMAL,self.get_colormap().alloc_color(self.__Options.back_color.value))
		self.__box.label.modify_bg(g.STATE_NORMAL,\
			self.__box.label.get_colormap().alloc_color(self.__Options.back_color.value))
		self.__box.label.modify_bg(g.STATE_PRELIGHT,\
			self.__box.label.get_colormap().alloc_color(tool.back_color_prelight(self.__Options)))
		self.__box.image.modify_bg(g.STATE_NORMAL,\
			self.__box.image.get_colormap().alloc_color(self.__Options.back_color.value))
		self.__box.image.modify_bg(g.STATE_PRELIGHT,\
			self.__box.image.get_colormap().alloc_color(tool.back_color_prelight(self.__Options)))

	### Callback Mathod after Configure-Event of the window or applet (save size, refresh background)
	def win_configure(self, dummy, event):
		if self.applet: w, h = self.size_request()
		else: w, h = self.get_size()
		if w <> self.__Options.hor_size.int_value or h <> self.__Options.ver_size.int_value:
			self.__Options.mainwin_size_changed(w, h)
		if (self.__Options.transparent.int_value): self.refresh_background(w, h)

	### The way make the background look transparent
	def refresh_background(self, w, h):
		if not(self.__pixbuf_back): return
		w_b = self.__pixbuf_back.get_width()
		h_b = self.__pixbuf_back.get_height()
		x, y = self.window.get_position()
		w, h = self.get_size()
		if x < 0 or y < 0: return
		if x + w > w_b or y + h > h_b: return
		x_l, y_l = self.__box.label.window.get_position()
		w_l, h_l = self.__box.label.window.get_size()
		x_i, y_i = self.__box.image.window.get_position()
		w_i, h_i = self.__box.image.window.get_size()
		if self.__pixbuf: del self.__pixbuf
		self.__pixbuf = g.gdk.Pixbuf(g.gdk.COLORSPACE_RGB, False, 8, w, h)
		if self.__pixbuf_label: del self.__pixbuf_label
		self.__pixbuf_label = g.gdk.Pixbuf(g.gdk.COLORSPACE_RGB, False, 8, w_b - x - x_l, h_l)
		if self.__pixbuf_image: del self.__pixbuf_image
		self.__pixbuf_image = g.gdk.Pixbuf(g.gdk.COLORSPACE_RGB, False, 8, w_i, h_i)
		self.__pixbuf_back.copy_area(x, y, w, h, self.__pixbuf, 0, 0)
		self.__pixbuf_back.copy_area(x+x_l, y+y_l, w_b - x - x_l, h_l, self.__pixbuf_label, 0, 0)
		self.__pixbuf_back.copy_area(x+x_i, y+y_i, w_i, h_i, self.__pixbuf_image, 0, 0)
		self.__pixmap, mask = self.__pixbuf.render_pixmap_and_mask()
		self.__pixmap_label, mask = self.__pixbuf_label.render_pixmap_and_mask()
		self.__pixmap_image, mask = self.__pixbuf_image.render_pixmap_and_mask()
		self.window.set_back_pixmap(self.__pixmap, False)
		self.__box.label.window.set_back_pixmap(self.__pixmap_label, False)
		self.__box.image.window.set_back_pixmap(self.__pixmap_image, False)
		self.resize(w,h)
		self.__box.label.hide()
		self.__box.label.show()
		self.__box.image.hide()
		self.__box.image.show()
	
	### exit the while Programm (calls __del__ in callback)
	def exit_prog(self, dummy): 
		tool.kill_child_task()
		self.destroy()

	### if exciting the Program, save the Options, and close all windows
	def __del__(self, dummy):
		self.__show_list.export_xml()	## save actual feeds
		rox.app_options.save()		## save Options (mightbe changed since last Access to Optionsbox)
		if self.__Options.OptionsBox: self.__Options.OptionsBox.destroy()
		self.destroy();
		g.main_quit()
		sys.exit()




### Program-Window
class TickerWindow(rox.Window, MainContainer):
        def __init__(self, V, Version, user_conf, verbose):
		rox.Window.__init__(self)
		self.applet = False
		self.__Options = None
		MainContainer.__init__(self, V, Version, user_conf, verbose)
		self.position_menu = None
		self.set_title(" " + Version + " ")




### Program-Applet
class TickerApplet(applet.Applet, MainContainer):
        def __init__(self, V, Version, user_conf, verbose):
                applet.Applet.__init__(self,sys.argv[1])
		self.applet = True
		MainContainer.__init__(self, V, Version, user_conf, verbose)
		self.__Options = None

"""--------------------------------------------------------------------------------------------"""


