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
import gc
import gobject

"""--------------------------------------------------------------------------------------------"""
"""------ some tools to make programming easyer -----------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""				


"""--------------------------------------------------------------------------------------------"""
"""------ a class to remember all set connections, to remove them later -----------------------"""
"""--------------------------------------------------------------------------------------------"""				
### The Connection class is used to make signal connections between other clases. Cause a
### connection from a signal of classA to a function of classB keeps classB alive till this
### connection is removed, this class stores all set connection and gives you the chance to
### remove them later
class Connections:
	def __init__(self):
		self.__connections = []        # holds all connections
	
	### set a connection
	def connect(self, source, signal, callback):
		con = source.connect(signal, callback)
		self.__connections.append({'source' : source, 'signal' : signal, 'con' : con})
	
	### set a connection and remove any other connection from same source to signal made before
	def connect_new(self, source, signal, callback):
		self.disconnect(source, signal)
		self.connect(source, signal, callback)
		
	### search and remove all connections from signal of source to anything
	def disconnect(self, source, signal):
		i = 0
		while i < len(self.__connections):
			con = self.__connections[i]
			if con['source'] == source and con['signal'] == signal:
				con['source'].disconnect(con['con'])
				self.__connections.pop(i)
			else: i += 1

	### remove all connection, should be called before removing any other reference to the instance
	def disconnect_all(self, dummy = None):
		for con in self.__connections: con['source'].disconnect(con['con'])
		self.__connections = []



"""--------------------------------------------------------------------------------------------"""
"""------ a class to call a mehtod after the given value keeps stabe for a while --------------"""
"""--------------------------------------------------------------------------------------------"""				
### This class is to wait a small amount of time before calling a function. The waiting-timer
### will be resetted without calling the function if a given value has changed since last call
### ok, a usage: The user types a string in a box, the programm should react on the new string.
### With this class you can wait till typing is done (string dosnt change any more for a amount
### of time) and then call the function only once.
class DelayCall:
	def __init__(self, time_to_wait, function_to_call):
		self.time_to_wait = time_to_wait
		self.function_to_call = function_to_call
		self.value = None
		self.timeout = None
	
	### to change or remove the timeout (remove = set to 0)
	def set_time(self, time):
		self.time_to_wait = time
		if self.timeout:
			g.timeout_remove(self.timeout)
			self.timeout = g.timeout_add(long(self.time_to_wait * 1000), self.fire)
	
	### sets the value, if it keeps stable for a while, callback is fired
	def set_value(self, value = None):
		self.value = value
		if self.timeout: g.timeout_remove(self.timeout)
		if self.time_to_wait <> 0:
			self.timeout = g.timeout_add(long(self.time_to_wait * 1000), self.fire)
		else: self.timeout = None; self.fire()
	
	### calls function an deletes value
	def fire(self):
		self.function_to_call(self.value)
		self.value = None



"""--------------------------------------------------------------------------------------------"""
"""------ a class to show a progressbar -------------------------------------------------------"""
"""--------------------------------------------------------------------------------------------"""				
class Win_ProgBar(g.Window):
	def __init__(self, Label = None):
		g.Window.__init__(self)
		self.set_decorated(g.FALSE)
		self.prog = g.ProgressBar()
		self.prog.set_size_request(100,12)
		self.prog.set_pulse_step(0.2)
		if Label: self.prog.set_text(Label)
		self.add(self.prog)
		### find the right position for the bar
		x, y, mods = g.gdk.get_default_root_window().get_pointer()
		if x - 50 > 0: x = x - 50
		else: x = 0
		if y - 10 > 0: y = y - 10
		else: y = y + 10
		self.move(x, y)
		self.show_all()
	
	### start the progressbar to move
	def start_pulse(self): tasks.Task(self.pulse_loop())
	def pulse_loop(self): 
		while(self.prog):
			self.prog.pulse()
			yield tasks.TimeoutBlocker(0.1)
	
	### remove the progressbar
	def rem(self): self.prog = None; self.destroy()


"""--------------------------------------------------------------------------------------------"""
### removes tags and/or entities from a given string and returns a new string
import re
def unxml(string):
	string = unxml_wo_tags(string)
	tag=re.compile('<.*?>')
	(string,null)=tag.subn("",string,0)
	return string	
def unxml_wo_tags(string):
	lt=re.compile('&lt;')
	gt=re.compile('&gt;')
	amp=re.compile('&amp;')
	auml=re.compile('&auml;|&#228;')
	Auml=re.compile('&Auml;')
	ouml=re.compile('&ouml;|&#246;')
	Ouml=re.compile('&Ouml;')
	uuml=re.compile('&uuml;|&#252;')
	Uuml=re.compile('&Uuml;')
	szlig=re.compile('&szlig;|&#223;')
	quot=re.compile('&quot;')
	apos=re.compile('&apos;')
	#~ (string,null)=amp.subn("&",string,0)
	(string,null)=auml.subn(u'\xE4',string,0)
	(string,null)=Auml.subn(u'\xC4',string,0)
	(string,null)=ouml.subn(u'\xF6',string,0)
	(string,null)=Ouml.subn(u'\xD5',string,0)
	(string,null)=Uuml.subn(u'\xDC',string,0)
	(string,null)=szlig.subn(u'\xDF',string,0)
	(string,null)=uuml.subn(u'\xFC',string,0)
	(string,null)=quot.subn('"',string,0)
	(string,null)=apos.subn("'",string,0)
	(string,null)=lt.subn("<",string,0)
	(string,null)=gt.subn(">",string,0)
	return string

"""--------------------------------------------------------------------------------------------"""
### convert a dc:date time information to the internal format
import time
def conv_iso_time(date):
	if date[-5] == "+" or date[-5] == "-": date = date[:-5]
	if date[-6] == "+" or date[-6] == "-": date = date[:-6]
	try:	return time.mktime(time.strptime(date, "%Y-%m-%dT%H:%M:%S"))
	except ValueError:  ### time format migt be broken
		return 0
	



"""--------------------------------------------------------------------------------------------"""
### the following functions get the data out of an xml-field
def getdata(channel,name): # return as a string
	c_name_s=channel.getElementsByTagName(name)
	c_name = ""
	if c_name_s:
		for t in c_name_s[0].childNodes:
			if t: c_name+=t.data
	return c_name

def getdata_wo_ret(channel,name): # return as String without return
	c_name = getdata(channel,name)
	pos = c_name.find('\n')
	while pos <> -1:
		if pos <> 0: tmp = c_name[:pos] + " "
		else: tmp = ""
		tmp += c_name[pos+1:]
		c_name = tmp
		pos = c_name.find('\n')
	return c_name

def getintdata(channel,name): # return as int
	c_name = getdata(channel,name)
	try: return int(c_name)
	except: return 0

def getfloatdata(channel,name): # return as float
	c_name = getdata(channel,name)
	try: return float(c_name)
	except: return 0

def gettimedata(channel,name): # return as time
	c_name = getdata(channel,name)
	if c_name == "": return 0
	else: return float(conv_iso_time(c_name))

"""--------------------------------------------------------------------------------------------"""
### set prelight colors. Contrast between background and foreground will set higher
def back_color_prelight(Options):
	text_obj, back_obj = get_prelight_colors(Options); return back_obj

def text_color_prelight(Options):
	text_obj, back_obj = get_prelight_colors(Options); return text_obj

def get_prelight_colors(Options):
	back_obj = g.gdk.color_parse(Options.back_color.value)
	text_obj = g.gdk.color_parse(Options.text_color.value)
	if Options.transparent.int_value == 1:
		if text_obj.red + text_obj.green + text_obj.blue > 65535/2:
			text_obj = change_color(text_obj, 0.3)
		else: text_obj = change_color(text_obj, -0.3)
	if text_obj.red + text_obj.green + text_obj.blue \
		> back_obj.red + back_obj.green + back_obj.blue:
		# foreground brighter than background
		text_obj = change_color(text_obj, 0.3)
		back_obj = change_color(back_obj, -0.3)
	else:
		text_obj = change_color(text_obj, -0.3)
		back_obj = change_color(back_obj, 0.3)
	return text_obj, back_obj

def change_color(obj, value):	
	obj.red = set_color_part(obj.red, value)
	obj.green = set_color_part(obj.green, value)
	obj.blue = set_color_part(obj.blue, value)
	obj.pixel = 0
	return obj

def set_color_part(color_part, value):
	tmp = int(color_part * (1 + value))
	if tmp > 65535: return 65535
	if tmp < 0: return 0 # this shouldnt happen ;)
	return tmp



"""--------------------------------------------------------------------------------------------"""
### returns a cache_filename. It is done by removing the protocol (if there) and then replacing
### all following / by _
def cache_filename(cache, url):
	pos = url.find("http://")
	if pos <> -1: url = url[pos+7:]
	while 1:
		pos = url.find("/")
		if pos <> -1:
			url = url[:pos] + "_" + url[pos+1:]
		else: break
	
	return cache + "/" + url.encode('ascii','ignore')

"""--------------------------------------------------------------------------------------------"""
### a function to limit strings to a special length. looks for a space to cut the line and adds ...
def makeshorter(text, length):
	new_text = text[:length]
	last_space = new_text[10:].find(" ")
	if last_space <> 0: new_text = new_text[:len(new_text)-10+last_space]
	return new_text + "..."

"""--------------------------------------------------------------------------------------------"""
child_task = None

### a special urlretrieve version which calls gethttp as a own command to stop blocking
def urlretrieve(url, file):
	###### special approach to stop blocking in urllib
	import options
	#~ file.encode('ascii', 'ignore')
	if os.path.isfile(file): os.remove(file)
	exec_file = os.path.join(rox.app_dir, 'extras/gethttp.py')
	command = ['python', exec_file, url.encode('utf8', 'ignore'), file, options.use_proxy.value, options.proxy.value]
	import task
	t = task.Task(command); t.Run()
	global child_task
	child_task = t
	return t
	####### feed copyd without blocking


def kill_child_task():
	global child_task
	t = child_task
	### get rid of the started child-prozess
	if t.Status() == None: t.Kill(); t.Wait()
	if t.Status() == None: import signal; t.Kill(signal.SIGKILL); t.Wait()
	


"""--------------------------------------------------------------------------------------------"""
### This function opens a webpage in your favorite browser
def openPage(link, Options):
	pid = None
	if Options.br_options.value <> "":
		pid = os.spawnlp(os.P_NOWAIT,Options.browser.value,\
			Options.browser.value,Options.br_options.value,link)
	else: pid = os.spawnlp(os.P_NOWAIT,Options.browser.value,Options.browser.value,link)
	tasks.Task(wait_till_done(pid))
	
def wait_till_done(pid):
	pid_done = 0
	######## check every 5 seconds if the child-process is finished
	while pid_done <> pid:
		yield tasks.TimeoutBlocker(5)
		pid_done,status = os.waitpid(pid,os.WNOHANG)
	