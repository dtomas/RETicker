#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

from __future__ import generators

import rox
from rox import g

import gobject

import event_image
import tool
from RETicker import minsize

"""--------------------------------------------------------------------------------------------"""
"""--------------------------- One Page of the Sources Dialog ---------------------------------"""
"""--------------------------------------------------------------------------------------------"""
### This is a page of the sources configuration container. Its the place to store and edit the
### whole configuration of one source
class SourcesDialogPage(g.VBox):
        def __init__(self, Options):
		g.VBox.__init__(self,g.FALSE,3)
		self.set_border_width(3)
		self.__Options = Options
		
		self.tooltip = g.Tooltips(); self.tooltip.enable()
		

		"""-----------------------------------------------------------------------------------"""
		""" 1. Layout-Area                                                                    """
		"""-----------------------------------------------------------------------------------"""
		
		"""--------------------------- Notebook - Tab- Image ---------------------------------"""
		self.icon_image_tab = event_image.EventImage(self.__Options)
		
		"""--------------------------- News - Source (TickerAddress) --------------------------"""
		# The frame (holds a button and text)
		hbox_tickerer_frame = g.HBox()
		self.ticker_frame_button = event_image.EventImage(self.__Options, g.STOCK_NO, self.switch_active, minsize, "click to activate")
		self.ticker_frame_label = g.Label(" News Source (click button to activate)")
		hbox_tickerer_frame.pack_start(self.ticker_frame_button, g.FALSE, g.FALSE, 0)
		hbox_tickerer_frame.pack_start(self.ticker_frame_label, g.FALSE, g.FALSE, 0)
		
		frame_ticker = g.Frame()
		frame_ticker.set_label_widget(hbox_tickerer_frame)
		frame_ticker.set_shadow_type(g.SHADOW_OUT)
		frame_ticker.set_border_width(3)
		
		# The Entry Area (holds a label and a entry field)
		vbox_ticker = g.VBox()
		vbox_ticker.set_border_width(3)
		frame_ticker.add(vbox_ticker)
		
		hbox_ticker = g.HBox()
		ticker_label = g.Label("source http-address")
		hbox_ticker.pack_start(ticker_label, g.FALSE, g.FALSE, 0)
		
		self.ticker_entry = g.Entry()
		self.tooltip.set_tip(self.ticker_entry, "http-address of ticker (rdf/rss)")
		
		vbox_ticker.pack_start(hbox_ticker, g.FALSE, g.FALSE, 0)
		vbox_ticker.pack_start(self.ticker_entry, g.FALSE, g.FALSE, 0)
		
		self.pack_start(frame_ticker, g.FALSE, g.FALSE, 0)
		
		"""--------------------------- The area below Ticker --------------------------"""
		# a new horizontal Box
		hbox_below_ticker = g.HBox()
		self.pack_start(hbox_below_ticker, g.FALSE, g.FALSE, 0)
		
		
		"""--------------------- Icon Configuration (left side of hbox_below_ticker) --"""
		# first create a frame
		frame_icon = g.Frame("Icon Configuration")
		frame_icon.set_shadow_type(g.SHADOW_ETCHED_OUT)
		frame_icon.set_border_width(3)
		hbox_below_ticker.pack_start(frame_icon, g.FALSE, g.FALSE, 0)
		
		# its all in a vertical box
		vbox_icon_all = g.VBox(g.FALSE, 0)
		vbox_icon_all.set_border_width(3)
		frame_icon.add(vbox_icon_all)
		
		# icon http-address (contains a label, an event_image)
		hbox_icon = g.HBox()
		icon_label = g.Label("http-address")
		#self.icon_button = event_image.EventImage(self.__Options, g.STOCK_CONVERT, self.fetch_icon, g.ICON_SIZE_SMALL_TOOLBAR, "fetch icon from http-address to local address now")
		hbox_icon.pack_start(icon_label, g.FALSE, g.FALSE, 3)
		#hbox_icon.pack_end(self.icon_button, g.FALSE, g.FALSE, 3)
		vbox_icon_all.pack_start(hbox_icon, g.FALSE, g.FALSE, 0)
		
		# the http-address entry field
		self.icon_entry = g.Entry()
		self.tooltip.set_tip(self.icon_entry, "http-address of icon for this ticker (only used if no local icon found)")
		vbox_icon_all.pack_start(self.icon_entry, g.FALSE, g.FALSE, 0)
		
		# Spacer
		space_label= g.Label()
		vbox_icon_all.pack_start(space_label, g.FALSE, g.FALSE, 0)
		
		# local icon address (contains a label, an event_image)
		hbox_iconcache = g.HBox()
		iconcache_label = g.Label("local address (preferred)")
		self.iconcache_button = event_image.EventImage(self.__Options, g.STOCK_OPEN, self.open_cache_file, g.ICON_SIZE_SMALL_TOOLBAR, "choose file")
		hbox_iconcache.pack_start(iconcache_label, g.FALSE, g.FALSE, 0)
		hbox_iconcache.pack_end(self.iconcache_button, g.FALSE, g.FALSE, 0)
		vbox_icon_all.pack_start(hbox_iconcache, g.FALSE, g.FALSE, 0)
		
		# local icon address entry field
		self.iconcache_entry = g.Entry()
		self.tooltip.set_tip(self.iconcache_entry, \
			"local image, if it is found there will be no http-connection established otherwise it will be retrieved to this address")
		vbox_icon_all.pack_start(self.iconcache_entry, g.FALSE, g.FALSE, 0)
		
		# label under the entry field to indicate if icon is in local cache
		self.icon_in_local_cache_label = g.Label("[ icon in cachdir - see path conf ]")
		vbox_icon_all.pack_start(self.icon_in_local_cache_label, g.FALSE, g.FALSE, 0)
		
		"""--------------------- (right side of hbox_below_ticker) -----------------------"""
		# on the right side there are two frames, both in a vbox
		vbox_right_all = g.VBox()
		hbox_below_ticker.pack_start(vbox_right_all, g.FALSE, g.FALSE, 0)
		
		"""--------------------- Number of News (upper area of right side below ticker) --"""
		# first create a frame
		frame_news = g.Frame("Ticker Configuration")
		frame_news.set_shadow_type(g.SHADOW_ETCHED_OUT)
		frame_news.set_border_width(3)
		vbox_right_all.pack_start(frame_news, g.FALSE, g.FALSE, 0)
		
		# Number of news to show (contains label and SpinButton)
		hbox_num_of_news = g.HBox(g.FALSE, 3)
		frame_news.add(hbox_num_of_news)
		hbox_num_of_news.set_border_width(3)
		num_of_news_label = g.Label("max. Number\nof News to show")
		self.num_of_news_spin = g.SpinButton(g.Adjustment(5, 1, 300, 1, 10, 10))
		self.tooltip.set_tip(self.num_of_news_spin, "maximum Number of news from this source to show in Ticker")
		hbox_num_of_news.pack_start(num_of_news_label, g.FALSE, g.FALSE, 0)
		hbox_num_of_news.pack_end(self.num_of_news_spin, g.FALSE, g.FALSE, 0)
		
		"""--------------------- max News-Age (lower area of right side below ticker) --"""
		""" only shown if ticker provides date information in dc_date field             """
		# first create a frame
		self.frame_date = g.Frame("[ticker provides date info]")
		self.frame_date.get_label_widget().modify_fg(g.STATE_NORMAL, g.gdk.color_parse('#008000'))
		self.frame_date.set_shadow_type(g.SHADOW_ETCHED_OUT)
		self.frame_date.set_border_width(3)
		vbox_right_all.pack_start(self.frame_date, g.FALSE, g.FALSE, 0)
		
		# max age of news (by date stamp)
		hbox_date = g.HBox(g.FALSE, 3)
		self.frame_date.add(hbox_date)
		hbox_date.set_border_width(3)
		date_label = g.Label("max news-age\nin minutes\n(0 to ignore)")
		self.date_spin = g.SpinButton(g.Adjustment(5, 0, 10000, 1, 10, 10))
		self.tooltip.set_tip(self.num_of_news_spin, "maximal age of message till its declared as old and not shown in Ticker anymore")
		hbox_date.pack_start(date_label, g.FALSE, g.FALSE, 0)
		hbox_date.pack_end(self.date_spin, g.FALSE, g.FALSE, 0)
		
		
		self.show_all()
		
		"""-----------------------------------------------------------------------------------"""
		""" 2. Variables                                                                      """
		"""-----------------------------------------------------------------------------------"""
		self.active = 1
		self.ticker = ""
		self.icon = ""
		self.def_icon = "" 		# default icon http-address
		self.iconcache = ""
		self.def_iconcache = "" 	# default icon local address (in cache)
		self.news_age_by_date = 0
		self.provides_date_info = None
		self.shownews = 5
		
		### Some delay_calls, fired if values are constant for a special time
		self.DelayCall_ticker = tool.DelayCall(0, self.change_ticker)
		self.DelayCall_icon = tool.DelayCall(0, self.change_icon)
		self.DelayCall_iconcache = tool.DelayCall(0, self.change_iconcache)
		self.DelayCall_shownews = tool.DelayCall(0, self.change_shownews)
		self.DelayCall_news_age_by_date = tool.DelayCall(0, self.change_news_age_by_date)
		
		
		"""-----------------------------------------------------------------------------------"""
		""" 3. Signals and connections                                                        """
		"""-----------------------------------------------------------------------------------"""
		self.sig_ticker = None
		self.sig_icon = None
		self.sig_iconcache = None
		self.sig_news_age_by_date = None
		self.sig_shownews = None
		self.sig_active = None
		
		self.block_sig_ticker = 0	# to remember who blocked the signals
		self.block_sig_icon = 0
		
		self.Cons = tool.Connections()
		self.connect("destroy", self.disconnect_all)

	### The usual method to disconnect all made connections at the end
	def disconnect_all(self, dummy=None): self.Cons.disconnect_all()
	
	### tool-like methods to shrink/grow printed path (used in iconcache-entryfield)
	def short_dir(self,value):
		if value.find(self.__Options.icon_cache_dir.value) == 0:
			return "[...]"+value[len(self.__Options.icon_cache_dir.value):]
		return value
	def long_dir(self,value):
		if value.find("[...]") == 0:
			return self.__Options.icon_cache_dir.value + value[5:]
		return value	

	### this method is used to refresh the shown tab image
	def refresh_tab_image(self, dummy=None, source = None):
		# cause this is usually called if source was added, refresh a connection if not still there
		if source:
			if source <> self.__Options.sources.get_by_ticker(self.ticker): return
		else: source = self.__Options.sources.get_by_ticker(self.ticker)
		
		if source: self.Cons.connect_new(source, "change_iconset", self.refresh_tab_image)
		self.icon_image_tab.set(self.ticker)
		self.tooltip.set_tip(self.icon_image_tab, self.ticker)
		
	
	### if ticker provides dc_date field, the additional options should be shown
	def check_date_area(self, dummy = None, source = None):
		# cause this is usually called if source was added, refresh a connection if not still there
		if source:
			if source <> self.__Options.sources.get_by_ticker(self.ticker): return
		else: source = self.__Options.sources.get_by_ticker(self.ticker)
		
		if source: self.provides_date_info =  source.get_provides_date_info()
		if self.provides_date_info: self.frame_date.show()
		else: self.frame_date.hide()

	"""-----------------------------------------------------------------------------------"""
	""" 1. Signals                                                                        """
	"""-----------------------------------------------------------------------------------"""
	### signals are usually connected to check_* method, they might be activated or deactivated	
	def activate_Signals(self):
		if self.__Options.v: print "activate Page-Item SIGNALs"
		if not(self.sig_ticker): self.sig_ticker = self.ticker_entry.connect('changed',self.check_ticker)
		if not(self.sig_icon): self.sig_icon = self.icon_entry.connect('changed',self.check_icon)
		if not(self.sig_iconcache): self.sig_iconcache = self.iconcache_entry.connect('changed',self.check_iconcache)
		if not(self.sig_shownews): self.sig_shownews = self.num_of_news_spin.connect('value-changed',self.check_shownews)
		if not(self.sig_news_age_by_date): self.sig_news_age_by_date = self.date_spin.connect('value-changed',self.check_news_age_by_date)
	def deactivate_Signals(self):
		if self.__Options.v: print "deactivate Page-Item SIGNALs"
		if self.sig_ticker:
			self.ticker_entry.disconnect(self.sig_ticker); self.sig_ticker = None
		if self.sig_icon:
			self.icon_entry.disconnect(self.sig_icon); self.sig_icon = None
		if self.sig_iconcache:
			self.iconcache_entry.disconnect(self.sig_iconcache); self.sig_iconcache = None
		if self.sig_shownews:
			self.num_of_news_spin.disconnect(self.sig_shownews); self.sig_shownews = None
		if self.sig_news_age_by_date:
			self.date_spin.disconnect(self.sig_news_age_by_date); self.sig_news_age_by_date = None
	
	"""-----------------------------------------------------------------------------------"""
	""" 2. DelayCalls                                                                     """
	"""-----------------------------------------------------------------------------------"""
	### if you change a value, it is not directly used to build a new configuration. If it
	### keeps stable for a shorter period (for instance 0.5 sec.) it is taken over into field
	### values
	def check_shownews(self,value): self.DelayCall_shownews.set_value(self.num_of_news_spin.get_value())
	def check_news_age_by_date(self,value): self.DelayCall_news_age_by_date.set_value(self.date_spin.get_value())
	def check_ticker(self,value): self.DelayCall_ticker.set_value(self.ticker_entry.get_text())
	def check_icon(self,value): self.DelayCall_icon.set_value(self.icon_entry.get_text())
	def check_iconcache(self,value): self.DelayCall_iconcache.set_value(self.iconcache_entry.get_text())
	def unset_DelayCall_times(self):	
		self.DelayCall_ticker.set_time(0)
		self.DelayCall_icon.set_time(0)
		self.DelayCall_iconcache.set_time(0)
		self.DelayCall_shownews.set_time(0)
		self.DelayCall_news_age_by_date.set_time(0)
	def set_DelayCall_times(self):	
		self.DelayCall_ticker.set_time(0.5)
		self.DelayCall_icon.set_time(0.5)
		self.DelayCall_iconcache.set_time(0.5)
		self.DelayCall_shownews.set_time(0.5)
		self.DelayCall_news_age_by_date.set_time(0.5)
	
	
	"""-----------------------------------------------------------------------------------"""
	""" 3. Modify Values                                                                  """
	"""-----------------------------------------------------------------------------------"""
	### usually methods of this section are reached after changing the value, a signal was
	### then emitted and then the delay was over - ok, now use the new value
	def change_shownews(self,value):
		self.shownews = int(self.num_of_news_spin.get_value())
		if self.__Options.v: print "changed shownews"
		self.emit('changed_Page')
	
	def change_news_age_by_date(self,value):
		self.news_age_by_date = int(self.date_spin.get_value())
		if self.__Options.v: print "changed news_age_by_date"
		self.emit('changed_Page')
	
	### the following methods are more complex, changing of ticker for instance changes 
	### also the default icon name, if there is no special entry there, it has to be adapted
	def change_ticker(self,value):
		self.deactivate_Signals()
		self.block_sig_ticker = 1	# remember that signals were blocked by change_ticker
		
		# get new ticker
		self.ticker = self.ticker_entry.get_text()
		
		""" default icon postion has changed too """
		# get server name
		if self.ticker.find("http://") == 0:
			pos = self.ticker[8:].find("/")
			if pos <> -1: pos = pos + 8
		else:	pos = self.ticker.find("/")
		# and add favicon.ico to get default icon position
		if pos <> -1: self.def_icon =  self.ticker[:pos] + "/favicon.ico"
		else:	self.def_icon =  self.ticker + "/favicon.ico"
		
		# if self.icon is not set, use new default value
		if self.icon == "":
			self.icon_entry.set_text(self.def_icon)
			self.icon_entry.modify_text(g.STATE_NORMAL,self.icon_entry.get_colormap().alloc_color('grey'))
			self.check_icon(None)
		
		self.Cons.disconnect_all()
		source = self.__Options.sources.get_by_ticker(self.ticker)
		if source: self.Cons.connect(source, "change_iconset", self.refresh_tab_image)
		self.Cons.connect(self.__Options, "options_changed_date_info", self.check_date_area)
		self.Cons.connect(self.__Options.sources, "source_added", self.refresh_tab_image)
		self.Cons.connect(self.__Options.sources, "source_added", self.check_date_area)
		
		# reactivate signals
		if self.__Options.v: print "changed ticker"
		self.block_sig_ticker = 0
		self.activate_Signals()
		self.emit('changed_Page')
	
	### see above method, changing of iconcache also changes the default iconcache name
	def change_icon(self,value):
		# deactivate signals and remember, that we have to activate them later again
		if not(self.block_sig_ticker): self.deactivate_Signals()
		self.block_sig_icon = 1
		
		# get new icon address
		tmp_icon = self.icon_entry.get_text()
		# if it is the same than the defautl address, delete the entry
		""" default iconcache postion has changed too """
		if tmp_icon <> self.def_icon:
			self.icon = tmp_icon
			self.def_iconcache = tool.cache_filename(self.__Options.icon_cache_dir.value, tmp_icon)
			self.icon_entry.modify_text(g.STATE_NORMAL,self.icon_entry.get_colormap().alloc_color('black'))
		else: 	
			self.icon = ""
			self.def_iconcache = tool.cache_filename(self.__Options.icon_cache_dir.value, self.def_icon)
			self.icon_entry.modify_text(g.STATE_NORMAL,self.icon_entry.get_colormap().alloc_color('grey'))
		
		# if self.iconcache is not set, use new default value
		if self.iconcache == "":
			self.iconcache_entry.set_text(self.short_dir(self.def_iconcache))
			self.icon_in_local_cache_label.show()
			self.iconcache_entry.modify_text(g.STATE_NORMAL,self.iconcache_entry.get_colormap().alloc_color('grey'))
			self.check_iconcache(None)
		
		# reactivate signals
		if self.__Options.v: print "changed icon"
		if not(self.block_sig_ticker):
			self.block_sig_icon = 0
			self.activate_Signals()
			self.emit('changed_Page')
		else: self.block_sig_icon = 0
	
	### change the iconcache name
	def change_iconcache(self,value):
		if not(self.block_sig_ticker) and not(self.block_sig_icon): self.deactivate_Signals()
		
		# get the new iconcache name
		tmp_iconcache = self.short_dir(self.iconcache_entry.get_text())
		
		# if local address is in defautl cache, show this
		if tmp_iconcache.find("[...]") == 0:
			self.icon_in_local_cache_label.show()
			self.iconcache_entry.set_text(tmp_iconcache)
		else: self.icon_in_local_cache_label.hide()

		# check if it is really a new entry or the same as the default value
		if tmp_iconcache <> self.short_dir(self.def_iconcache):
			self.iconcache = tmp_iconcache
			self.iconcache_entry.modify_text(g.STATE_NORMAL,self.iconcache_entry.get_colormap().alloc_color('black'))
		else:
			self.iconcache = ""
			self.iconcache_entry.set_text(tmp_iconcache)
			self.iconcache_entry.modify_text(g.STATE_NORMAL,self.iconcache_entry.get_colormap().alloc_color('grey'))

		# reactivate signals
		if self.__Options.v: print "changed iconcache"
		if not(self.block_sig_ticker) and not(self.block_sig_icon):
			self.activate_Signals()
			self.emit('changed_Page')


	"""-----------------------------------------------------------------------------------"""
	""" 4. Callbacks for Buttons                                                          """
	"""-----------------------------------------------------------------------------------"""
	### switch the activation state of the source
	def switch_active(self, widget, event):
		if self.__Options.v: print "switch active"
		if self.active == 1: self.active = 0
		else: self.active = 1
		self.check_active()		
	### adapt the activation button color and the text beneath to actual state
	def check_active(self):
		if self.active == 1:
			self.ticker_frame_button.set(g.STOCK_YES)
			self.ticker_frame_button.set_tip("click to deactivate")
			self.ticker_frame_label.set_text(" News Source (click button to deactivate)")
		else:
			self.ticker_frame_button.set(g.STOCK_NO)
			self.ticker_frame_button.set_tip("click to activate")
			self.ticker_frame_label.set_text(" News Source (click button to activate)")
		self.icon_image_tab.set_active(self.active)
		if self.__Options.v: print "changed active"
		self.emit('changed_Page')
	
	### Open file and get the filename, set value in iconcache
	def open_cache_file(self, widget, event):
		def set_cache_file(widget):
			sel.hide()
			self.iconcache_entry.set_text(sel.get_filename())
			self.check_iconcache(None)
		def exit(widget):
			sel.hide()
		if event.button == 1:
			sel = g.FileSelection()
			if self.iconcache <> "":
				sel.set_filename(self.long_dir(self.iconcache))
			else: sel.set_filename(self.long_dir(self.def_iconcache))
			sel.connect("destroy", exit)
			sel.ok_button.connect("clicked", set_cache_file)
			sel.cancel_button.connect("clicked", exit)
			sel.show()

	### method to fetch the icon, at the moment it has no function, sorry
	def fetch_icon(self, widget, event): self.emit("refresh_icon_Page", self.ticker)

	
	
	"""-----------------------------------------------------------------------------------"""
	""" 5. In- and Export af source information                                           """
	"""-----------------------------------------------------------------------------------"""
	### set Page Values from given xml-string, if value is None create a new, empty page
	def set(self, value = None):
		# deactivate Signals and make changing faster
		self.deactivate_Signals()
		self.unset_DelayCall_times()
		
		# if some value is given, read all data from xml
		if value:
			self.active = tool.getintdata(value, "active")
			
			tmp_ticker = tool.getdata(value, "ticker")
			self.ticker_entry.set_text(tmp_ticker); self.check_ticker(None)
			
			tmp_icon = tool.getdata(value, "icon")
			if tmp_icon <> "": self.icon_entry.set_text(tmp_icon); self.check_icon(None)
			
			tmp_iconcache = tool.getdata(value, "iconcache")
			if tmp_iconcache <> "": self.iconcache_entry.set_text(tmp_iconcache); self.check_iconcache(None)
			
			self.shownews = tool.getintdata(value, "shownews")
			self.num_of_news_spin.set_value(self.shownews)
			self.news_age_by_date = tool.getintdata(value, "news_age_by_date")
			self.date_spin.set_value(self.news_age_by_date)
			self.provides_date_info = tool.getintdata(value, "provides_date_info")
			self.refresh_tab_image()
		
		# activate special fields or buttons
		self.check_active()
		self.check_date_area()
		
		# reactivate signals and give entrys a delay
		self.set_DelayCall_times()
		self.activate_Signals()
	
	### export values of all variables as xml
	def _to_xml(self, parent):
		if self.ticker == '': return
		def createNode(doc, name, data):
			node = doc.createElement(name)
			node.appendChild(doc.createTextNode(data))
			return node
		doc = parent.ownerDocument
		parent.appendChild(createNode(doc, 'active', str(self.active)))
		parent.appendChild(createNode(doc, 'ticker', tool.unxml(self.ticker)))
		parent.appendChild(createNode(doc, 'icon', tool.unxml(self.icon)))
		if self.iconcache <> "": parent.appendChild(createNode(doc, 'iconcache', self.long_dir(self.iconcache)))
		else:			parent.appendChild(createNode(doc, 'iconcache', ""))
		parent.appendChild(createNode(doc, 'shownews', str(self.shownews)))
		parent.appendChild(createNode(doc, 'news_age_by_date', str(self.news_age_by_date)))
		parent.appendChild(createNode(doc, 'provides_date_info', str(self.provides_date_info)))
		return doc

gobject.signal_new("changed_Page", SourcesDialogPage, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("refresh_feed_Page", SourcesDialogPage, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.signal_new("refresh_icon_Page", SourcesDialogPage, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
