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
    
from graphics import SquareImage, hls_to_rgb
from core import Data

class BackgroundData(Data):
    def __init__(self):
        self._data = { "sky_hue": 60,
                       "sky_sat": 50,
                       "land_hue": 120,
                       "land_sat": 50,
                       "horizon": .6,
                       "rainbow_foot": .5, # [0,1]-based x-coordinate of the point where the rainbow hits the horizon
                       "rainbow_dir": -1,
                       "rainbow_height": 1.5,
                       "rainbow_band_width": 5,
                       "land_light": 40,
                       "cloud_positions": [(.6, .25)],
                       "cloud_sizes": [(.1, 1.5)], # the first is relative to the image, the second is relative to the first
                       "cloud_lightnesses": [95],
                     }

    def randomize(self, randomizer):
        choice, randint, random = randomizer.choice, randomizer.randint, randomizer.random
        
        self.sky_hue = randint(0, 359)
        self.sky_sat = randint(30, 70)
        self.land_hue = randint(0, 359)
        self.land_sat = randint(20, 60)
        self.horizon = .5 + random() * .2
        self.rainbow_foot = .2 + random() * .6
        self.rainbow_dir = choice((-1, 1))
        self.rainbow_height = .5 + random() * 1.5
        self.rainbow_band_width = .01 + random()* .02
        self.land_light = randint(20, 50)
        
    def randomize2(self, randomizer):
        choice, randint, random = randomizer.choice, randomizer.randint, randomizer.random
        
        self.cloud_positions = [(random(), (.3 + random() * .6) * self.horizon) for i in xrange(randint(1, 3))]
        self.cloud_sizes = [(random()*.04 + .02, random()*.7 + 1.3) for c in self.cloud_positions]
        self.cloud_lightnesses = [randint(75, 90) for c in self.cloud_positions]

def get_background(size, data): #return size is 2*size!

    im = SquareImage(size * 2, data.sky_col(60), data.sky_col(10))
 
    horizon_pix = int(im.size * data.horizon)
        
    center = (im.size * (data.rainbow_foot + data.rainbow_dir * data.rainbow_height), horizon_pix)
    outer_radius = data.rainbow_height * im.size
    delta = data.rainbow_band_width * im.size
    
    im.save()        
        
    for w in xrange(7):
        col = hls_to_rgb(w * 45, 50, 100)
        im.circle(center, outer_radius - w * delta, col)

    im.circle(center, outer_radius - 7 * delta, im.RESTORE)

    land1 = data.land_col(data.land_light)
    land2 = data.land_col(data.land_light / 2)
    im.hor_gradient(land1, land2, 0, 2 * size - 1, horizon_pix, 2 * size - 1)

    for pos, sizes, lightness in zip(data.cloud_positions, data.cloud_sizes, data.cloud_lightnesses):
        cloud(im, (im.size * pos[0], im.size * pos[1]), sizes[0] * im.size, sizes[1] * sizes[0] * im.size, data.sky_col(lightness))

    return im


def cloud(img, pos, size1, size2, color):
    """sizeX is a radius of one of the circles. size2 should be
       between 100 and 200% of size1. pos is bottom center."""
    x, y = map(int, pos)
    size1, size2 = int(size1), int(size2)
    
    img.circle((x - 2 * size1, y - size1 - 1), size1, color)
    img.circle((x + 2 * size1, y - size1 - 1), size1, color)
    img.top_half_circle((x, y-size1), size2, color)
    for ly in xrange(y - size1, y + 1):
        img.hor_line(color, x - 2 * size1, x + 2 * size1, ly)
        
