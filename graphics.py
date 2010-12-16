# Copyright 2010 Benjamin Dumke
# 
# This file is part of Unicornify
# 
# Unicornify is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Unicornify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the NU Affero General Public License
# along with Unicornify; see the file COPYING. If not, see
# <http://www.gnu.org/licenses/>.
    


# Most of the following is useless when you have access to a graphics library
# like the PIL. But since this was written for the App Engine (where you can't
# install C libraries) I needed pure Python versions of the graphics
# operations I need.

from colorsys import hls_to_rgb as hls_to_rgb_float
from functools import partial
from math import sqrt
import struct

def hls_to_rgb(h, l, s):
    rgb = hls_to_rgb_float(h / 360.0, l / 100.0, s / 100.0)
    return tuple(int(255 * v) for v in rgb)

def blend(color1, color2, factor):
    return tuple(c1 + int((c2 - c1) * factor) for c1, c2 in zip(color1, color2))

class SquareImage(object):

    RESTORE = -1

    @classmethod
    def plain(cls, size, color):
        self = object.__new__(cls)
        self._image = [[color] * size for y in xrange(size)]
        self.size = size
        self.s = size - 1
        return self
    
    def __init__(self, size, top_color, bottom_color):
        delta = [b - t for b, t in zip(bottom_color, top_color)]
        s = size - 1
        def color(y):
            return tuple(t + d * y // s for t, d in zip(top_color, delta))
        self._image = [[color(y)] * size for y in xrange(size)]
        self.size = size
        self.s = s

    def save(self):
        self._saved = [[p for p in l] for l in self._image]

    def hor_line(self, color, x0, x1, y):
        """x0 must be <= x1 """
        s = self.s
        if y < 0 or y > s or x0 > s or x1 < 0:
            return
        x0 = max(0, int(x0))
        x1 = min(s, int(x1)) + 1
        self._image[int(y+.5)][x0:x1] = [color] * (x1 - x0)

    def hor_gradient(self, color1, color2, x0, x1, y0, y1):
        s = self.s
        if y1 < 0 or y0 > s or x0 > s or x1 < 0:
            return
            
        if x0 < 0:
            color1 = blend(color1, color2, (x1 - x0) / float(-x0))
            x0 = 0
        if x1 > s:
            color2 = blend(color1, color2, (s - x0) / float(s - x0))
            x1 = s
        x0 = max(0, int(x0))
        x1 = min(s, int(x1)) + 1
        line = [blend(color1, color2, (x - x0) / float(x1 - x0)) for x in xrange(x0, x1)]
        for y in xrange(int(y0 + .5), int(y1 + 1.5)):
            self._image[y][x0:x1] = line
    
    def restore_hor_line(self, x0, x1, y):
        """x0 must be <= x1 """
        s = self.s
        if y < 0 or y > s or x0 > s or x1 < 0:
            return
        x0 = max(0, int(x0))
        x1 = min(s, int(x1)) + 1
        yr = int(y+.5)
        self._image[yr][x0:x1] = self._saved[yr][x0:x1]

    def circle(self, center, radius, color):
        # adapted from http://en.wikipedia.org/wiki/Midpoint_circle_algorithm
        
        radius = int(radius)
        x0, y0 = center
        
        if x0 < -radius or y0 < -radius or x0 - radius > self.size or y0 - radius > self.size:
            return
        
        f = 1 - radius
        ddF_x = 1
        ddF_y = -2 * radius
        x = 0
        y = radius

        if color == self.RESTORE:
            hl = self.restore_hor_line    
        else:
            hl = partial(self.hor_line, color)
        
        hl(x0 - radius, x0 + radius, y0)
        
        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x

            hl(x0 - x, x0 + x, y0 + y)
            hl(x0 - x, x0 + x, y0 - y)
            hl(x0 - y, x0 + y, y0 + x)
            hl(x0 - y, x0 + y, y0 - x)

    def connect_circles(self, center1, radius1, color1, center2, radius2, color2):
        # see Bone.draw() in core.py for some notes on performance of this algorithm
        center1 = map(int, center1)
        center2 = map(int, center2)
        radius1, radius2 = int(radius1), int(radius2)
        xmin = int(max(0, min(center1[0] - radius1, center2[0] - radius2)))
        xmax = int(min(self.s, max(center1[0] + radius1, center2[0] + radius2)))
        ymin = int(max(0, min(center1[1] - radius1, center2[1] - radius2)))
        ymax = int(min(self.s, max(center1[1] + radius1, center2[1] + radius2)))
        
        col = [tuple(int(v[0] + fac * (v[1] - v[0]) / 255) for v in zip(color1, color2)) for fac in xrange(256)]
        
        d = radius2 - radius1
        vx = center2[0] - center1[0]
        vy = center2[1] - center1[1]
        a = float(vx**2 + vy**2 - d**2)
        r1d = radius1 * d
        r1s = radius1 ** 2
        c2x = center2[0]
        d2xs = dict((x, (x - c2x)**2) for x in xrange(xmin, xmax + 1))
        
        for y in xrange(ymin, ymax + 1):
            line = self._image[y]
            dy = y - center1[1]
            b_ = vy * dy + r1d
            c_ = dy**2 - r1s
            r2sdy2s = radius2**2 - (y - center2[1])**2
            for x in xrange(xmin, xmax + 1):
                dx = x - center1[0]
                
                b = -2 *(vx * dx + b_)
                c = dx**2 + c_
                
                if d2xs[x] < r2sdy2s:
                    l = 1
                elif a == 0:
                    if b == 0:
                        continue
                    l = -c / float(b)
                else:
                    p = b / a
                    q = c / a
                    disc = p**2 / 4 - q
                    if disc < 0:
                        continue
                    sqrtdisc = sqrt(disc)
                    l = -p / 2 + sqrtdisc
                    if l > 1:
                        l = -p / 2 - sqrtdisc
                if l > 1:
                    continue
                    if (x - center2[0])**2 + (y - center2[1])**2 > radius2**2:
                        continue
                    else:
                        l = 1
                if l < 0:
                    if c > 0:
                        continue
                    else:
                        l = 0
                line[x] = col[int(l * 255)]

    def top_half_circle(self, center, radius, color):
        # This is just copy & paste from circle() with
        # two lines removed. I've heard this is called "code reuse".        
        
        radius = int(radius)
        x0, y0 = center
        if x0 < -radius or y0 < -radius or x0 - radius > self.size or y0 - radius > self.size:
            return
        f = 1 - radius
        ddF_x = 1
        ddF_y = -2 * radius
        x = 0
        y = radius
        if color == self.RESTORE:
            hl = self.restore_hor_line    
        else:
            hl = partial(self.hor_line, color)
        hl(x0 - radius, x0 + radius, y0)
        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x
            hl(x0 - x, x0 + x, y0 - y)
            hl(x0 - y, x0 + y, y0 - x)

    def to_bmp(self):
        padding = 4 - (3 * self.size) % 4
        if padding == 4:
            padding = 0
        bitmap_data_size = (3 * self.size + padding) * self.size
        total_size = bitmap_data_size + 54
        
        scanline_struct = struct.Struct("%dB%dx" % (3 * self.size, padding))
        def data_iterator():
            yield struct.pack("<2s6I2H6I", "BM", total_size, 0, 54, 40, self.size, self.size, 1, 24, 0, bitmap_data_size, 2835, 2835, 0, 0)
            for line in reversed(self._image):
                yield scanline_struct.pack(*(val for col in line for val in reversed(col)))
        return "".join(data_iterator())
