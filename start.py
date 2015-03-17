#!/usr/bin/python
#########################################################
#              RETicker v. 0.4.5
# a programm to display xml-formatted rss/rdf-feeds in
# a one line display
#########################################################
# please read Help.txt for contact information

#########################################################
# This is the starter for the real Ticker-Application   #
# it checks, if it is started as an applet an proofes   #
# command line options                                  #
#########################################################

import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "rox-lib", "ROX-Lib2", "python")
)

import rox

sys.path.insert(0,os.path.join(rox.app_dir, "main_win"))
sys.path.insert(0,os.path.join(rox.app_dir, "icons"))
sys.path.insert(0,os.path.join(rox.app_dir, "extra_win"))
sys.path.insert(0,os.path.join(rox.app_dir, "news"))
sys.path.insert(0,os.path.join(rox.app_dir, "extras"))
sys.path.insert(0,os.path.join(rox.app_dir, "options"))


V = "0.4.5k"
Version = "RETicker v " + V

user_conf = ""
applet = None
verbose = 0
if len(sys.argv) > 1:
	### check if started as an Applet, then the first param is a number
	try:
		int(sys.argv[1])
		print Version
		print "[starting as a rox-applet]"
		print "If this is happening on the command-line"
		print "and you don't want this, stop giving the"
		print "program a Number as a parameter"
		applet = True
		import RETicker
		RETicker.TickerApplet(V, Version, "_applet", verbose)
	except:
	### started as standalone Program
		i = 1
		print "***  " + Version + "  ***"
		### check for comand-line options
		while i < len(sys.argv):
			if sys.argv[i] == '--config':
				if len(sys.argv) < i+2:
					print "ERROR: to few arguments (try --help)"
					sys.exit()
				else:
					user_conf = "_" + sys.argv[i+1]
					i += 2
				continue
			if sys.argv[i] == '-v' or sys.argv[i] == '--verbose':
				verbose = 1; i += 1; continue
			if sys.argv[i] == '--help':
				print "usage:  ./start.py [--config X][--verbose|-v][--help]"
				print "  --config X    start with Konfiguration X"
				print "                use any Name for X"
				print "  --verbose     be more verbose"
				print "  --help        shows this help ;)"
				print "Please report any Problems (see README.txt)"
				sys.exit()
			print "ERROR: unknown argument : " + sys.argv[i] + \
				"\ntry --help"
			sys.exit()
if not(applet):
	print "***  " + Version + "  ***"
	import RETicker
	RETicker.TickerWindow(V, Version, user_conf, verbose)

rox.mainloop()
 
