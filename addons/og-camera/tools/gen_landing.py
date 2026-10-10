"""Writes edits_landing.txt: flatten the slope-following pitch curves of the landing states (1.3.0).

The low landing state (ONCL_Landing a1d68f0) and the high one (ONCH_Landing b1bb9af) turn the slope the
skater lands on into camera pitch with a curve that follows the slope almost 1:1 (-90 -> -75, 65 -> 45).
Scaling the curve's output keeps the camera nearer level on landing. Each asset copy (the action graph
and its onbegin/onend command copies) holds its own instances, so they are found by scanning."""
import pickle
import re

SCALE = 0.4
a = pickle.load(open('D:/dev/ogcam/assets.pkl', 'rb'))
pfx = 'gameplay/cameras/dingoesmcameradirector_esmcameradirectortree/'
targets = {'low': ('a1d68f0_ag', '8815c864'), 'high': ('b1bb9af_ag', 'e8ca85ca')}
out = []
for which, (ag, var) in targets.items():
    for key in sorted(k for k in a if k.startswith(pfx + ag)):
        blocks = re.split(r'\n(?=#\d+ )', a[key])
        by_index = {b.split()[0]: b for b in blocks}
        curves = {}
        for b in blocks:
            if 'YawRelativeCameraVariableBlend' not in b.split('\n')[0]:
                continue
            m = re.search(r'CameraVariable = -> import #\d+ (\S{8})', b)
            c = re.search(r'OffsetValueInterpolationCurve = -> #(\d+)', b)
            if m and c and m.group(1) == var:
                curves[c.group(1)] = by_index['#' + c.group(1)]
        if not curves:
            continue
        out.append(f'# {which} landing: {key[len(pfx):]}')
        out.append('asset ' + key)
        for idx, block in sorted(curves.items(), key=lambda x: int(x[0])):
            for i, (x, y) in enumerate(re.findall(r'X = (\S+)\n\s+Y = (\S+)', block)):
                out.append(f'set #{idx} Points[{i}].Y {round(float(y) * SCALE, 3)}')
open('D:/dev/ogcam/edits_landing.txt', 'w').write('\n'.join(out) + '\n')
print(sum(1 for l in out if l.startswith('asset ')), 'asset edits')
