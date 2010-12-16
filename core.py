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
    
from math import sin, cos, pi, sqrt
import functools
from graphics import hls_to_rgb

class Data(object):
    def __getattribute__(self, attr):
        try:
            return super(Data, self).__getattribute__(attr)
        except AttributeError:
            if attr in self._data:
                return self._data[attr]
            elif attr.endswith("_col"):
                part = attr[:-4]
                func = lambda lightness: hls_to_rgb(self._data[part + "_hue"], lightness, self._data[part + "_sat"])
                self._data[attr] = func
                return func
            else:
                raise KeyError("Unknown parameter %s" % attr)
        
    def __setattr__(self, attr, value):
        if attr == "_data":
            super(Data, self).__setattr__(attr, value)
        elif attr in self._data:
            self._data[attr] = value
        else:
            raise KeyError("Unknown parameter %s" % attr)


class Rect(object):
    def __init__(self, left, top, right, bottom):
        self.coords = left, top, right, bottom
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        
    def __add__(self, other):
        if other is None:
            return self
        zipped = zip(self.coords, other.coords)
        lt = map(min, zipped[:2])
        rb = map(max, zipped[2:])
        return Rect(*(lt + rb))

    def __radd__(self, other):
        return self + other
        
    def intersects(self, other):
        hori = other.left <= self.left <= other.right or other.left <= self.right <= other.right or (self.left <= other.left and self.right >= other.right)
        vert = other.top <= self.top <= other.bottom or other.top <= self.bottom <= other.bottom or (self.top <= other.top and self.bottom >= other.bottom)
        return hori and vert

class WorldView(object):
    """Note that projecting does not depend on shift, hence unlike
       the other parameters, shift may be changed without re-projecting."""
    def __init__(self, angle_y, angle_x, rotation_center, shift):
        self.angle_y = angle_y
        self.angle_x = angle_x
        self.rotation_center = rotation_center
        self.shift = shift

class Ball(object):
    def __init__(self, center, radius, color):
        self.center = tuple(map(float, center))
        self.radius = float(radius)
        self.color = color
        
        self.projection = None

    def project(self, worldview):
        rad_y = worldview.angle_y * pi / 180
        rad_x = worldview.angle_x * pi / 180
        x1, y1, z1 = (self.center[i] - worldview.rotation_center[i] for i in xrange(3))
        x2 = x1 * cos(rad_y) - z1 * sin(rad_y)
        y2 = y1
        z2 = x1 * sin(rad_y) + z1 * cos(rad_y)
        x3 = x2
        y3 = y2 * cos(rad_x) - z2 * sin(rad_x)
        z3 = y2 * sin(rad_x) + z2 * cos(rad_x)
        self.projection = tuple(c[0] + c[1] for c in zip((x3, y3, z3), worldview.rotation_center))

    def rotate(self, angle, other, axis = 2):
        """Rotate this ball around the ball "other", leaving the "axis" coordinate
           as is. (default z, i.e. rotation is in the x-y-plane)"""
        rad = angle * pi / 180
        swap = [(1, 2, 0), (0, 2, 1), (0, 1, 2)][axis]
        reverse = [(2, 0, 1), (0, 2, 1), (0, 1, 2)][axis]
        # the letters are the correct ones for the default case axis = 2
        x1, y1, z1 = (self.center[i] - other.center[i] for i in swap)
        x2 = x1 * cos(rad) - y1 * sin(rad)
        y2 = x1 * sin(rad) + y1 * cos(rad)
        z2 = z1
        self.center = tuple((x2, y2, z2)[reverse[i]] + other.center[i] for i in xrange(3))
           
    def set_distance(self, distance, other):
        """Move this ball to have the given distance to "other" while not changing the
           direction. This is the distance of the ball centers."""
        span = tuple(c[0] - c[1] for c in zip(self.center, other.center))
        stretch = distance / sqrt(sum(c * c for c in span))
        self.center = tuple(c[0] + stretch * c[1] for c in zip(other.center, span))
        
    def set_gap(self, gap, other):
        self.set_distance(gap + self.radius + other.radius, other)
        
    def move_to_sphere(self, other):
        self.set_distance(other.radius, other)
            
    def twoD(self):
        return self.projection[:2]            
            
    def draw(self, image, worldview):
        x, y = map(sum, zip(worldview.shift, self.twoD()))
        r = self.radius
        image.circle((x, y), r, self.color)
        
    def __sub__(self, other):
        tup1 = self.center
        if isinstance(other, Ball):
            tup2 = other.center
        else:
            tup2 = other
        return tuple(c[0] - c[1] for c in zip(tup1, tup2))
        
    def bounding(self):
        x, y, r = self.twoD() + (self.radius, )
        return Rect(x - r, y - r, x + r, y + r)
        
    def balls(self):
        yield self
        
    def sort(self, worldview):
        return
        
def identity(x):
    return x

