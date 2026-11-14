from pathlib import Path
import struct, hashlib, json, re
import pefile
R=Path(__file__).resolve().parent
src=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe')
original=src.read_bytes()
expected='88821d41e1e478ee07f4007d1ee9ddf0965ecc3322c6deb4f3fa21ed0cb5c5f3'
assert hashlib.sha256(original).hexdigest()==expected
backup=R/'MuMuNxDevice.before-v2.exe'
if not backup.exists():backup.write_bytes(original)
assert backup.read_bytes()==original
p=pefile.PE(data=original,fast_load=True);data=bytearray(original);changes=[]
def patch(va,b,label):
 o=p.get_offset_from_rva(va-0x140000000);old=bytes(data[o:o+len(b)]);data[o:o+len(b)]=b
 changes.append(dict(va=hex(va),offset=o,label=label,before=old.hex(),after=b.hex()))
def read(va,n):return p.get_data(va-0x140000000,n)

# Existing TabItem background painter: keep original frame/unwind/cookie.
start=0x14041d73f;code=bytearray()
def emit(h):code.extend(bytes.fromhex(h))
def rel(op,target):
 b=bytes.fromhex(op);code.extend(b+struct.pack('<i',target-(start+len(code)+len(b)+4)))
def call(iat):rel('ff15',iat)
def rcx(s):emit('488d4c24'+f'{s:02x}')
def rdx(s):emit('488d5424'+f'{s:02x}')
emit('488bf2488bf9') # rsi painter, rdi widget
emit('488bce33d2');call(0x142eac258) # no pen
emit('488bcf');rdx(0x30);call(0x142eaeb30)
# QRect: inset 6px horizontally and 5px vertically.
emit('83442430068344243405836c243806836c243c05')
# State colors: default, hover, selected.
emit('ba2b1c22ff80bf93000000007405ba3d2630ff80bf92000000007405ba4a2e3aff')
rcx(0x40);call(0x142eabb00)
rcx(0x50);rdx(0x40);emit('41b801000000');call(0x142eac5f0)
emit('488bce');rdx(0x50);call(0x142eac250)
rcx(0x50);call(0x142eac5e8)
emit('488bce');rdx(0x30);rel('f20f1015',0x14041d9f0);emit('0f28da')
emit('c744242000000000');call(0x142eac590)
rel('e9',0x14041dae4)
assert start+len(code)<0x14041d9e0
patch(start,code,'Floating rounded native tab backgrounds')
patch(0x14041d9f0,struct.pack('<d',9.0),'Nine-pixel tab corner radius')
patch(0x14041d9e0,b'ALL FICTION\0','Brand for home tab')
patch(0x14041df54,struct.pack('<i',0x14041d9e0-(0x14041df51+7)),'Home tab brand string')
patch(0x14041df81,b'\xe9'+struct.pack('<i',0x14041dfda-(0x14041df81+5)),'Prevent VM name overriding brand')

# Tool menu click connects directly to the existing settings slot.
assert read(0x140365744,3)==bytes.fromhex('488d05')
patch(0x140365747,struct.pack('<i',0x142514140-(0x140365744+7)),'Menu button opens device settings directly')
# Replace menu glyph references with existing built-in settings glyphs.
for va in [0x140445d4e,0x140445d64,0x140445dbd,0x140445dd3,0x140445e30,0x140445e46,0x140445ea3,0x140445eb9]:
 target=0x1425236e0 if va<0x140445e00 else 0x142523790
 assert read(va,3)==bytes.fromhex('488d0d')
 name=p.get_data(target-0x140000000,100).split(b'\0')[0]
 patch(va+3,struct.pack('<i',target-va-7),'Built-in settings icon')
 assert read(va-5,1)==b'\xba'
 patch(va-4,struct.pack('<I',len(name)),'Settings icon path length')

# Only construct menu/settings and ordinary window controls in this toolbar.
# Keyboard/game input engine is untouched. Missing button connections safely get null.
allow=bytearray()
for kind in [24,27,28,29]:allow.extend(bytes([0x83,0xfa,kind,0x74,0]))
allow.extend(bytes.fromhex('31c0c3'))
true_offset=len(allow);allow.extend(bytes.fromhex('b001c3'))
for pos in range(0,20,5):allow[pos+4]=true_offset-(pos+5)
patch(0x14044bb60,allow,'Disable construction of optional toolbar features')
patch(0x1404361f0,bytes.fromhex('4885c97405488b4140c331c0c3'),'Null-safe optional toolbar button lookup')

css=(b'#%1{background:#140e1a;}/*%2*/'
 b'#TitleBar QPushButton,#TitleBar QToolButton{background:#261a32;border:1px solid #493356;border-radius:9px;margin:5px 3px;}'
 b'#TitleBar QPushButton:hover,#TitleBar QToolButton:hover{background:#3b294b;}')
patch(0x14042e600,css+b'\0','Rounded floating toolbar button style')
for va in [0x14041a496,0x14041b213]:patch(va-4,struct.pack('<I',len(css)),'Updated embedded stylesheet length')
assert len(data)==len(original)
out=R/'MuMuNxDevice.all-fiction-v2.exe';out.write_bytes(data)
manifest=dict(source_sha256=expected,patched_sha256=hashlib.sha256(data).hexdigest(),changes=changes)
(R/'exe-theme-v2-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(output=str(out),sha256=manifest['patched_sha256'],patches=len(changes))))
