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
import time

# I dont know why but the prog eats memory if I do the calculation directly in set_events()
enter_leave_notify_mask = (g.gdk.ENTER_NOTIFY_MASK | g.gdk.LEAVE_NOTIFY_MASK)

"""--------------------------------------------------------------------------------------------"""
"""------ a class which shows all messages of one feed (to use it in activetip or overview) ---"""
"""--------------------------------------------------------------------------------------------"""				
### as some other classes which are used in activetooltip, the ov_feed is once created and than
### if needed filled with new contents by reinit-method
class ov_feed(g.EventBox):
	def __init__(self, Options, tooltips, overview = None):
		self.__Options = Options
		self.__tooltips = tooltips
		self.__overview = overview ## to recognize the different color used by window

		########################
		g.EventBox.__init__(self)
		
		self.__feed = None
		self.vbox = None
		self.label1 = None	# those labels are used to show
		self.label2 = None	# something if no message is available
		self.list_of_msgs = []
		
		self.Cons = tool.Connections()
		self.Cons.connect(self.__Options, "refresh_ov_colors", self.refresh_colors)
		self.connect("destroy", self.disconnect_all)
	
	### remove all connections, also all connections in list_of_msgs
	def disconnect_all(self, dummy=None):
		self.Cons.disconnect_all()
		for msg in self.list_of_msgs: msg.disconnect_all(); del msg
		self.list_of_msgs = []
	
	### use the colors which are set in Options
	def refresh_colors(self, dummy = None):
		if self.__feed.get_active() == 1:
			if self.__overview: bg_color = self.__Options.ov_bg.value
			else: bg_color = self.__Options.tt_a_bg.value
		else:
			if self.__overview: bg_color = self.__Options.ov_bg_inactive.value
			else: bg_color = self.__Options.tt_a_bg_inactive.value
		self.modify_bg(g.STATE_NORMAL,self.get_colormap().alloc_color(bg_color))
		if self.__overview: fg_color = self.__Options.ov_color_old_msg.value
		else: fg_color = self.__Options.tt_a_color_old_msg.value
		
		if self.label1:
			self.label1.modify_fg(g.STATE_NORMAL,self.label1.get_colormap().alloc_color(fg_color))
		if self.label2:
			self.label2.modify_fg(g.STATE_NORMAL,self.label2.get_colormap().alloc_color(fg_color))
	
	### fills the structure with contents of the news-feed
	def reinit(self, fd):
		# if there was something before, remove the connections made
		if self.__feed:
			self.Cons.disconnect(self.__Options.sources.get_by_ticker(self.__feed.ticker), "change_active")
		for msg in self.list_of_msgs: msg.disconnect_all()
		self.list_of_msgs = []
		# if there was an vbox before, remove it
		if self.vbox: self.remove(self.vbox); del self.vbox; self.vbox = None
		# ok, now we can really start to fill the structure
		count = 1 # it is needed to check, if number of mesage is greather than number
			  # number of messages to show in ticker
		if not(fd): return
		
		# recreate just deleted elems
		self.vbox = g.VBox()
		self.add(self.vbox)
		self.__feed = fd
		self.Cons.connect(self.__Options.sources.get_by_ticker(self.__feed.ticker), "change_active", self.refresh_colors)
		
		if len(self.__feed.msg) <> 0:
			# there are messages in feed
			for i in self.__feed.msg:
				msg = ov_message(self.__Options, self.__tooltips, self.__feed, i, count, self.__overview)
				self.list_of_msgs.append(msg)
				self.vbox.pack_start(msg, g.FALSE, g.FALSE, 0)
				count += 1
			#import sys; import gc; gc.collect();
			#print "added " + str(count-1) + " messages" + \
			#	" --> refrences to Options: " + str(sys.getrefcount(self.__Options))
			self.label1 = None
			self.label2 = None
		else:
			# there are no messages found in feed
			if self.label1: del self.label1
			if self.label2: del self.label2
			self.label1=g.Label("no messages available")
			self.label1.set_size_request(-1,-1)
			self.label1.set_alignment(0,0)
			self.label1.set_padding(3,0)
			self.label1.show()
			self.label2=g.Label("maybe you have to\nactivate ticker or\nrefresh the news")
			self.label2.set_size_request(-1,-1)
			self.label2.set_alignment(0,0)
			self.label2.set_padding(3,0)
			self.label2.show()
			self.vbox.pack_start(self.label1, g.FALSE, g.FALSE, 0)
			self.vbox.add(self.label2)
		self.refresh_colors()
		self.show_all()


