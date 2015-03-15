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

import tool

# I dont know why but the prog eats memory if I do the calculation directly in set_events()
enter_leave_notify_mask = (g.gdk.ENTER_NOTIFY_MASK | g.gdk.LEAVE_NOTIFY_MASK)


"""--------------------------------------------------------------------------------------------"""
"""--------------------------- An Image in an Eventbox ----------------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### This calss is widely used in the program toi have an image to click on. if you give the
### optional param press_event, it will be called if image(button) pressed. The Param StockOrTicker
### contains a valid Stcok description (should start with 'gtk-') or a name of a ticker
class EventImage(g.EventBox):
	def __init__(self, Options, StockOrTicker = g.STOCK_MISSING_IMAGE, \
				press_event = None, size = g.ICON_SIZE_SMALL_TOOLBAR, tooltip = None):
		
		# ok, image and eventbox
		self.__Options = Options
		self.size = size
		g.EventBox.__init__(self)
		self.image = g.Image()
		self.add(self.image)
		
		# now some connections
		self.set_events(enter_leave_notify_mask)
		if press_event <> None:
			self.connect('button_press_event', self.button_pressed)
			self.connect('button_press_event', press_event)
			self.connect('button_release_event', self.button_released)
		self.connect("enter-notify-event", self.enter_widget)
		self.connect("leave-notify-event", self.leave_widget)

		self.Cons = tool.Connections()
		self.connect("destroy", self.disconnect_all)
		
		# the actual image is always set from the following iconset
		self.__iconset = None
		self.set(StockOrTicker)
		
		self.image.show()
		self.show()
		
		if tooltip: self.set_tip(tooltip)
		
	### remove all connections if destroyed
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()

	### Changing the States of the Image
	def enter_widget(self, widget=None, event=None): self.image.set_state(g.STATE_PRELIGHT)
	def leave_widget(self, widget=None, event = None): self.image.set_state(g.STATE_NORMAL)
	def set_active(self, active): self.image.set_sensitive(active)
	def button_pressed(self, widget, event): self.image.set_state(g.STATE_SELECTED)
	def button_released(self, widget, event): tasks.Task(self.blink())
	def blink(self):
		for i in range(0, 6):
			self.image.set_state(g.STATE_PRELIGHT); yield tasks.TimeoutBlocker(0.02)
			self.image.set_state(g.STATE_NORMAL); yield tasks.TimeoutBlocker(0.02)
	
	### The set Method refers to the set_ method - this makes it easyer to override it (see output.py)
	def set(self, StockOrTicker): self.set_(StockOrTicker)
	def set_(self, StockOrTicker):
		# if there were old connections, remove them
		self.Cons.disconnect(self.__iconset, "icon_changed")
		self.Cons.disconnect(self.__iconset, "icon_at_url_not_retrieved")
		if StockOrTicker.find('gtk-') == 0:
			# ok, its a stock image, get it from Options.stock_iconsets
			self.image.set_from_icon_set(self.__Options.stock_iconsets.get(StockOrTicker), self.size)
		else: 
			# ahh, its a ticker name. so get the iconset from Options.sources
			self.__iconset = self.__Options.sources.get_iconset_by_ticker(StockOrTicker)
			if self.__iconset:
				# iconset for ticker was found, connect and refresh
				self.Cons.connect(self.__iconset, "icon_changed", self.refresh) # To keep Icon up to date
				self.Cons.connect(self.__iconset, "icon_at_url_not_retrieved", self.no_icon) # To react if no icon 
				self.refresh()
			else: self.set_(g.STOCK_DIALOG_ERROR) ### maybe Source was killed in meantime
	### called if "icon_changed"
	def refresh(self, dummy = None): self.image.set_from_icon_set(self.__iconset.get(), self.size)
	
	### called if "icon_at_url_not_retrieved"
	def no_icon(self, dummy = None): self.image.set_from_icon_set(self.__Options.stock_iconsets.get(g.STOCK_MISSING_IMAGE), self.size)
	
	## set and remove tooltips
	def set_tip(self, Text):
		if not(Text): return
		self.tooltip = g.Tooltips(); self.tooltip.enable()
		self.tooltip.set_tip(self, Text)
	def rem_tip(self):
		self.tooltip.disable()
