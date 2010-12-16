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
    
from core import Ball, Bone, Figure, NonLinBone, Data
import math

pose_functions = {}

def pose(name):
    def decorator(f):
        pose_functions[name] = f
        return f
    return decorator
    
def interpol(*args):
    l = list(sorted(args))
    l.insert(0, (l[-1][0] - 1, l[-1][1]))
    l.append((l[1][0] + 1, l[1][1]))
    import sys
    def f(x):
        x = x % 1
        x1, v1 = max(p for p in l if p[0] <= x)
        x2, v2 = min(p for p in l if p[0] >= x)
        if x1 == x2:
            return v1
        r = v1 + (v2 - v1) * (x - x1) / (x2 - x1)
        return r
    return f

@pose("rotatory_gallop")
def _r_gallop(unicorn, data):
    # movement per phase: ca. 125
    phase = data.pose_phase

    fl, fr, bl, br = unicorn.legs
    
    # approximated from http://commons.wikimedia.org/wiki/File:Horse_gif_slow.gif
    front_top = interpol((9/12., 74), (2.5/12., -33))
    front_bottom = interpol((2/12., 0), (6/12., -107), (8/12., -90), (10/12., 0))
    back_top = interpol((11/12., -53), (4/12., 0), (6/12., 0))
    back_bottom = interpol((11/12., 0), (1.5/12., 90), (6/12., 30), (8/12., 50))

    fr.knee.rotate(front_top(phase), fr.hip)
    fr.hoof.rotate(front_top(phase), fr.hip)

    fr.hoof.rotate(front_bottom(phase), fr.knee)

    fl.knee.rotate(front_top(phase - .25), fl.hip)
    fl.hoof.rotate(front_top(phase - .25), fl.hip)

    fl.hoof.rotate(front_bottom(phase - .25), fl.knee)

    br.knee.rotate(back_top(phase), br.hip)
    br.hoof.rotate(back_top(phase), br.hip)

    br.hoof.rotate(back_bottom(phase), br.knee)

    bl.knee.rotate(back_top(phase - .167), bl.hip)
    bl.hoof.rotate(back_top(phase - .167), bl.hip)

    bl.hoof.rotate(back_bottom(phase - .167), bl.knee)

@pose("walk")
def _walk(unicorn, data):
    phase = data.pose_phase

    fl, fr, bl, br = unicorn.legs
    
    # approximated from http://de.wikipedia.org/w/index.php?title=Datei:Muybridge_horse_walking_animated.gif&filetimestamp=20061003154457
    front_top = interpol((6.5/9., 40), (2.5/9., -35))
    front_bottom = interpol((7/9., 0), (2/9., 0), (5/9., -70))

    back_top = interpol((1/9., -35), (4/9., 0), (6/12., 0))
    
    back_bottom = interpol((5/9., 40), (9/9., 10))

    fr.knee.rotate(front_top(phase), fr.hip)
    fr.hoof.rotate(front_top(phase), fr.hip)

    fr.hoof.rotate(front_bottom(phase), fr.knee)

    fl.knee.rotate(front_top(phase - .56), fl.hip)
    fl.hoof.rotate(front_top(phase - .56), fl.hip)

    fl.hoof.rotate(front_bottom(phase - .56), fl.knee)

    br.knee.rotate(back_top(phase), br.hip)
    br.hoof.rotate(back_top(phase), br.hip)

    br.hoof.rotate(back_bottom(phase), br.knee)

    bl.knee.rotate(back_top(phase - .44), bl.hip)
    bl.hoof.rotate(back_top(phase - .44), bl.hip)

    bl.hoof.rotate(back_bottom(phase - .44), bl.knee)


