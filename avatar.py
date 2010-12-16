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
    
from random import Random
from core import WorldView
from unicorn import UnicornData, Unicorn
from background import get_background, BackgroundData
from math import sqrt
from graphics import SquareImage

class BadHashString(Exception):
    pass

def create_avatar(size, hash_val, with_background = True):
    """Returns a unicorn image with *twice* the given size (i.e. with size=128,
       you'll get a 256x256 image) -- it's aliased, so you'll want to run it
       through a resizing filter to have an antialiased image of your actual
       desired size."""
       
    randomizer = Random()
    randint, choice, random = randomizer.randint, randomizer.choice, randomizer.random
    randomizer.seed(hash_val)
    
    unicorndata = UnicornData()
        
    backgrounddata = BackgroundData()

    # Here comes the randomizing. To keep consistence of unicorns between versions,
    # new random() calls should usually be made *after* the already existing calls
    unicorndata.randomize(randomizer)
    backgrounddata.randomize(randomizer)
    unicorn_scale_factor = (.5 + (random()**2) * 2.5)
    y_angle = 90 + choice((-1,1)) * randint(10, 75)
    x_angle = randint(-20, 20)
    unicorndata.randomize2(randomizer) # new in v4
    backgrounddata.randomize2(randomizer) 
    unicorndata.randomize3(randomizer) # new in v5
    # End of randomizing

    if (y_angle - 90) * unicorndata.neck_tilt > 0:
        # The unicorn should look at the camera.
        unicorndata.neck_tilt = -unicorndata.neck_tilt
        unicorndata.face_tilt = -unicorndata.face_tilt
        
    unicorn = Unicorn(unicorndata)
    if with_background:
        im = get_background(size, backgrounddata)
    else:
        im = SquareImage.plain(size * 2, (255, 255, 255))

    unicorn.scale(unicorn_scale_factor * size / 200.0)
    
    wv = WorldView(y_angle, x_angle, (150, 0, 0), (0, 100))

    unicorn.project(wv)
    headpos = unicorn.head.projection
    shoulderpos = unicorn.shoulder.projection
    
    headshift = (im.size/2 - headpos[0], im.size/3 - headpos[1])
    shouldershift = (im.size / 2 - shoulderpos[0], im.size/2 - shoulderpos[1])
    
    # factor = 1 means center the head at (1/2, 1/3); factor = 0 means
    # center the shoulder at (1/2, 1/2)
    factor = sqrt((unicorn_scale_factor - .5) / 2.5)
    wv.shift = tuple(c0 + factor * (c1 - c0) for c0, c1 in zip(shouldershift, headshift))

    unicorn.sort(wv)
    unicorn.draw(im, wv)
    
    return im.to_bmp()

