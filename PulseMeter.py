#!/usr/bin/env python

# PulseMeter.py
#
# Displays graphically the pulse curve and the estimated pulse rate.
#
# TODO:
#  . improve peak detection
#  . improve pulse rate calculation
#
# Author: Christophe Augier <christophe.augier@gmail.com>
#
# This file is licensed under a Creative Commons Attribution 3.0 Unported
# License.
#

import pygtk
pygtk.require('2.0')
import gtk, gobject
import sys, serial

class PulseMeter:
    def destroy(self, widget, data=None):
        # Quit PulseMeter
        gtk.main_quit()

    def draw_text(self, x, y):
        self.pangolayout.set_text("Point")
        self.graph.window.draw_layout(self.gc, x+5, y+50, self.pangolayout)

    def high_pass_filter(self, x):
        """ High pass filter computed at:
            http://www-users.cs.york.ac.uk/~fisher/mkfilter/trad.html

            with filter order = 1, Butterworth Highpass,
                 sample rate  = 20,
                 corner frequency = 0.1 Hz
        """
        self.y_1 = self.y_0
        self.x_1 = self.x_0
        self.x_0 = x
        self.y_0 = self.x_0 - self.x_1 + (0.9690674172 * self.y_1)

    def band_pass_filter(self, x):
        """ Band pass filter computed at:
            http://www-users.cs.york.ac.uk/~fisher/mkfilter/trad.html

            with filter order = 1, Butterworth Bandpass,
                 sample rate  = 20,
                 corner frequency 1 = 0.1 Hz
                 corner frequency 2 = 4 Hz ( < 240bpm)
        """
        self.y_2 = self.y_1
        self.y_1 = self.y_0
        self.x_2 = self.x_1
        self.x_1 = self.x_0
        self.x_0 = x

        self.y_0 = self.x_0 - self.x_2 + (-0.1745279389 * self.y_2) + (1.1480196762 * self.y_1)


    def graph_expose_cb(self, widget, event):
        self.style = self.graph.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        gc_in = self.style.fg_gc[gtk.STATE_INSENSITIVE]
        self.pangolayout.set_text("%d bpm" % int(self.pulse_rate))
        self.graph.window.draw_layout(self.gc, 10, 10, self.pangolayout)

        _, _, w, h = self.graph.get_allocation()
        length = len(self.data)
        samples = w / 2
        if length > samples:
            start = length - samples
        else:
            start = 0

        x = last_d = 0
        sec = 0
        for i in range(start, length):
            d = h - 50 - int(self.data[i])
            self.graph.window.draw_line(self.gc, x, last_d, x+1, d)
            sec = sec + 1
            if sec == 20:
                self.graph.window.draw_line(gc_in, x, 0, x, h)
                sec = 0
            x = x + 2
            last_d = d

        return True

    def add_data(self, d):
        last = self.data[-1]
        self.data.append(d)

        cur_t = len(self.data)

        # Compute pulse rate by finding highest peaks
        # in a 10 samples window
        #
        if self.peak and (cur_t - self.peak[0]) >= 10:
            pulse_rate = 60 * (self.peak[0] - self.peaks[-1][0]) / 20.0
            self.pulse_rate = (self.pulse_rate + pulse_rate) / 2
            #print "pulse: %f" % pulse_rate
            self.peaks.append(self.peak)
            self.peak = None

        deriv = d - last
        peak  = None
        if (self.last_deriv > 0 and deriv <= 0) or (
            self.last_deriv >= 0 and deriv < 0):
            peak = (cur_t, d)
        self.last_deriv = deriv

        if peak:
            if self.peak and (cur_t - self.peak[0]) < 10 and d > self.peak[1] :
                self.peak = peak
            elif not self.peak:
                self.peak = peak

    def read_serial(self):
        buf = self.serial.read(self.serial.inWaiting())
        lines = buf.split('\n')
        for l in lines:
            if l != '':
                d = float(l)
                # You can use either the band or high pass filter
                #self.band_pass_filter(d)
                self.high_pass_filter(d)
                self.add_data(int(self.y_0))
        self.graph.queue_draw()
        return True

    def __init__(self, ser):
        import math
        self.serial = ser
        self.data   = [1024]
        self.last_deriv = 0
        self.pulse_rate = 60.0
        self.peak  = (0, -1024)
        self.peaks = [self.peak]
        self.x_2 = self.x_1 = self.x_0 = 0.0
        self.y_2 = self.y_1 = self.y_0 = 0.0

        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("PulseMeter")
        self.window.set_size_request(400,300)
        self.window.connect("destroy", self.destroy)

        self.graph = gtk.DrawingArea()
        self.pangolayout = self.graph.create_pango_layout("")
        self.graph.connect("expose-event", self.graph_expose_cb)
        self.window.add(self.graph)

        # Set a timer to read regularly what was sent on the Serial line
        gobject.timeout_add(240, self.read_serial) # call 4 times every second
    
        self.graph.show()
        self.window.show()

    def main(self):
        gtk.main()

if __name__ == "__main__":
    import optparse

    parser = optparse.OptionParser(
        usage = "%prog [port [baudrate]]",
        description = "A simple program displaying a graph of the pulse values read on a serial port."
    )

    parser.add_option("-p", "--port",
        dest = "port",
        help = "port, a number (default 0) or a device name",
        default = "/dev/ttyACM0"
    )

    parser.add_option("-b", "--baud",
        dest = "baudrate",
        action = "store",
        type = 'int',
        help = "set baud rate, default: %default",
        default = 115200
    )

    (options, args) = parser.parse_args()

    port = options.port
    baudrate = options.baudrate

    if args:
        if options.port is not None:
            parser.error("no arguments are allowed, options only when --port is given")
        port = args.pop(0)
        if args:
            try:
                baudrate = int(args[0])
            except ValueError:
                parser.error("baud rate must be a number, not %r" % args[0])
            args.pop(0)
        if args:
            parser.error("too many arguments")
    else:
        if port is None: port = 0

    # connect to serial port
    ser = serial.Serial()
    ser.port     = port
    ser.baudrate = baudrate
    ser.timeout  = 1

    try:
        ser.open()
    except serial.SerialException, e:
        sys.stderr.write("Could not open serial port %s: %s\n" % (ser.portstr, e))
        sys.exit(1)

    pm = PulseMeter(ser)
    pm.main()