class Bone(object):
    def __init__(self, ball1, ball2):
        self._balls = [ball1, ball2]
        
    def draw(self, image, worldview, xfunc = identity, yfunc = identity):
        """xfunc and / or yfunc should map [0,1] -> [0,1] if the parameter "step"
           should not be applied linearly to the coordinates. Note that these x and
           y are screen, i.e. 2D, coordinates. This is currently used to make the hair
           wavy."""

        calc = lambda c1, c2, factor: c1 + (c2 - c1) * factor
        x1, y1 = map(sum, zip(self[0].twoD(), worldview.shift))
        x2, y2 = map(sum, zip(self[1].twoD(), worldview.shift))
        steps = max(*map(abs, (x2-x1, y2-y1)))
        # The centers might be very close, but the radii my be more apart,
        # hence the following step. without it, the eye/iris gradient sometimes
        # only has two or three steps
        steps = max(steps, abs(self[0].radius - self[1].radius))
        colors = zip(self[0].color, self[1].color)

        # the old way is faster for smaller images, the new one for larger ones.
        # This table shows test measurings. Note that the size is the final size,
        # i.e. half the drawing size. O means the old one is faster, N the new one.
        #
        # zoom    test hash         32  64  128 256 512
        # ----------------------------------------------
        # close   21b96dcc68138     O   N   N   N!  N!
        # medium  18011847b11145af  O!  O   =   N   N
        # far     1895854ba5a70     O!  O!  O   =   N

        if xfunc is identity and yfunc is identity:
            if steps > 80: # based on tests, this number seems roughly to be the break-even point
                image.connect_circles((x1, y1), self[0].radius, self[0].color, (x2, y2), self[1].radius, self[1].color)
                return 

        for step in xrange(int(steps + 1)):
            factor = float(step) / steps
            color = tuple(map(int, (calc(c[0], c[1], factor) for c in colors)))
            x, y, r = calc(x1, x2, xfunc(factor)), calc(y1, y2, yfunc(factor)), calc(self[0].radius, self[1].radius, factor)
            image.circle((x, y), r, color)

    def __getitem__(self, index):
        return self._balls[index]
        
    def balls(self):
        return iter(self._balls)
        
    def project(self, worldview):
        for ball in self._balls:
            ball.project(worldview)
            
    def sort(self, worldview):
        self._balls.sort(key = lambda ball: ball.projection[2], reverse = True)
        
    def span(self):
        return self[1] - self[0]
        
    def bounding(self):
        return self[0].bounding() + self[1].bounding()

def reverse(func):
    def result(v):
        return 1 - func(1 - v)
    return result

class NonLinBone(Bone):        
    def __init__(self, ball1, ball2, xfunc = identity, yfunc = identity):
        self._balls = [ball1, ball2]
        self._xfunc = xfunc
        self._yfunc = yfunc
        
    def draw(self, image, worldview):
        super(NonLinBone, self).draw(image, worldview, self._xfunc, self._yfunc)

    def sort(self, worldview):
        previous = self._balls[:]
        super(NonLinBone, self).sort(worldview)
        if previous != self._balls:
            self._xfunc = reverse(self._xfunc)
            self._yfunc = reverse(self._yfunc)

def compare(worldview, first, second):
    """Compares two objects (balls or bones) to determine which one is behind the other.
       Note that although the worldview must be given, the objects still must
       have already been projected."""
       
    # FIXME: currently, this should be okay most of the time, because the
    # only subfigure used so far is unicorn.hairs. 
    if isinstance(first, Figure):
        return 1
    elif isinstance(second, Figure):
        return -1
    
       
    if isinstance(first, Ball) and isinstance(second, Ball):
        return cmp(first.projection[2], second.projection[2])
    elif isinstance(first, Bone) and isinstance(second, Ball):
        # see Definition 1.1 at http://en.wikibooks.org/wiki/Linear_Algebra/Orthogonal_Projection_Into_a_Line
        span = first.span()
        lensquare = float(sum(c**2 for c in span))
        factor = sum(c[0] * c[1] for c in zip(second - first[0], span)) / lensquare
        if factor < 0:
            return compare(worldview, first[0], second)
        elif factor > 1:
            return compare(worldview, first[1], second)
        else: # the projection is within the bone
            proj = tuple(c[0] * factor + c[1] for c in zip(span, first[0].center))
            proj_ball = Ball(proj, 1, None)
            proj_ball.project(worldview)
            return compare(worldview, proj_ball, second)
    elif isinstance(first, Ball) and isinstance(second, Bone):
        return -compare(worldview, second, first)
    elif isinstance(first, Bone) and isinstance(second, Bone):
        set1 = set(first.balls())
        set2 = set(second.balls())
        if set1 & set2: # they share a ball
            # which bone is longer?
            l1, l2 = (sum((b[1].projection[i] - b[0].projection[i])**2 for i in (0, 1, 2)) for b in (first, second))
            if l1 > l2:
                return compare(worldview, first, (set2 - set1).pop())
            else:
                return compare(worldview, (set1 - set2).pop(), second)
        else:
            # check for the simple case: is there a pair of balls (one from
            # first, one from second that we can compare instead?
            for ball1 in first.balls():
                for ball2 in second.balls():
                    if ball1.bounding().intersects(ball2.bounding()):
                        result = compare(worldview, ball1, ball2)
                        if result != 0:
                            return result
        
            # find the point where the bones intersect *on the screen*. t1
            # and t2 are the parameters such that, say, ball1_x + t1 * (ball2_x-ball1_x)
            # is the x-coordinate refereced by t1. t_ < 0 or t_ > 1 means
            # that the "intersection" isn't on the line itself.
            
            s1x, s1y, s1z = first[0].projection
            d1x, d1y, d1z = (first[1].projection[i] - first[0].projection[i] for i in (0, 1, 2))
            s2x, s2y, s2z = second[0].projection
            d2x, d2y, d2z = (second[1].projection[i] - second[0].projection[i] for i in (0, 1, 2))
            
            # this number is zero if and only if the lines are parallel
            # (again, their screen projections -- not neccessarily
            # parallel in 3d space)
            denom = d1x * d2y - d2x * d1y
            
            if abs(denom) < 1e-4:
                return 0 #FIXME later?
                
            t2 = (d1y * (s2x - s1x) - d1x * (s2y - s1y)) / denom
            if abs(d1x) > 1e-4:
                t1 = (s2x + t2 * d2x - s1x) / d1x
            elif abs(d1y) > 1e-4:
                t1 = (s2y + t2 * d2y - s1y) / d1y
            else:
                return 0 #FIXME later?
            
                
            if t1 < -.5 or t1 > 1.5 or t2 < -1 or t2 > 2:
                return 0
                
                
            return cmp(s1z + t1 * d1z, s2z + t2 * d2z) #FIXME: zero case?
    else:
        raise ValueError("Can't compare %s and %s" % (first, second))

