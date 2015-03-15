#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

import rox
from rox import g, Menu
from rox.Menu import Menu, set_save_name

import gobject

"""--------------------------------------------------------------------------------------------"""
"""------------- The Menu, which is shown if you right-click on the image ---------------------"""
"""--------------------------------------------------------------------------------------------"""
### It is only shown, if active-tooltip is not shwon as a menu. As you could see, its a quite
### simple structure with signals
class menu(gobject.GObject, Menu):
	def __init__(self, Options, Window):
		gobject.GObject.__init__(self)
		self.__Options = Options
		set_save_name(self.__Options.program)
		Menu.__init__(self, 'main', [
		('/Quit',		'quit',		'<StockItem>',  '', g.STOCK_QUIT),
		('/Help',          	'help',         '<StockItem>',  '', g.STOCK_HELP),
		('/Info',          	'info',         '<StockItem>',  '', g.STOCK_DIALOG_INFO),
		('/',		'',		'<Separator>'),
		('/Show Window',        'show_window',  '<StockItem>',  '', g.STOCK_INDEX),
		('/Options',            'show_options', '<StockItem>',  '', g.STOCK_PREFERENCES),
		('/',		'',		'<Separator>'),
		('/Refresh',            'refresh_ticker', '<StockItem>',  '', g.STOCK_REFRESH),
		('/Go To',		'',		'<Branch>'),
		('/Go To/Prev Feed',           'prev_feed', '<StockItem>',  '', g.STOCK_GO_BACK),
		('/Go To/Next Feed',           'next_feed', '<StockItem>',  '', g.STOCK_GO_FORWARD),
		('/Go To/',		'',		'<Separator>'),
		('/Go To/Prev Msg',            'prev_msg', '<StockItem>',  '', g.STOCK_GO_BACK),
		('/Go To/Next Msg',            'next_msg', '<StockItem>',  '', g.STOCK_GO_FORWARD)
		])
		self.attach(Window, self)
	def quit(self): self.emit("m_quit")
	def help(self): self.emit("m_help")
	def info(self): self.emit("m_info")
	def show_window(self): self.emit("m_show_window")
	def show_options(self): self.emit("m_show_options")
	def refresh_ticker(self): self.emit("m_refresh_ticker")
	def prev_feed(self): self.emit("m_prev_feed")
	def next_feed(self): self.emit("m_next_feed")
	def prev_msg(self): self.emit("m_prev_msg")
	def next_msg(self): self.emit("m_next_msg")
	
gobject.signal_new("m_quit", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_help", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_info", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_show_window", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_show_options", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_refresh_ticker", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_prev_feed", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_next_feed", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_prev_msg", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
gobject.signal_new("m_next_msg", menu, gobject.SIGNAL_RUN_LAST,gobject.TYPE_NONE, ())
