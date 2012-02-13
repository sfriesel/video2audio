#!/usr/bin/env python

import sys, gst, inspect
import gobject; gobject.threads_init()

def muxer_callback(muxer, pad):
	print "muxer_callback: muxer created pad", pad
	out_name = sys.argv[1]
	if out_name.endswith(".m4a"):
		out_name, _, _ = out_name.rpartition(".")
		out_name += ".audio"
	elif out_name.endswith(".flv") or out_name.endswith(".mp4"):
		out_name, _, _ = out_name.rpartition(".")
	out_name = "%s.%s" % (out_name, "m4a")
	
	sink = gst.element_factory_make("filesink")
	sink.set_property("location", out_name)
	converter.add(sink)
	muxer.link(sink)
	converter.set_state(gst.STATE_PLAYING)

def demuxer_callback(demuxer, pad):
	print "demuxer_callback: demuxer created pad", pad
	caps = pad.get_caps()
	if not str(caps).startswith("audio"):
		return
	print "demuxer_callback: using pad", pad, "as audio"
	muxer = find_mux(caps)
	assert muxer
	muxer.connect("pad-added", muxer_callback)
	converter.add(muxer)
	demuxer.link(muxer)

def find_mux(caps):
	return gst.element_factory_make("mp4mux")

def find_demux(caps):
	for f in gst.registry_get_default().get_feature_list(gst.ElementFactory):
		if f.get_klass() != "Codec/Demuxer" or not f.can_sink_caps(caps):
			continue
		return f.create()
	return None

def typefind_callback(element, probability, caps):
	print "typefind_callback found type", caps, "with probability", probability
	demuxer = find_demux(caps)
	if not demuxer:
		raise Exception("unknown input type")
	demuxer.connect("pad-added", demuxer_callback)
	
	converter.add(demuxer)
	typefind.link(demuxer)

converter = gst.Pipeline("converter")
source = gst.element_factory_make("filesrc")
source.set_property("location", sys.argv[1])
typefind = gst.element_factory_make("typefind")
typefind.connect("have-type", typefind_callback)
converter.add(source, typefind)
source.link(typefind)

converter.set_state(gst.STATE_PAUSED)
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