def two_combinations(l):
    """itertools.combinations was introduced in Python 2.6; the app engine
       runs 2.5."""
    for i, first in enumerate(l):
        for second in l[i+1:]:
            yield (first, second)

# used in Figure.sort() to determine which thing should be drawn next if
# it's not possible to fullfill all draw_after constraints
def evilness(thing):
    z = thing.projection[2] if isinstance(thing, Ball) else max(b.projection[2] for b in thing.balls())
    return -z

class Figure(object):
    def __init__(self):
        self._things = []
        
    def add(self, *things):
        self._things.extend(things)
        
    def project(self, worldview):
        for thing in self._things:
            thing.project(worldview)
            
    def sort(self, worldview):
        """this assumes that projection has already happened!"""
        comp = functools.partial(compare, worldview)
        
        # values of this dict are lists of all things that have
        # to be drawn before the corresponding key
        draw_after = dict((thing, []) for thing in self._things) 

        for first, second in two_combinations(self._things):
            if second not in draw_after[first] and first not in draw_after[second]:
                if first.bounding().intersects(second.bounding()):
                    c = comp(first, second)
                    if c < 0:
                        # first is in front of second
                        draw_after[first].append(second)
                    elif c > 0:
                        draw_after[second].append(first)
        
        # this is pretty much the algorithm from http://stackoverflow.com/questions/952302/
        sorted_things = []
        queue = []
        for thing, deps in draw_after.items():
            if not deps:
                queue.append(thing)
                del draw_after[thing]

        while draw_after:
            while queue:
                popped = queue.pop()
                sorted_things.append(popped)
                for thing, deps in draw_after.items():
                    if popped in deps:
                        deps.remove(popped)
                        if not deps:
                            queue.append(thing)
                            del draw_after[thing]

            if draw_after:
                # if the sorting couldn't fullfill all "draw after" contraints,
                # we remove the ball / bone which lies farthest in the back
                # and try again

                least_evil = min((thing for thing in draw_after.iterkeys()),
                                 key = evilness
                                )
                sorted_things.append(least_evil)
                del draw_after[least_evil]
                for thing, deps in draw_after.items():
                    if least_evil in deps:
                        deps.remove(least_evil)
                        if not deps:
                            queue.append(thing)
                            del draw_after[thing]
                
        self._things = sorted_things            

        for thing in self._things:
            thing.sort(worldview)
            
    def draw(self, image, worldview):
        viewrect = Rect(*(tuple(-c for c in worldview.shift) + tuple(image.size - c for c in worldview.shift)))
        for thing in self._things:
            if thing.bounding().intersects(viewrect):
                thing.draw(image, worldview)

    def balls(self):
        for thing in self._things:
            for ball in thing.balls():
                yield ball

    def ball_set(self):
        """Returns all balls that are either directly in this figure or in
           on of its bones. It returns a set; i.e. each ball is returned
           exactly once."""
        return set(self.balls())
        
    def scale(self, factor):
        for ball in self.ball_set():
            ball.radius *= factor
            ball.center = tuple(c * factor for c in ball.center)
            
    def bounding(self):
        return sum((thing.bounding() for thing in self._things), None)
        
