#!/usr/bin/env python

from subprocess import *
from sys import argv

def main():
#	call(["/home/sfriesel/Projekte/youtube-dl.py", "-F", argv[1]])

	for fmt in ["34", "35", "83", "84", "13", "17"]:
		print "trying format", fmt
		if 0 == call(["/home/sfriesel/Projekte/youtube-dl.py", "-f", fmt, argv[1]]):
			if 0 == call(["/home/sfriesel/Projekte/video2audio/video2mp4.py", argv[1] + ".flv"]):
				return 0
			if 0 == call(["/home/sfriesel/Projekte/video2audio/video2mp4.py", argv[1] + ".mp4"]):
				return 0
			return 1
	return 1

if __name__ == "__main__":
	main()
