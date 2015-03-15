#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

import time
import tool
import message

"""--------------------------------------------------------------------------------------------"""
"""------------------------------ feed - The Class which holds the Channel / Feed -------------"""
"""--------------------------------------------------------------------------------------------"""				
### class for a news feed -- The most importend contents are a list of Messages (self.msg),
### the self.ticker string as a definite key to this feed and the source, which is directly
### connected with the feed
class feed:
	def __init__(self, myOptions, source):
		self.__Options = myOptions
		self.__source = source
		
		## use own Ticker only as label...
		self.ticker = self.__source.ticker 
		
		### additional data-fields with basic information
		self.title = None
		self.link = None
		self.desc = None
		
		# stores the messages
		self.msg = []			
		
		### additional fields
		self.type = None		# recognized feed-type
		self.feed_nr = None		# number in parent news feed-list
		self.__add_pos = 0		# pos to add next msg
		self.__cache_count = 0		# max number of msg to cache
		self.__tmp_cache_count = 0
	
	
	
	### some methods, to simply get the fields directly connected to this feed by
	### getting it from the connected source
	def get_active(self): return self.__source.get_active()
	def get_ticker(self): return self.__source.get_ticker()
	def get_icon(self): return self.__source.get_icon()
	def get_iconcache(self): return self.__source.get_iconcache()
	def get_iconset(self): return self.__source.get_iconset()
	def get_shownews(self): return self.__source.get_shownews()
	def get_news_age_by_date(self): return self.__source.get_news_age_by_date()
	def get_provides_date_info(self): return self.__source.get_provides_date_info()

	### stat returns some Information about the feed, like number of messages at all
	### and number of active messages. Usually called by parent news_ class method stat
	def stat(self, stat):
		stat['all_msg_count'] += len(self.msg)
		if self.get_active() == 1:
			stat['act_feed_count'] += 1
			stat['act_msg_count'] += len(self.msg)
			for i in range(0, len(self.msg)-1):
				if i >= self.get_shownews(): continue	
				if self.msg_is_new(self.msg[i]): stat['new_msg_count'] += 1
		return stat

	
	
	
	### say if message is in feed (here same title and same link)
	def msg_in_feed(self, msg):
		for msg_old in self.msg:
			if msg.title == msg_old.title and \
				msg.link == msg_old.link: return True
		return False
	
	### check, if message is new in terms of user wishes
	def msg_is_new(self, msg):
		# check if message was read in browser
		if msg.read == 1: return False
		# check if msg-fetchtimestamp is to old
		if self.__Options.news_age.int_value <> 0 and \
			msg.fetchtime + self.__Options.news_age.int_value*60 < time.time():
			return False
		# check if msg-timestamp is to old
		if self.get_news_age_by_date() <> 0 and self.get_provides_date_info() == 1 and \
			msg.time + self.get_news_age_by_date() * 60 < time.time():
			return False
		# check if msg-showcount is less then max showcount
		if self.__Options.news_showcount.int_value <> 0 and \
			msg.showcount >= self.__Options.news_showcount.int_value:
			return False
		return True



	### export feed contents to xml, usually used to write cache
	def _to_xml(self, parent):
		def createNode(doc, name, data):
			node = doc.createElement(name)
			if data == None: data = ""
			node.appendChild(doc.createTextNode(data))
			return node
		doc = parent.ownerDocument
		root = doc.createElement('feed')
		parent.appendChild(root)
		root_c = doc.createElement('channel')
		root.appendChild(root_c)
		root_c.appendChild(createNode(doc, 'title', self.title))
		root_c.appendChild(createNode(doc, 'ticker', self.ticker))
		root_c.appendChild(createNode(doc, 'link', self.link))
		root_c.appendChild(createNode(doc, 'description', self.desc))
		for i in self.msg:
			i._to_xml(root)
		return doc		



	### import or update contents of feed from xml-data
	def _from_xml(self, xmldoc, type, box = None):
		
		self.type = type	# store the feed-type, mightbe sometimes useful
		
		### get channel == feed information. If xml-data structure wasnt recongnized
		### ('fallback') then use the whole structure as channel
		if self.type <> 'fallback': channel = xmldoc.getElementsByTagName("channel")[0]
		else: channel = xmldoc
		
		### search for additional information (it might have been updated)
		self.title = tool.getdata_wo_ret(channel, "title")
		self.link = tool.getdata(channel, "link")
		self.desc = tool.getdata_wo_ret(channel, "description")
		
		### search xmldoc for items to add to the feed, if it is a rss feed, items are
		### a part of the channel element
		if self.type == 'rss':	items = channel.getElementsByTagName("item")
		else:	items = xmldoc.getElementsByTagName("item")

		self.__add_pos = 0 		### reinit position to add new msgs
		
		### check all 'item' elements for new messages
		for i in items:
			if box: box.status("Checking " + self.title + " (" + str(self.__tmp_cache_count) + ")")
			### create new message and try to add it
			self.try_to_add_msg(message.message(i, self.type))
		
		### if number of msg had grown, grow also value if cached news
		if len(items) > self.__cache_count:
			self.__cache_count = len(items)
		
		### reduce number of cached messages
		while len(self.msg) > self.__cache_count:
			self.msg.pop()
		
		### check if messages now providing date-info
		self.reinit_provides_date_info()
	
	### check, if at least one message has a dc:date field (means msg.time <> 0)
	def reinit_provides_date_info(self):
		for msg in self.msg:
			if msg.time <> 0:
				self.__Options.set_provides_date_info(self.__source, 1)
				return
		self.__Options.set_provides_date_info(self.__source, 0)

	
	
	### adds message, if it is not still in feed
	def try_to_add_msg(self,msg_new):
		if self.msg_in_feed(msg_new): return
		
		### ok, add message, but where?
		if msg_new.time <> 0: # feed-msg provides dc:date info, so use it
				      # to find right position for new msg

			#search timeposition
			for index in range(0, len(self.msg)-1):
				### to compare msg-times, use time-stamp of message
				### if the old message hasnt a timestamp, use fethtime instead
				if self.msg[index].time <> 0: 	index_time = self.msg[index].time
				else: 	index_time = self.msg[index].fetchtime
				if index_time < msg_new.time:
					self.msg.insert(index, msg_new)
					if index < self.__add_pos: self.__add_pos += 1
					return
			self.msg.append(msg_new)	# not found
		else:
			# if no cd_timestamp provided, add at self.__add_pos position
			self.msg.insert(self.__add_pos, msg_new)
			self.__add_pos += 1