"""--------------------------------------------------------------------------------------------"""
"""------ a class which shows a message (to use it in activetip or overview) ------------------"""
"""--------------------------------------------------------------------------------------------"""				
### this is a class for one message, it reacts on events and open pages etc.
class ov_message(g.EventBox):
	def __init__(self, Options, tooltips, feed, msg, count, overview = None):
		self.__Options = Options
		self.__tooltips = tooltips
		self.__feed = feed
		self.__overview = overview ## to recognize the different color used by window and tip
		self.__msg = msg
		self.__count = count

		###############
		g.EventBox.__init__(self)
		
		self.text = tool.unxml(self.__msg.title).encode("utf-8")
		
		### create additional information
		page_time = msg.fetchtime
		self.time_val = time.strftime("%a %H:%M", time.localtime(page_time))
		if msg.time <> 0:	page_time = msg.time; self.time_val += time.strftime(" [%a %H:%M]", time.localtime(page_time))
		
		self.stat = "[" + str(msg.showcount) + "x]"

		if (self.__overview):
			self.show_age = self.__Options.ov_show_age.int_value
			self.show_stat = self.__Options.ov_show_stat.int_value
			self.show_tip = self.__Options.ov_msg_tip.int_value
		else:
			self.show_age = self.__Options.tt_a_show_age.int_value
			self.show_stat = self.__Options.tt_a_show_stat.int_value
			self.show_tip = self.__Options.tt_a_msg_tip.int_value
		
		if self.show_tip: self.create_tooltip()
		
		self.__label=g.Label() 
		self.refresh_msg_text()
		
		self.__label.set_size_request(-1,-1)
		self.__label.set_alignment(0,0)
		self.__label.set_padding(3,0)
		self.__label.show()
		self.add(self.__label)
		
		self.show()
		
		self.set_events(enter_leave_notify_mask)
		self.connect("enter-notify-event", self.enter_widget)
		self.connect("leave-notify-event", self.leave_widget)
		self.connect("button_press_event", self.callback_event)

		self.source = self.__Options.sources.get_by_ticker(self.__feed.get_ticker())
		self.refresh_colors()
		#print "message-Quelle " + str(self.source)
		
		self.Cons = tool.Connections()
		self.connect("destroy", self.disconnect_all)
		self.Cons.connect(self.source, "change_active", self.refresh_colors)
		self.Cons.connect(self.source, "change_shownews", self.refresh_colors)
		self.Cons.connect(self.source, "change_news_age_by_date", self.refresh_colors)
		self.Cons.connect(self.source, "change_provides_date_info", self.refresh_colors)
		self.Cons.connect(self.__Options, "refresh_ov_colors", self.refresh_colors)
		self.Cons.connect(self.__Options, "refresh_aging_opts", self.refresh_colors)
		if self.__overview: self.Cons.connect(self.__Options, "refresh_ov_msgs", self.refresh_msg_text)
		
	### remoive all connections before destroying any instance
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()
	
	### create tooltip of single message by Options.
	def create_tooltip(self):
		tiptext = ""
		if self.show_age == 1: tiptext += self.time_val
		if tiptext <> "": tiptext += " "
		if self.show_stat == 1: tiptext += self.stat
		if tiptext <> "": tiptext = self.text + " (" + tiptext + ")"
		else: tiptext = self.text
		desc = tool.unxml(self.__msg.desc.encode("utf-8"))
		from message import EMPTY_DESC
		if desc <> EMPTY_DESC:
			tiptext += "\n---------------------\n" + desc
		self.__tooltips.set_tip(self, tiptext)
	
	### set message text. if tooltip is deactivated an stat or time should be shown, it will
	### be shown in the label widget
	def refresh_msg_text(self, dummy=None):
		text_new = ""
		if self.show_tip == 0:
			if self.show_age == 1: text_new += self.time_val
			if text_new <> "": text_new += " "
			if self.show_stat == 1: text_new += self.stat
			if text_new <> "": text_new += " "
		text_new += self.text
		self.__label.set_text(text_new)	
	
	### set the colors of the message depending on message status
	def refresh_colors(self, dummy = None):
		# get the values from options, depending on where to show message
		if (self.__overview):
			bg = self.__Options.ov_bg.value
			bg_inactive = self.__Options.ov_bg_inactive.value
			old_msg = self.__Options.ov_color_old_msg.value
			new_msg = self.__Options.ov_color_new_msg.value
			not_shown_msg = self.__Options.ov_color_not_shown_msg.value
		else:
			bg = self.__Options.tt_a_bg.value
			bg_inactive = self.__Options.tt_a_bg_inactive.value
			old_msg = self.__Options.tt_a_color_old_msg.value
			new_msg = self.__Options.tt_a_color_new_msg.value
			not_shown_msg = self.__Options.tt_a_color_not_shown_msg.value
		
		if self.__feed.get_active() == 1: bg_color = bg
		else: bg_color = bg_inactive
		
		if self.__count > self.__feed.get_shownews(): fg_color = not_shown_msg
		elif self.__feed.msg_is_new(self.__msg): fg_color = new_msg
		else: fg_color = old_msg
		
		self.__label.modify_fg(g.STATE_NORMAL,self.__label.get_colormap().alloc_color(fg_color))
		self.modify_bg(g.STATE_NORMAL,self.get_colormap().alloc_color(bg_color))

	### set the states by entering and leaving the message
	def enter_widget(self, widget, event):
		widget.set_state (g.STATE_PRELIGHT)
	def leave_widget(self, widget, event):
		widget.set_state (g.STATE_NORMAL)
	
	### callback if a button was pressed over the message
	def callback_event(self, widget, event):
		widget.set_state (g.STATE_SELECTED)
		if event.button == 1: tasks.Task(self.open_page())
	
	### open a page, must be started as a task to prevent the from stopping
	def open_page(self):
        	yield None
		# set the color to the ione of a read message
		if self.__overview: fg_color = self.__Options.ov_color_old_msg.value
		else: fg_color = self.__Options.tt_a_color_old_msg.value
		self.modify_fg(g.STATE_NORMAL,self.get_colormap().alloc_color(fg_color))
		# mark message read
		self.__msg.read = 1
		yield None
		# open page in browser
		tool.openPage(self.__msg.link, self.__Options)

