"""Writes edits_shots.txt: the fisheye and per-shot edits for OG Camera 1.1.0."""
import math
import pickle
import re

out = []

# ---- Fisheye -------------------------------------------------------------------------------
# Every time-of-day "look" switches lens distortion off over the base camera; switch it on, and give
# the base camera the curve of skate.'s own fisheye lens (camera/camerapresets/lens/ve_camlens_basic_fisheye).
ve = open('D:/dev/ogcam/allve.txt').read()
docs = {}
for block in re.split(r'\n(?====== )', ve):
    name = block.split()[1]
    docs.setdefault(name, block)


def filmic_index(name):
    found = re.findall(r'^#(\d+) \S+ <FilmicEffectsComponentData>', docs[name], re.M)
    assert len(found) == 1, (name, found)
    return found[0]


out.append('# Fisheye: base camera curve (gain 0.413, cubic 1.053, stretch 0.296 = skate.\'s own fisheye lens)')
base = 'lighting/ve/camera/ve_dingo_50mm_neutral_base'
i = filmic_index(base)
out.append('asset ' + base)
out.append(f'set #{i} LensDistortionGain 0.413')
out.append(f'set #{i} LensDistortionCubicGain 1.053')
out.append(f'set #{i} LensDistortionStretch 0.296')
out.append(f'append #{i} PropertyOverrides LensDistortionCubicGain')
out.append(f'append #{i} PropertyOverrides LensDistortionStretch')
# Bits 13 and 14 mark the two fields as overridden (bit n = nth field of FilmicEffectsComponentData).
out.append(f'set #{i} FieldFlagOverride0 {6403 | (1 << 13) | (1 << 14)}')
out.append('# Fisheye: every gameplay look keeps it on')
looks = sorted(n for n in docs if re.search(r'/ve_look_', n) and '"EnableLensDistortion"' in docs[n])
for name in looks:
    out.append('asset ' + name)
    out.append(f'set #{filmic_index(name)} EnableLensDistortion true')

# ---- Shots ---------------------------------------------------------------------------------
assets = pickle.load(open('D:/dev/ogcam/assets.pkl', 'rb'))
pfx = 'gameplay/cameras/dingoesmcameradirector_esmcameradirectortree/'


def holders(guid):
    return sorted(k for k, v in assets.items() if k.startswith(pfx) and guid in v)


def shot(comment, framing, blend, distance=None, elevation=None, look_down=None, yaw=None, z=None, x=None):
    """framing: FramingCameraControllerData guid; blend: CameraFramingBlendData guid holding its copy
    (slice index 0). Skate 3 shot: camera `distance` m from the subject at `elevation` degrees,
    tilted down by elevation + framing pitch (`look_down`)."""
    out.append('# ' + comment)
    sets = []
    if distance is not None:
        y = distance * math.sin(math.radians(elevation))
        zz = distance * math.cos(math.radians(elevation))
        sets += [('y', round(y, 3), 'pos'), ('z', round(zz, 3), 'pos'), ('x', -look_down, 'rot')]
    if z is not None:
        sets.append(('z', z, 'pos'))
    if yaw is not None:
        sets.append(('y', yaw, 'rot'))
    if x is not None:
        sets.append(('x', x, 'pos'))
    for asset in holders(framing):
        out.append('asset ' + asset)
        doc = assets[asset]
        for axis, value, kind in sets:
            field = 'LocalPositionOffset' if kind == 'pos' else 'LocalRotationOffset'
            out.append(f'set {framing} {field}.Value.{axis} {value}')
            if blend and blend in doc:
                field = 'PositionOffset' if kind == 'pos' else 'RotationOffset'
                out.append(f'set {blend} YawSlices[0].Framings[0].{field}.Value.{axis} {value}')


# Low camera (ONCL_*): its orbit pitch is level, so Skate 3's elevation goes into the framing.
shot('Low grind -> Skate 3 rail_far: 2.5 m, 15 deg up, looking down at the board',
     '931ab302-104d-40cb-acee-432536f0dc30', '41e20c28-5f41-423b-a27a-ed32709a40c5',
     distance=2.5, elevation=15, look_down=15, x=0)
shot('Low manual -> between Skate 3 close_manual and far_manual: 1.6 m, level, tilted 5 deg up, 15 deg to the side',
     'bf2c5669-333f-4653-914e-93810f96c82a', '63ad2a3c-44d4-4e8e-8f88-8ca74e15f8bc',
     distance=1.6, elevation=0, look_down=-5, yaw=-15, x=-0.5)
shot('Low big air -> Skate 3 air_big: pulled back to 4 m, 15 deg up, tilted 5 deg up at the skater',
     '94d298bb-fd13-4c3f-bcd7-8b5bd52f29a2', 'edda6f1b-95a0-4fe3-90d4-55219cc58e3c',
     distance=4.0, elevation=15, look_down=-5)
shot('Low big air (second framing)',
     'b34dbebc-9b64-4f7b-9384-56c7f3a6d16a', '53965c6e-3e26-4c91-b46f-e491fd82f274',
     distance=4.0, elevation=15, look_down=-5)
# High camera (ONCH_*): the orbit already supplies the 27 deg; Skate 3's high shots set the distance.
shot('High manual -> Skate 3 high_manual: 2.25 m, 19 deg up, looking down at the skater (the manual state levels the orbit)',
     'd9f51af0-d17e-4c3e-a8f2-942280b5ebf3', '61b1b0b3-5b7f-4688-a00e-65fb8d27f783',
     distance=2.25, elevation=19, look_down=19)
shot('High big air -> Skate 3 high_bigair: pulled back to 5 m',
     'ecd85611-c2fd-491f-8bc4-5f65e207c929', '91e1dc34-827f-4b3c-aed2-0679bee5a232', z=5.0)

open('D:/dev/ogcam/edits_shots.txt', 'w').write('\n'.join(out) + '\n')
print(len(looks), 'looks;', sum(l.startswith('asset ') for l in out), 'asset edits')
