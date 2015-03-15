#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

from __future__ import generators
import rox
from rox import applet, g, tasks

import gobject

import tool
import event_image

# I dont know why but the prog eats memory if I do the calculation directly in set_events()
enter_leave_notify_mask = (g.gdk.ENTER_NOTIFY_MASK | g.gdk.LEAVE_NOTIFY_MASK)


"""--------------------------------------------------------------------------------------------"""
"""------------------------------- Ticker Output Container ------------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### if Applet or Window, the messages will be shown in the following
### box. It contain's the icon and the label and holds methods to
### set and reset mesages and icons
class Label_box(g.HBox):
    	def __init__(self, Options):
    		self.Options = Options
		g.HBox.__init__(self,g.FALSE, 0)
    		### set a little border, then there is space in applet for rox-standard-applet menu
		self.set_border_width(1)
		self.image = TickBild(Options)
		self.label = TickLabel(Options)
    		self.pack_start(self.image, g.FALSE, g.FALSE, 3)
    		self.pack_start(self.label, g.FALSE, g.FALSE, 3)
		self.show()
		self.wait_cont = tool.DelayCall(3, self.reset) # keep last tmp message 3 sek.
		
	### a method to show status messages
	### those messages (and icons) will be deleted after some seconds
	def status(self, Message, Stock = None, File = None):
		if self.Options.check_verbose.int_value: self.label.set_status(Message)
		if self.Options.v: print Message
		if Stock and self.Options.check_image.int_value: self.image.set_tmp(Stock)
		elif self.Options.check_verbose.int_value:
			if Stock: self.image.set_tmp(Stock)
			elif File: self.image.set_tmp(File)
		self.wait_cont.set_value()
	
	### method which will reset icon and label to original value after some seconds
	def reset(self, dummy):
		self.label.reset(); self.image.reset()

	### initiate callback-events, its importend to initiate them after initiating
	### show_list (and subclass news) in main class
	def set_callback_events(self):
		self.label.set_callback_events()
		self.image.set_callback_events()




### The folloing class contains the iconimage and is directly derived from EventImage
### as a special Feauture this class remembers the image (StockOrTicker) and is able
### to restore it (used for displaying graphical status messages)
class TickBild(event_image.EventImage):
	def __init__(self, Options):
    		self.Options = Options
		event_image.EventImage.__init__(self, Options, g.STOCK_MISSING_IMAGE, \
			self.callback_image)
		self.tooltip = g.Tooltips(); self.tooltip.enable()
		self.tooltip.set_tip(self, " " + self.Options.Version + " ")
		self.StockOrTicker = None	# stores the Name of Image

	### second set of Methods for setting/resetting status Icon (parallel to event_image.EventImage)
	def set(self, StockOrTicker):
		self.StockOrTicker = StockOrTicker; self.set_(StockOrTicker)
	def set_tmp(self, StockOrTicker): self.set_(StockOrTicker)
	def reset(self):
		if self.StockOrTicker: self.set_(self.StockOrTicker)
	
	### adding a tooltip as the user like it :)
	def addTip(self, fd, news):
		def brk_tip(tooltip):
			if tooltip == "": return ""
			else: return "\n"
		tooltip = ""
		if self.Options.tt_i.int_value: 
			if self.Options.tt_i_frame.int_value: tooltip += "---------------------------------------------"
			if self.Options.tt_i_title.int_value: tooltip += brk_tip(tooltip) + "Ticker : " + tool.unxml(fd.title).encode("utf-8")
			if self.Options.tt_i_frame.int_value: tooltip += brk_tip(tooltip) + "---------------------------------------------"
			if self.Options.tt_i_desc.int_value:
				desc = fd.desc
				if len(desc) > 100: desc = desc[:100] + "..."
				tooltip += brk_tip(tooltip) + tool.unxml(desc).encode("utf-8")
			if self.Options.tt_i_frame.int_value: tooltip += brk_tip(tooltip)
			if self.Options.tt_i_src.int_value: tooltip += brk_tip(tooltip) + "Src : " + tool.unxml(fd.ticker).encode("utf-8")
			if self.Options.tt_i_link.int_value: tooltip += brk_tip(tooltip) + "Link : " + tool.unxml(fd.link).encode("utf-8")
			if self.Options.tt_i_ver.int_value:  tooltip += brk_tip(tooltip) + " *** " + self.Options.Version + " *** \n" + news.stat()
			self.set_tip(tooltip)
		else:
			self.tooltip.disable()
	def set_tip(self, tooltip): self.tooltip.enable(); self.tooltip.set_tip(self, tooltip)
	
	### the callback on user-clicks on the image sends some signals
	def callback_image(self, widget, event):
		if event.button == 1: self.emit("img_click_button_1")
        	if event.button == 2: self.emit("img_click_button_2")
		if event.button == 3: self.emit("img_click_button_3", event) # event argument is used by menu

	### override the event_image.EventImage methods for entering and leaving the widget
	def enter_widget(self, widget, event):
		self.emit("img_entered"); widget.set_state (g.STATE_PRELIGHT)
		# check if active-tooltip is enabled and shown as tip
		if self.Options.tt_i.int_value == 0 or \
			(self.Options.tt_a.int_value == 1 and self.Options.tt_a_as_menu.int_value == 0):
			self.tooltip.disable()
		else: self.tooltip.enable()
	
	def leave_widget(self, widget, event):
		self.emit("img_leaved"); widget.set_state (g.STATE_NORMAL)

gobject.signal_new("img_click_button_1", TickBild, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("img_click_button_2", TickBild, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("img_click_button_3", TickBild, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("img_entered", TickBild, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("img_leaved", TickBild, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())




### The next Class is a label with two kinds of messages, news and status messages
### news messages should be shown always, but status messages should only be shown
### for some seconds (see parent box class)
class TickLabel(g.EventBox):
	def __init__(self, Options):
		self.Options = Options
		g.EventBox.__init__(self)
		#### create the main label
		self.text = " " + self.Options.Version + " " # The 'normal' Message
		self.label = g.Label(self.text)
		self.label.show()
		self.add(self.label)
		self.tooltip = g.Tooltips(); self.tooltip.enable()
		self.tooltip.set_tip(self, " " + self.Options.Version + " ")
		self.set_events(enter_leave_notify_mask)
		self.set_color()
		self.show()

		self.connect("enter-notify-event", self.enter_widget)
		self.connect("leave-notify-event", self.leave_widget)
		self.connect("button_press_event", self.callback_label)

	### show status message
	def set_status(self, Label): self.label.set_text(Label)
	
	### and reset to 'normal' message
	def reset(self): self.label.set_text(self.text)

	### update changes 'normal' message and double-stores this message in self.text
	def update(self,Label): 
		if (self.Options.debug_mode.int_value > 1):
			import sys; import gc; gc.collect();
			try: Label = str(sys.gettotalrefcount()) + ": " + Label;
			except: Label = "no pydebug: " + Label;
		self.text = Label; self.label.set_text(self.text)

	### as called, to set the text-color (foreground) in normal and prelight stage
	def set_color(self, dummy = None):
		self.label.modify_fg(g.STATE_NORMAL, g.gdk.color_parse(self.Options.text_color.value))
		self.label.modify_fg(g.STATE_PRELIGHT, tool.text_color_prelight(self.Options))

	### adding a tooltip as the user like it :)
	def addTip(self, i):
		def brk_tip(tooltip):
			if tooltip == "": return ""
			else: return "\n"
		tooltip = ""
		if self.Options.tt_l.int_value: 
			if self.Options.tt_l_frame.int_value: tooltip += "---------------------------------------------"
			if self.Options.tt_l_title.int_value: tooltip += brk_tip(tooltip) + tool.unxml(i.title).encode("utf-8")
			if self.Options.tt_l_frame.int_value: tooltip += brk_tip(tooltip) + "---------------------------------------------"
			tooltip += brk_tip(tooltip) + tool.unxml(i.desc).encode("utf-8")
			if self.Options.tt_l_frame.int_value: tooltip += brk_tip(tooltip)
			if self.Options.tt_l_link.int_value: tooltip += brk_tip(tooltip) + "Link   : " + tool.unxml(i.link).encode("utf-8")
			if self.Options.tt_l_ver.int_value:  tooltip += brk_tip(tooltip) + " *** " + self.Options.Version + " *** "
			self.set_tip(tooltip)
		else:
			self.tooltip.disable()
	def set_tip(self, tooltip): self.tooltip.enable(); self.tooltip.set_tip(self, tooltip)

	### the following callbacks are connected an main hirarchie
	def enter_widget(self, widget, event):
		self.emit("lab_tickbild_entered"); widget.set_state (g.STATE_PRELIGHT)
	def leave_widget(self, widget, event):
		self.emit("lab_tickbild_leaved"); widget.set_state (g.STATE_NORMAL)
	def callback_label(self, widget, event):
		print event.button
		if event.button == 1: self.emit("lab_click_button_1")
        	if event.button == 2: self.emit("lab_click_button_2")
		if event.button == 3: self.emit("lab_click_button_3")

gobject.signal_new("lab_click_button_1", TickLabel, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("lab_click_button_2", TickLabel, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("lab_click_button_3", TickLabel, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("lab_tickbild_entered", TickLabel, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("lab_tickbild_leaved", TickLabel, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