class UnicornData(Data):
    def __init__(self):
        self._data = { "body_hue": 0,
                       "body_sat": 75,
                       "horn_hue": 180,
                       "horn_sat": 75,
                       "snout_size": 15, # 8,30
                       "snout_length": 80,
                       "head_size": 30, #25,40
                       "shoulder_size": 50, # 40,60
                       "butt_size": 45, # 30,60
                       "horn_onset_size": 8,
                       "horn_tip_size": 4,
                       "horn_length": 60,
                       "horn_angle": 30, # 0 means straight in x-direction, >0 means upwards
                       "eye_size": 10,
                       "iris_size": 7,
                       "iris_hue": 240,
                       "iris_sat": 80,
                       "pupil_size": 4,
                       "pose_sitting": 0, # DEPRECATED 0 means standing, 1 means sitting
                       "pose_upright": 0, # DEPRECATED 
                       "hair_hue": 240,
                       "hair_sat": 80,
                       "hair_starts": [0, 20, 30, 40, 50, 60, 80, 100],
                       "hair_gammas": [.3, .6, .9, 1.1, 1.3, 1.5, 1.9, 2.3],
                       "hair_lengths": [80, 90, 100, 110, 120, 130, 140, 150],
                       "hair_angles": [20, 25, 30, 35, 40, 45, 50, 55],
                       "hair_tip_lightnesses": [50, 55, 60, 65, 70, 75, 80, 85],
                       "hair_straightnesses": [-20, -15, -10, -5, 0, 5, 10, 15], # for lack of a better word -- this is just the z offsets of the tip
                       "tail_start_size": 8,
                       "tail_end_size": 16,
                       "tail_length": 120,
                       "tail_angle": -30,
                       "tail_gamma": 1.2,
                       "brow_size": 3,
                       "brow_length": 10,
                       "brow_mood": -.5, # from -1 (angry) to 1 (astonished)
                       "neck_tilt": 30,
                       "face_tilt": -20,
                       "pose_kind": "rotatory_gallop",
                       "pose_phase": .5
                     }

    def randomize(self, randomizer):
        randint, random = randomizer.randint, randomizer.random
        
        self.body_hue = randint(0, 359)
        self.body_sat = randint(50, 100)
        self.horn_hue = (self.body_hue + randint(60, 300)) % 360
        self.horn_sat = randint(50, 100)
        self.snout_size = randint(8, 30)
        self.snout_length = randint(70, 110)
        self.head_size = randint(25, 40)
        self.shoulder_size = randint(40, 60)
        self.butt_size = randint(30, 60)
        self.horn_onset_size = randint(6, 12)
        self.horn_tip_size = randint(3,6)
        self.horn_length = randint(50, 100)
        self.horn_angle = randint(10, 60)
        self.eye_size = randint(8, 12)
        self.iris_size = randint(3, 6)
        self.iris_hue = randint(70, 270)
        self.iris_sat = randint(40, 70)
        self.pupil_size = randint(2, 5)
        self.pose_sitting = randint(0, 60) / 100.0
        #self.pose_upright = randint(20, 80) / 100.0
        self.hair_hue = (self.body_hue + randint(60, 300)) % 360
        self.hair_sat = randint(60, 100)
        self.hair_starts = [randint(-20, 100) for i in xrange(randint(12, 30))]
        self.hair_gammas = [.3 + random()*3 for h in self.hair_starts]
        self.hair_lengths = [randint(80, 150) for h in self.hair_starts]
        self.hair_angles = [randint(00, 60) for h in self.hair_starts]

    def randomize2(self, randomizer):
        randint, random = randomizer.randint, randomizer.random
        self.hair_tip_lightnesses = [randint(40, 85) for h in self.hair_starts]
        self.hair_straightnesses = [randint(-40, 40) for h in self.hair_starts] 
        self.tail_start_size = randint(4, 10)
        self.tail_end_size = randint(10, 20)
        self.tail_length = randint(100, 150)
        self.tail_angle = randint(-20, 45)
        self.tail_gamma = .1 + random()*6
        self.brow_size = randint(2, 4)
        self.brow_length = 2 + random()*3
        self.brow_mood = 2 * random() - 1
        self.neck_tilt = randint(-30, 30)
        self.face_tilt = randint(*sorted((self.neck_tilt / 3, self.neck_tilt / 4)))
        
    def randomize3(self, randomizer):
        randint, random, choice = randomizer.randint, randomizer.random, randomizer.choice

        self.pose_kind = choice(pose_functions.keys())
        self.pose_phase = random()

