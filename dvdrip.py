#!/usr/bin/env python

import sys, gst, inspect
import gobject; gobject.threads_init()

#filetypes = [("video/quicktime,variant=iso", "m4a"),
#             ("video/x-matroska", "mka"),
#             ("video/mpeg,mpegversion=2", "mp3"),
#             ("application/ogg", "ogg"),
#             ("video/x-msvideo", "avi")]

#def muxer_callback(muxer, pad):
#	print "muxer_callback: muxer created pad", pad
#	out_name = sys.argv[1]
#	if out_name.endswith("." + muxer.ext):
#		out_name, _, _ = out_name.rpartition(".")
#		out_name += ".audio"
#	out_name = "%s.%s" % (out_name, muxer.ext)
#	
#	sink = gst.element_factory_make("filesink")
#	sink.set_property("location", out_name)
#	converter.add(sink)
#	muxer.link(sink)
#	converter.set_state(gst.STATE_PLAYING)

mux = gst.element_factory_make("mpegtsmux")
demux = gst.element_factory_make("dvddemux")
converter = gst.Pipeline("converter")

#audiocounter = 0

def find_mux(caps):
	print caps.to_string()
	muxers = [f for f in gst.registry_get_default().get_feature_list(gst.ElementFactory)]
	#muxers = filter(lambda f: f.get_klass() == "Codec/Muxer", muxers)
	#muxers = filter(lambda f: "not recommended" not in f.get_longname(), muxers)
	muxers = filter(lambda f: f.can_sink_caps(caps), muxers)
	
	for m in muxers:
		print m
	
	return muxers[-1].create()

def demuxer_callback(demuxer, pad):
	#global audiocounter
	global mux
	global demux
	#global converter
	#print "demuxer_callback: demuxer created pad", pad
	caps = pad.get_caps()
	if str(caps).startswith("audio"):
		print "this is a audio pad"
		#sink_name = "audio_%02d" % (audiocounter)
		#print "the caps are:", str(caps), "and", str(mux.get_pad(sink_name).get_caps())
		#con = gst.element_factory_make("audioconvert")
		#demux.link_pads(str(pad), mux, sink_name)
		#pad.link(mux.get_pad(sink_name))
		queue = gst.element_factory_make("queue")
		converter.add(queue)
		demux.link(queue)
		queue.link(mux)
		#audiocounter += 1
		
	elif str(caps).startswith("video/mpeg"):
		#print str(caps)
		print "this is a video pad"
		muxer = find_mux(caps)
		#converter.add(muxer)
		demux.link(mux)
		#demux.link_filtered(mux, gst.caps_from_string("video/mpeg, mpegversion=(int)2, systemstream=(boolean)false,width=720,height=576,framerate=25"))
	else:
		print "this gets ignored"
	converter.set_state(gst.STATE_PLAYING)

source = gst.element_factory_make("dvdreadsrc")
source.set_property("title", 3)

demux.connect("pad-added", demuxer_callback)
converter.add(source, demux, mux)
source.link(demux)

sink = gst.element_factory_make("filesink")
sink.set_property("location", "test.mp4")
converter.add(sink)
q = gst.element_factory_make("queue")
converter.add(q)
mux.link(q)
q.link(sink)
converter.set_state(gst.STATE_PLAYING)

mainloop = gobject.MainLoop()

def on_message(bus, message):
	t = message.type
	if t == gst.MESSAGE_EOS:
		converter.set_state(gst.STATE_NULL)
		mainloop.quit()
	elif t == gst.MESSAGE_ERROR:
		err, debug = message.parse_error()
		print "Error: %s" % err, debug
		converter.set_state(gst.STATE_NULL)
		mainloop.quit()
	return True

bus = converter.get_bus()
bus.add_watch(on_message)

mainloop.run()

