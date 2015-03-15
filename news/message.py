#!/usr/bin/env python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

import time
import tool

EMPTY_DESC = "(no further Information)" ### This String indicates an empty
					### description field in message

"""--------------------------------------------------------------------------------------------"""
"""------------------------------ message - The Class which holds the Message -----------------"""
"""--------------------------------------------------------------------------------------------"""
### class for a news message and all information related to one, see __init__ for contents
class message:
	def __init__(self, xml_source = None, type = 'fallback'):
		self.title = ""
		self.link  = ""
		self.desc  = ""
		self.time  = 0			# time wich found in field dc:date
		self.fetchtime = 0		# time when message was fetched
		self.showcount = 0		# how often message was shown in ticker
		self.read = 0			# if 1, message was opened in browser
		
		# usually an empty message is useless
		if xml_source: self._from_xml(xml_source, type)
	
	### import contents of message from xml; usually called by __init__
	def _from_xml(self, xml_source, type):
		self.title = tool.getdata(xml_source, "title")
		self.link = tool.getdata(xml_source, "link")
		self.desc = tool.getdata_wo_ret(xml_source, "description")
		
		# if there is no title for the message, try to get some from description
		if self.title == "": self.title = tool.makeshorter(self.desc, 50)
		if self.title == "": self.title = tool.makeshorter(self.link, 50)
		# if still no title - forget the whole thing
		
		if self.desc == "": self.desc = EMPTY_DESC
		
		self.fetchtime = tool.getfloatdata(xml_source, "fetchtime")
		if self.fetchtime <> 0:  	### only happens if cache-data is read
			self.time = tool.getfloatdata(xml_source, "time")
		else:
			self.time = tool.gettimedata(xml_source, "dc:date")
			self.fetchtime = time.time()
		
		self.showcount = tool.getintdata(xml_source, "showcount")
		self.read =  tool.getintdata(xml_source, "read")
		
	### export contents of message to xml	
	def _to_xml(self, parent):
		def createNode(doc, name, data):
			node = doc.createElement(name)
			node.appendChild(doc.createTextNode(data))
			return node
		doc = parent.ownerDocument
		root = doc.createElement('item')
		parent.appendChild(root)
		root.appendChild(createNode(doc, 'title', self.title))
		root.appendChild(createNode(doc, 'link', self.link))
		root.appendChild(createNode(doc, 'description', self.desc))
		root.appendChild(createNode(doc, 'time', str(self.time)))
		root.appendChild(createNode(doc, 'fetchtime', str(self.fetchtime)))
		root.appendChild(createNode(doc, 'showcount', str(self.showcount)))
		root.appendChild(createNode(doc, 'read', str(self.read)))
		return doc
	
	### print Message contents xml-formatted
	def __str__(self):
		doc = Document()
		root = doc.createElement('message'); doc.appendChild(root)
		self._to_xml(root)
		return doc.toxml()