def gammafunc(gamma):
    def result(x):
        return x**gamma
    return result

class Unicorn(Figure):
    
    def __init__(self, data):
        super(Unicorn, self).__init__()
        
        self.head = Ball((0,0,0), data.head_size, data.body_col(60))
        self.snout = Ball((-25, 60, 0), data.snout_size, data.body_col(80))
        self.snout.set_distance(data.snout_length, self.head)
        self.shoulder = Ball((80, 120, 0), data.shoulder_size, data.body_col(40))
        self.butt = Ball((235, 155, 0), data.butt_size, data.body_col(40))
        self.horn_onset = Ball((-22, -10, 0), data.horn_onset_size, data.horn_col(70))
        self.horn_onset.move_to_sphere(self.head)
        
        self.horn_tip = Ball(self.horn_onset - (10, 0, 0), data.horn_tip_size, data.horn_col(90))
        self.horn_tip.set_distance(data.horn_length, self.horn_onset)
        self.horn_tip.rotate(data.horn_angle, self.horn_onset)

        self.create_eyes(data)
        self.create_legs(data)
        
        pose_functions[data.pose_kind](self, data)

        self.create_mane(data)

        self.tail_start = Ball(self.butt - (-10, 10, 0), data.tail_start_size, data.hair_col(80))
        self.tail_start.move_to_sphere(self.butt)
        self.tail_end = Ball(self.tail_start - (-10, 0, 0), data.tail_end_size, data.hair_col(60))
        self.tail_end.set_distance(data.tail_length, self.tail_start)
        self.tail_end.rotate(data.tail_angle, self.tail_start)
        self.tail = NonLinBone(self.tail_start, self.tail_end, yfunc = gammafunc(data.tail_gamma))
        
        square = gammafunc(2)

        self.add(Bone(self.snout, self.head),
                 Bone(self.horn_onset, self.horn_tip),
                 Bone(self.eye_left, self.iris_left),
                 Bone(self.eye_right, self.iris_right),
                 self.pupil_left, self.pupil_right,
                 NonLinBone(self.brow_left_inner, self.brow_left_middle, xfunc = square),
                 NonLinBone(self.brow_left_middle, self.brow_left_outer, xfunc = math.sqrt),
                 NonLinBone(self.brow_right_inner, self.brow_right_middle, xfunc = square),
                 NonLinBone(self.brow_right_middle, self.brow_right_outer, xfunc = math.sqrt),
                )

        for thing in self.ball_set():
            thing.rotate(data.face_tilt, self.head, axis = 0)

        self.add(Bone(self.head, self.shoulder),
                 self.hairs
                )

        for thing in self.ball_set():
            thing.rotate(data.neck_tilt, self.shoulder, axis = 1)

        self.add(Bone(self.shoulder, self.butt),
                 self.tail,
                )

        for leg in self.legs[:2]:
            self.add(*leg)
            
        for leg in self.legs[2:]:
            self.add(*leg)

    def create_eyes(self, data):
        self.eye_left = Ball((-10, 3, -5), data.eye_size, (255, 255, 255))
        self.eye_left.set_gap(5, self.head)
        self.eye_right = Ball((-10, 3, 5), data.eye_size, (255, 255, 255))
        self.eye_right.set_gap(5, self.head)

        self.iris_left = Ball(self.eye_left - (4, 0, 0), data.iris_size, data.iris_col(80))
        self.iris_right = Ball(self.eye_right - (4, 0, 0), data.iris_size, data.iris_col(80))

        self.pupil_left = Ball(self.iris_left - (10, 0, 0), data.pupil_size, (0, 0, 0))
        self.pupil_left.move_to_sphere(self.iris_left)
        self.pupil_right = Ball(self.iris_right - (10, 0, 0), data.pupil_size, (0, 0, 0))
        self.pupil_right.move_to_sphere(self.iris_right)

        mood_delta = data.brow_mood * 3
        
        self.brow_left_inner = Ball(self.eye_left - (0, 10, -data.brow_length), data.brow_size, data.hair_col(50))
        self.brow_left_inner.set_gap(5 + mood_delta, self.eye_left)
        self.brow_left_middle = Ball(self.eye_left - (0, 10, 0), data.brow_size, data.hair_col(70))
        self.brow_left_middle.set_gap(5 + data.brow_length, self.eye_left)
        self.brow_left_outer = Ball(self.eye_left - (0, 10, data.brow_length), data.brow_size, data.hair_col(60))
        self.brow_left_outer.set_gap(5 - mood_delta, self.eye_left)
        self.brow_right_inner = Ball(self.eye_right - (0, 10, data.brow_length), data.brow_size, data.hair_col(60))
        self.brow_right_inner.set_gap(5 + mood_delta, self.eye_right)
        self.brow_right_middle = Ball(self.eye_right - (0, 10, 0), data.brow_size, data.hair_col(70))
        self.brow_right_middle.set_gap(5 + data.brow_length, self.eye_right)
        self.brow_right_outer = Ball(self.eye_right - (0, 10, -data.brow_length), data.brow_size, data.hair_col(50))
        self.brow_right_outer.set_gap(5 - mood_delta, self.eye_right)

    def create_legs(self, data):
        self.legs = [] # order: front left, front right, back left, back right

        for z in (-25, 25): # front
            hip = Ball((55, 160, z), 25, data.body_col(40))
            knee = Ball((35, 254, z), 9, data.body_col(70))
            hoof = Ball((55, 310, z), 11, data.body_col(45))
            hip.move_to_sphere(self.shoulder)
            leg = Leg(hip, knee, hoof)
            self.legs.append(leg)

        for z in (-25, 25): # back
            hip = Ball((225, 190, z), 25, data.body_col(40))
            knee = Ball((230, 265, z), 9, data.body_col(70))
            hoof = Ball((220, 310, z), 11, data.body_col(45))
            hip.move_to_sphere(self.butt)
            leg = Leg(hip, knee, hoof)
            self.legs.append(leg)

    def create_mane(self, data):
        self.hairs = Figure()

        hair_top = Ball(self.head - (-10, 5, 0), 8, None)
        hair_top.move_to_sphere(self.head)
        hair_bottom = Ball(self.shoulder - (-10, 15, 0), 8, None)
        hair_bottom.move_to_sphere(self.shoulder)        
        for start, gamma, length, angle, lightness, straightness in zip(
                        data.hair_starts, data.hair_gammas, data.hair_lengths,
                        data.hair_angles, data.hair_tip_lightnesses,
                        data.hair_straightnesses):
            x, y, z = (c[0] + start / 100.0 * (c[1] - c[0]) for c in zip(hair_top.center, hair_bottom.center))
            hair_start = Ball((x, y, z), 8, data.hair_col(60))
            hair_end = Ball((x + length, y, z + straightness), 4, data.hair_col(lightness))
            hair_end.rotate(-angle, hair_start)
            hair = NonLinBone(hair_start, hair_end, yfunc = gammafunc(gamma))
            self.hairs.add(hair)        

class Leg(list):
    def __init__(self, hip, knee, hoof):
        super(Leg, self).__init__((Bone(hip, knee), Bone(knee, hoof)))
        self.hip = hip
        self.knee = knee
        self.hoof = hoof
