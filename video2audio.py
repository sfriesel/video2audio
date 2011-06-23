#!/usr/bin/env python

import sys, gst, inspect
import gobject; gobject.threads_init()

filetypes = [("video/quicktime,variant=iso", "mp4"),
             ("video/webm", "webm"),
             ("video/x-matroska", "mkv"),
             ("video/x-msvideo", "avi"),
             ("application/ogg", "ogg")]

def muxer_callback(muxer, pad):
	out_name = sys.argv[1]
	if out_name.endswith("." + muxer.ext):
		out_name, _, _ = out_name.rpartition(".")
		out_name += ".audio"
	out_name = "%s.%s" % (out_name, muxer.ext)
	
	sink = gst.element_factory_make("filesink")
	sink.set_property("location", out_name)
	converter.add(sink)
	muxer.link(sink)
	converter.set_state(gst.STATE_PLAYING)

def demuxer_callback(demuxer, pad):
	caps = pad.get_caps()
	if not str(caps).startswith("audio"):
		return
	
	muxer = find_mux(caps)
	assert muxer
	muxer.connect("pad-added", muxer_callback)
	converter.add(muxer)
	demuxer.link(muxer)

def find_mux(caps):
	muxers = [f for f in gst.registry_get_default().get_feature_list(gst.ElementFactory)]
	muxers = filter(lambda f: f.get_klass() == "Codec/Muxer", muxers)
	muxers = filter(lambda f: "not recommended" not in f.get_longname(), muxers)
	muxers = filter(lambda f: f.can_sink_caps(caps), muxers)

	for muxer in muxers:
		for caps_string, ext in filetypes:
			if muxer.can_src_caps(gst.caps_from_string(caps_string)):
				muxer = muxer.create()
				muxer.ext = ext
				return muxer
	return None

def find_demux(caps):
	for f in gst.registry_get_default().get_feature_list(gst.ElementFactory):
		if f.get_klass() != "Codec/Demuxer" or not f.can_sink_caps(caps):
			continue
		return f.create()
	return None

def typefind_callback(element, probability, caps):
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

