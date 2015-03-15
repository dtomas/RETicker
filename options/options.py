#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information
from __future__ import generators

import rox
from rox import g, tasks, ButtonMixed, options
from rox.options import Option

import sys
from xml.dom import minidom
import xml.sax
import urllib
import gc
import os
import re
import gobject

import tool
import icon
import sources
import optionsbox

"""--------------------------------------------------------------------------------------------"""
"""--------------------------- Here are the Options -------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### one instance of this class stores all the options of RETicker. 

class Options(gobject.GObject):
	def __init__(self, V, Version, user_conf, verbose):
		gobject.GObject.__init__(self)
		## store some init-variables for global access
		self.Version = Version
		self.v = verbose
		if self.v: print "Verbose mode activated"
		pos = V.find(".") + 1
		pos += V[pos:].find(".")
		self.program = "RETicker_" + V[:pos]	+ user_conf
		rox.setup_app_options(self.program)
		
		# debug Option
		self.debug_mode = Option('debug_mode', '0') # 0 = off
		
		# How to decide if 'news' are old
		self.news_age = Option('news_age', '60') # in Min
		self.news_showcount = Option('news_showcount', '0')
		
		# Layout-Options for Ticker
		self.text_color = Option('text_color', '#880000')
		self.back_color = Option('back_color', '#DEDBD6')
		self.transparent = Option('transparent', '0')
		self.back_datei = Option('back_datei', '')
		self.hor_size=Option('hor_size', '-1')
		self.ver_size=Option('ver_size', '20')
		self.borderless=Option('borderless', '0')
		
		# Layout-Optionen (Overview-Window)
		self.ov_show_age = Option('ov_show_age', '1')
		self.ov_show_stat = Option('ov_show_stat', '1')
		self.ov_msg_tip = Option('ov_msg_tip', '1')
		self.ov_bg = Option('ov_bg', '#FFFFFF')
		self.ov_bg_inactive = Option('ov_bg_inactive', '#888888')
		self.ov_bg_stat = Option('ov_bg_stat', '#D70707')
		self.ov_color_new_msg = Option('color_new_msg', '#880000')
		self.ov_color_old_msg = Option('color_old_msg', '#000000')
		self.ov_color_not_shown_msg = Option('color_not_shown_msg', '#666666')
		self.ov_hor_size=Option('ov_hor_size', '400')
		self.ov_ver_size=Option('ov_ver_size', '600')

		# ActiveTooltip-Design
		self.tt_a=Option('tt_a', '1')
		self.tt_a_show_age = Option('tt_a_show_age', '1')
		self.tt_a_show_stat = Option('tt_a_show_stat', '1')
		self.tt_a_msg_tip = Option('tt_a_msg_tip', '1')
		self.tt_a_inactive_fd=Option('tt_a_inactive_fd', '0')
		self.tt_a_fd_wo_news=Option('tt_a_fd_wo_news', '1')
		self.tt_a_as_menu=Option('tt_a_as_menu', '0')
		self.tt_a_bg = Option('tt_a_bg', '#eee2b4')
		self.tt_a_bg_inactive = Option('tt_a_bg_inactive', '#cec294')
		self.tt_a_bg_stat = Option('tt_a_bg_stat', '#eee2b4')
		self.tt_a_color_new_msg = Option('tt_a_color_new_msg', '#880000')
		self.tt_a_color_old_msg = Option('tt_a_color_old_msg', '#000000')
		self.tt_a_color_not_shown_msg = Option('tt_a_color_not_shown_msg', '#666666')
		self.tt_a_hor_size=Option('tt_a_hor_size', '200')
		self.tt_a_ver_size=Option('tt_a_ver_size', '200')
		self.tt_a_hor_scrollbar=Option('tt_a_hor_scrollbar', '0')
		self.tt_a_ver_scrollbar=Option('tt_a_ver_scrollbar', '1')

		# Tooltip-Design Label
		self.tt_l=Option('tt_l', '1') # show Label-ToolTip with Description
		self.tt_l_frame=Option('tt_l_frame', '1')
		self.tt_l_title=Option('tt_l_title', '1')
		self.tt_l_link=Option('tt_l_link', '1')
		self.tt_l_ver=Option('tt_l_ver', '1')
		
		# Tooltip-Design Image
		self.tt_i=Option('tt_i', '0') # show Image-ToolTip with Description
		self.tt_i_frame=Option('tt_i_frame', '1')
		self.tt_i_title=Option('tt_i_title', '1')
		self.tt_i_desc=Option('tt_i_desc', '1')
		self.tt_i_src=Option('tt_i_src', '1')
		self.tt_i_link=Option('tt_i_link', '1')
		self.tt_i_ver=Option('tt_i_ver', '1')

		# Fetch-Options
		self.update_time = Option('update_time', '15') # in sec.
		self.refresh_time= Option('refresh_time', '30') # in Min
		self.check_verbose=Option('check_verbose', '1')
		self.check_image=Option('check_image', '0')
	
		# different paths and browser
		global use_proxy; use_proxy=Option('use_proxy', '0')
		global proxy; proxy=Option('proxy', '')
		self.browser= Option('browser', 'opera')
		self.br_options= Option('br_options', '-newpage')
		try:
			path = os.environ['CHOICESPATH']
			paths = path.split(':')
		except KeyError:
			paths = [ os.environ['HOME'] + '/Choices',
				  '/usr/local/share/Choices',
				  '/usr/share/Choices' ]
		if not(os.path.exists(paths[0])): os.mkdir(paths[0])
		cache = paths[0] + '/' + self.program
		if not(os.path.exists(cache)): os.mkdir(cache)
		xml_cache_ = cache + "/xml_cache"
		if not(os.path.exists(xml_cache_)): os.mkdir(xml_cache_)
		xml_cache_ += "/News.xml"
		self.xml_cache=Option('xml_cache', xml_cache_)
		icon_cache = cache + "/icon_cache"
		if not(os.path.exists(icon_cache)): os.mkdir(icon_cache)
		self.icon_cache_dir=Option('icon_cache_dir', icon_cache)
	
		# This stores iconsets of modified stock icons for faster accessibility
		self.stock_iconsets = icon.Stock_IconSets()
		
		# Sources - there are two version
		# __sources - a xml string which might be modified (and will be stored) by Options Dialog
		# sources   - a class, which contains the actual sources which are used in the program
		# they should mostly be synchronized, but there should be a timeshift between taking over
		# any changes in __sources.value in used sources.
		self.sources = sources.Sources(self)
		self.sources.init_from_xml("<Options><source><active>1</active>" \
			+ "<ticker>http://slashdot.org/slashdot.rdf</ticker>" \
			+ "<icon>http://slashdot.org/favicon.ico</icon>" \
			+ "<iconcache></iconcache><shownews>5</shownews></source></Options>")
		self.__sources = Option('sources', self.sources.export_xml())
	
		# tell rox that there are some options
		rox.app_options.notify()
		rox.app_options.add_notify(self.options_changed)
		
		# store sources Information after getting Option Value
		print "init sources (" + self.sources.stat() + ")"
		self.sources.init_from_xml(self.__sources.value)
		print "read saved sources (" + self.sources.stat() + ")"

		self.OptionsBox = None
	
	#~ def sources_date_info_update(self, dummy, feed):
		#~ self.sources.date_info_update(feed)
		#~ self.__sources.value = self.sources.export_xml()
	
	### thisone is used to switch state of sources from outside
	def sources_switch_feed_active(self, dummy, feed):
		if self.OptionsBox:
			rox.alert("Options-Dialog is open\nPlease change status there or close it")
			self.OptionsBox.present()
			return
		self.sources.switch_feed_active(feed)
		self.__sources.value = self.sources.export_xml()
	
	### thisone is to update the date-info field from feed.py
	def set_provides_date_info(self, source, value):
		if source.set_provides_date_info(value):
			self.__sources.value = self.sources.export_xml()
			self.emit("options_changed_date_info", source)

	### some methods to update the size-informations
	def mainwin_size_changed(self, w, h):
		self.hor_size.value = str(w); self.hor_size.int_value = w
		self.ver_size.value = str(h); self.ver_size.int_value = h
	def act_tick_size_changed(self, dummy, w, h):
		self.tt_a_hor_size.value = str(w); self.tt_a_hor_size.int_value = w
		self.tt_a_ver_size.value = str(h); self.tt_a_ver_size.int_value = h
	def overview_size_changed(self, dummy, w, h):
		self.ov_hor_size.value = str(w); self.ov_hor_size.int_value = w
		self.ov_ver_size.value = str(h); self.ov_ver_size.int_value = h
	
	### this is called if any Option has changed, usually emits a signal
	def options_changed(self):
		if self.__sources.has_changed: self.sources.reinit_from_xml(self.__sources.value)
		if self.update_time.has_changed: self.emit("refresh_update_time")
		if self.refresh_time.has_changed: self.emit("refresh_refresh_time")
		if self.hor_size.has_changed or self.ver_size.has_changed: self.emit("refresh_win_size")
		if self.ov_hor_size.has_changed or self.ov_ver_size.has_changed: self.emit("refresh_ov_size")
		if self.tt_a_hor_size.has_changed or self.tt_a_ver_size.has_changed: self.emit("refresh_tt_a_size")
		if self.text_color.has_changed or self.back_color.has_changed: self.emit("refresh_label_color")
		if self.borderless.has_changed: self.emit("refresh_windowdecorations")
		if self.transparent.has_changed or self.back_datei.has_changed: self.emit("refresh_transparency")
		if self.back_color.has_changed and self.transparent.int_value <> 1: self.emit("refresh_background")
		if self.tt_a_bg.has_changed or self.tt_a_bg_inactive.has_changed \
			or self.tt_a_bg_stat.has_changed or self.tt_a_color_new_msg.has_changed \
			or self.tt_a_color_old_msg.has_changed or self.tt_a_color_not_shown_msg.has_changed:
			self.emit("refresh_ov_colors")
		if self.ov_bg.has_changed or self.ov_bg_inactive.has_changed \
			or self.ov_bg_stat.has_changed or self.ov_color_new_msg.has_changed \
			or self.ov_color_old_msg.has_changed or self.ov_color_not_shown_msg.has_changed:
			self.emit("refresh_ov_colors")
		if self.ov_show_age.has_changed or self.ov_show_stat.has_changed or self.ov_msg_tip.has_changed:
			self.emit("refresh_ov_msgs")
		if self.tt_a_hor_scrollbar.has_changed or self.tt_a_ver_scrollbar.has_changed:
			self.emit("refresh_scrollbars")
		if self.news_age.has_changed or self.news_showcount.has_changed:
			self.emit("refresh_aging_opts")
	
	### a request to show Options Dialog (parallel to rox/options)
	def show_options(self, dummy): tasks.Task(self.edit_options())
	def edit_options(self):
		yield None
		if self.OptionsBox: self.OptionsBox.present(); return
		options_file = os.path.join(rox.app_dir, 'options/Options.xml')
		self.OptionsBox = optionsbox.OptionsBox(self, rox.app_options, options_file)
		def closed(widget): self.OptionsBox = None; Cons.disconnect_all()
		Cons = tool.Connections(); Cons.connect(self.OptionsBox, 'destroy', closed)
		self.OptionsBox.open()

gobject.signal_new("refresh_update_time", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_refresh_time", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_win_size", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_tt_a_size", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_ov_size", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_label_color", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_transparency", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_windowdecorations", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_background", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_ov_colors", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_ov_msgs", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_scrollbars", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_aging_opts", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())

gobject.signal_new("options_changed_date_info", Options, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
