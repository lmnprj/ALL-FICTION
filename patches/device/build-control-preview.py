from pathlib import Path
import hashlib,json,struct,sys,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qt-tools'))
from PyQt5.QtCore import QResource,QFile,QIODevice,QByteArray,QDir,QDirIterator
from PyQt5.QtSvg import QSvgRenderer
root=Path(__file__).resolve().parent
target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\rcc\NxDeviceResource.rcc')
original=target.read_bytes();out=bytearray(original);assert QResource.registerResource(str(target))
paths=[':/resources/images/keymap/swipehold/normal.svg',':/resources/images/keymap/swipehold/hovered.svg',':/resources/images/keymap/swipehold/content.svg',':/resources/images/keymap/left_stick_walk/normal.svg',':/resources/images/keymap/left_stick_walk/hovered.svg',':/resources/images/keymap/left_stick_walk/content.svg']
expected={};shared={}
it=QDirIterator(':',QDir.Files,QDirIterator.Subdirectories)
while it.hasNext():
 p=it.next();r=QResource(p);shared.setdefault((r.isCompressed(),bytes(r.data())),[]).append(p)
for path in paths:
 r=QResource(path);f=QFile(path);assert f.open(QIODevice.ReadOnly);data=bytes(f.readAll());old=bytes(r.data())
 # Brighter boundary and translucent interior expose the game underneath.
 updated=data.replace(b'fill-opacity="0.7"',b'fill-opacity="0.38"').replace(b'stroke="white"',b'stroke="#caa4ee"').replace(b'stroke-opacity="0.18"',b'stroke-opacity="0.6"')
 if path.endswith('/content.svg'):
  updated=updated.replace(b'fill="white" fill-opacity="0.18"',b'fill="#caa4ee" fill-opacity="0.32"')
 updated=updated.replace(b'\r',b'').replace(b'\n',b'')
 assert QSvgRenderer(QByteArray(updated)).isValid()
 users=shared[(r.isCompressed(),old)]
 if any(not (x.startswith(':/resources/images/keymap/') or x.startswith(':/resources/images/keyhint/')) for x in users):raise RuntimeError('Shared outside keymap: '+path)
 needle=struct.pack('>I',len(old))+old
 payload=struct.pack('>I',len(updated))+zlib.compress(updated,9) if r.isCompressed() else updated
 if len(payload)>len(old):raise RuntimeError('No room for '+path)
 replacement=struct.pack('>I',len(payload))+payload+bytes(len(old)-len(payload));pos=0
 while True:
  pos=original.find(needle,pos)
  if pos<0:break
  if out[pos:pos+len(needle)] not in (needle,replacement):raise RuntimeError('Overlap')
  out[pos:pos+len(needle)]=replacement;pos+=len(needle)
 for p in users:expected[p]=updated
dest=root/'NxDeviceResource.control-preview-candidate.rcc';dest.write_bytes(out)
assert QResource.registerResource(str(dest),'/candidate')
for p,data in expected.items():
 f=QFile(':/candidate'+p[1:]);assert f.open(QIODevice.ReadOnly) and bytes(f.readAll())==data,p
(root/'control-preview-manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(out).hexdigest(),'changed':sorted(expected)},indent=2))
print('Prepared',len(expected),'preview resources')
