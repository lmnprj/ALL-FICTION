from pathlib import Path
import hashlib, struct, json
import pefile

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe')
EXPECTED = '295d19fca7ed25650237673a86bdefe8e7136e3da3000fbb4b575847f6a613a4'
original = SOURCE.read_bytes()
assert hashlib.sha256(original).hexdigest() == EXPECTED, 'Unexpected EXE; no changes made'
backup = ROOT / 'MuMuNxDevice.before-all-fiction.exe'
if not backup.exists(): backup.write_bytes(original)
assert backup.read_bytes() == original
p = pefile.PE(data=original)
base = p.OPTIONAL_HEADER.ImageBase
data = bytearray(original)
changes = []
def patch(va, new, label):
    off = p.get_offset_from_rva(va-base)
    old = bytes(data[off:off+len(new)])
    data[off:off+len(new)] = new
    changes.append(dict(label=label, va=hex(va), offset=off, before=old.hex(), after=new.hex()))
def read(va,n): return p.get_data(va-base,n)

# Reuse the original logo's paint method, retaining its prologue, unwind data,
# stack cookie and epilogue. The title bar invokes it instead of its base paint.
start = 0x14042e3c9
code = bytearray()
def emit(h): code.extend(bytes.fromhex(h))
def rel(op, target):
    b=bytes.fromhex(op); code.extend(b+struct.pack('<i',target-(start+len(code)+len(b)+4)))
def call(iat): rel('ff15',iat)
def rcx(slot): emit('488d4c24'+f'{slot:02x}')
def rdx(slot): emit('488d5424'+f'{slot:02x}')
def r8(slot): emit('4c8d4424'+f'{slot:02x}')
emit('488bd9')                         # rbx=this
emit('488d5310'); rcx(0x30); call(0x142eac678) # QPainter
emit('488bcb'); rdx(0x40); call(0x142eaeb30)   # QRect
rcx(0x50); emit('ba1a0e14ff'); call(0x142eabb00) # QColor #140e1a
rcx(0x30); rdx(0x40); r8(0x50); call(0x142eac1a8)
rcx(0x60); call(0x142eb29e8)            # bold 14 font
rcx(0x30); rdx(0x60); call(0x142eac1c8)
rcx(0x50); emit('baf8e9efff'); call(0x142eabb00) # lavender text
rcx(0x30); rdx(0x50); call(0x142eac178)
rel('488d0d',0x14042e5f0); emit('ba0b000000'); call(0x142eaabc0)
emit('4889442470')                     # QString
rcx(0x30); rdx(0x40); emit('41b884000000'); emit('4c8d4c2470')
emit('48c744242000000000'); call(0x142eac1b0) # centered drawText
rcx(0x70); call(0x142eaab78)
rcx(0x60); call(0x142eac458)
rcx(0x30); call(0x142eac670)
rel('e9',0x14042e8ec)
assert start+len(code)<0x14042e5f0
patch(start,code,'Native centered title painting')
patch(0x14042e5f0,b'ALL FICTION\0','Brand text')

# Existing vtable addresses already have DIR64 base relocation records.
title_slot=0x14251c7c0+0xd8
logo_slot=0x14251f030+0xd8
assert any(e.rva==title_slot-base for b in p.DIRECTORY_ENTRY_BASERELOC for e in b.entries)
assert any(e.rva==logo_slot-base for b in p.DIRECTORY_ENTRY_BASERELOC for e in b.entries)
base_paint=read(title_slot,8)
patch(title_slot,struct.pack('<Q',0x14042e390),'TitleBar custom paint virtual method')
patch(logo_slot,base_paint,'Remove old logo and device-name painter')
for va in [0x14042e17f,0x14042e1cf,0x14042ddbb]:
    patch(va,struct.pack('<I',0),'Remove old logo reserved width')

css=(b'#%1{background-color:#140e1a;}/*%2*/ '
     b'#TitleBar QPushButton,#TitleBar QToolButton{border:1px solid #40304f;border-radius:5px;}'
     b'#TitleBar QPushButton:hover,#TitleBar QToolButton:hover{background-color:#30203e;}'
     b'#kMuMuRemote{min-width:0px;max-width:0px;}')
cssva=0x14042e600
assert cssva+len(css)+1<0x14042e8ec
patch(cssva,css+b'\0','Embedded title-bar stylesheet')
for va in [0x14041a496,0x14041b213]:
    assert read(va,3)==bytes.fromhex('488d0d')
    patch(va+3,struct.pack('<i',cssva-(va+7)),'Use embedded title style')
    assert read(va-5,1)==b'\xba'
    patch(va-4,struct.pack('<I',len(css)),'Embedded style length')

assert len(data)==len(original)
out=ROOT/'MuMuNxDevice.all-fiction.exe'
out.write_bytes(data)
check=pefile.PE(data=data)
assert check.OPTIONAL_HEADER.AddressOfEntryPoint==p.OPTIONAL_HEADER.AddressOfEntryPoint
manifest=dict(source_sha256=EXPECTED,patched_sha256=hashlib.sha256(data).hexdigest(),changes=changes)
(ROOT/'exe-theme-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(output=str(out),sha256=manifest['patched_sha256'],modified_bytes=sum(a!=b for a,b in zip(original,data)),patches=len(changes))))
