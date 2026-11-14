from pathlib import Path
from collections import Counter
import hashlib, json, re, struct, sys, zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'qt-tools'))
from PyQt5.QtCore import QResource, QFile, QIODevice, QDir, QDirIterator, QByteArray
from PyQt5.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parent
source = Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\rcc\NxDeviceResource.rcc')
target = root / 'NxDeviceResource.controls-purple-candidate.rcc'
original = source.read_bytes()
out = bytearray(original)
assert QResource.registerResource(str(source))

# Keep conflict/red indicators distinct and leave all geometry and event handling intact.
colors = {
    '#02bfff':'#b983ed', '#01a4ff':'#b983ed', '#00a3ff':'#b983ed',
    '#3485ff':'#a46ddd', '#3dbaff':'#c99afa', '#00d1ff':'#d6aaff',
    '#7addff':'#e3c7ff', '#00b0ec':'#b983ed', '#0098cc':'#9560c8',
    '#0085b3':'#8051ad', '#267aca':'#8657b4', '#60cdff':'#d4adf5',
    '#151820':'#171020', '#313d5b':'#493459', '#343947':'#372942',
    '#343340':'#34263e', '#464858':'#50405a', '#59616c':'#71627c',
}
iterator = QDirIterator(':', QDir.Files, QDirIterator.Subdirectories)
paths = []
storage_users = {}
while iterator.hasNext():
    path = iterator.next()
    resource = QResource(path)
    raw_storage = bytes(resource.data())
    storage_users.setdefault((resource.isCompressed(), raw_storage), []).append(path)
    if path.endswith('.svg') and (path.startswith(':/resources/images/keymap/') or '/nx/keymap_' in path):
        paths.append(path)

changes, skipped, expected = [], [], {}
for path in paths:
    resource = QResource(path)
    file = QFile(path)
    if not file.open(QIODevice.ReadOnly): raise RuntimeError(path)
    raw = bytes(file.readAll())
    updated = re.sub(rb'#[0-9a-fA-F]{6}\b', lambda m: colors.get(m.group().decode().lower(), m.group().decode()).encode(), raw)
    if updated == raw: continue
    if not QSvgRenderer(QByteArray(updated)).isValid(): raise RuntimeError('Invalid SVG: '+path)
    old = bytes(resource.data())
    needle = struct.pack('>I', len(old)) + old
    positions = []
    pos = original.find(needle)
    while pos >= 0:
        positions.append(pos)
        pos = original.find(needle, pos + 1)
    if not positions:
        skipped.append([path, 'storage not found']); continue
    users = storage_users[(resource.isCompressed(), old)]
    if any(user not in paths for user in users):
        skipped.append([path, 'shared with other interface']); continue
    payload = struct.pack('>I', len(updated)) + zlib.compress(updated,9) if resource.isCompressed() else updated
    if len(payload) > len(old):
        skipped.append([path, 'does not fit']); continue
    replacement = struct.pack('>I',len(payload)) + payload + bytes(len(old)-len(payload))
    if any(out[pos:pos+len(needle)] not in (needle, replacement) for pos in positions):
        skipped.append([path, 'overlapping storage']); continue
    for pos in positions:
        out[pos:pos+len(needle)] = replacement
    expected[path] = updated
    changes.append(path)

if not changes: raise RuntimeError('No resources changed')
target.write_bytes(out)
QResource.unregisterResource(str(source))
if not QResource.registerResource(str(target)): raise RuntimeError('Candidate cannot be registered')
for path, data in expected.items():
    f = QFile(path)
    if not f.open(QIODevice.ReadOnly) or bytes(f.readAll()) != data:
        raise RuntimeError('Resource verification failed: '+path)
manifest = {'source_sha256':hashlib.sha256(original).hexdigest(), 'candidate_sha256':hashlib.sha256(out).hexdigest(), 'changed':changes, 'skipped':skipped}
(root/'control-theme-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Recolored:',len(changes),'Skipped:',len(skipped),'Candidate:',target)
