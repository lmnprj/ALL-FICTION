from pathlib import Path
import hashlib, json, struct
import pefile

root=Path(__file__).resolve().parent
source=root/'MuMuNxDevice.before-wave.exe'
data=bytearray(source.read_bytes()); digest=hashlib.sha256(data).hexdigest()
assert digest=='e1a92312fb65e31f4e3a8d22b9fe7354fe93e9b0e573ece9e2853d85b24fb2d5'
assert hashlib.sha256(Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe').read_bytes()).hexdigest()=='6a5dd573e3e81ae9d1b0a4b277237e4f350c9315191d53cdd12e9861486051b3'
pe=pefile.PE(data=data,fast_load=True)
def offset(a):return pe.get_offset_from_rva(a-0x140000000)
def patch(a,b,expect=None):
 o=offset(a)
 if expect is not None:assert data[o:o+len(expect)]==expect,(hex(a),data[o:o+len(expect)].hex())
 data[o:o+len(b)]=b

class Code:
 def __init__(self,start):self.start=start;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,target):
  b=bytes.fromhex(op);self.code.extend(b+struct.pack('<i',target-self.start-len(self.code)-len(b)-4))
 def call(self,target):self.rel('ff15',target)
 def direct(self,target):self.rel('e8',target)
 def rcx(self,x):self.emit(('488d4c24'+f'{x:02x}') if x<128 else ('488d8c24'+struct.pack('<I',x).hex()))
 def rdx(self,x):self.emit(('488d5424'+f'{x:02x}') if x<128 else ('488d9424'+struct.pack('<I',x).hex()))
 def r8(self,x):self.emit(('4c8d4424'+f'{x:02x}') if x<128 else ('4c8d8424'+struct.pack('<I',x).hex()))

# A parent-owned QTimer asks only the title widget to repaint every 20 ms.
t=Code(0x140084800)
t.emit('53564883ec58488bdf')             # save widget from constructor's rdi
t.call(0x142eae928)                     # original addStretch(layout, 0)
t.emit('b940000000');t.direct(0x140005c77)
t.emit('4885c0');j=len(t.code);t.emit('7400')
t.emit('488bf0488bc8488bd3');t.call(0x142eaa4a8) # QTimer(parent)
t.rcx(0x38);t.emit('488bd6');t.rel('4c8d05',0x140084c00);t.emit('4c8bcb')
t.rel('488d05',0x140084c10);t.emit('4889442420c744242800000000')
t.call(0x142eaa9e8)                    # QObject::connect(timeout, update)
t.rcx(0x38);t.call(0x142eaada0)
t.emit('488bceba14000000');t.call(0x142eaa490) # start(20 ms)
t.code[j+1]=len(t.code)-(j+2)
t.emit('4883c4585e5bc3')
assert len(t.code)<0x300
patch(t.start,t.code,b'\xcc'*len(t.code))
patch(0x140084c00,b'2timeout()\0',b'\xcc'*11)
patch(0x140084c10,b'1update()\0',b'\xcc'*10)
hook=0x14042d952
patch(hook,b'\xe8'+struct.pack('<i',t.start-hook-5)+b'\x90',bytes.fromhex('ff15d00fa802'))

# Paint a pale grey wave across the title using the normal Qt painter.
g=Code(0x140084900);title=0x140084c30;half=0x140084c40;one=0x140084c48;left=0x140084c50;right=0x140084c58
g.emit('534881ec00010000488bd9')        # rbx=widget; 256-byte stack
g.emit('488d5310');g.rcx(0x30);g.call(0x142eac678)
g.emit('488bcb');g.rdx(0x40);g.call(0x142eaeb30)
g.emit('488bcb');g.call(0x142eaf050);g.emit('488bc8');g.call(0x142eaf078);g.emit('89442428')
g.emit('488bcb');g.call(0x142eaeb50);g.emit('f7d88944244003442428ffc889442448')
g.call(0x142eaa740)                    # ms since epoch
g.emit('31d2b97017000048f7f1488bc2483db80b0000760bb970170000482bc8488bc1488bc8480fafc04869c0a0000000ba28230000482bd1482bd1480fafc231d248b9004e53490600000048f7f1') # eased ping-pong phase
g.emit('8b4c2440034c2448d1f983e97003c1') # centered wave start
g.emit('660f57c9f20f2ac8')             # xmm1=x1
g.emit('660f57d283c040660f57dbf20f2ad8') # xmm2=0, xmm3=x1+64
g.emit('48c744242000000000');g.rcx(0x70);g.call(0x142eac1e0)
for color,position in [(0xffeee8f2,None),(0xffb5aeba,left),(0xffffffff,half),(0xffb5aeba,right),(0xffeee8f2,one)]:
 g.rcx(0x50);g.emit('ba'+struct.pack('<I',color).hex());g.call(0x142eabb00)
 g.rcx(0x70)
 if position is None:g.emit('660f57c9')
 else:g.rel('f20f100d',position)
 g.r8(0x50);g.call(0x142eac1e8)
g.rcx(0xb0);g.rdx(0x70);g.call(0x142eac1f0)
g.rcx(0xb8);g.rdx(0xb0);g.rel('f20f1015',one);g.emit('41b901000000c744242010000000c744242840000000');g.call(0x142eac5a8)
g.rcx(0x30);g.rdx(0xb8);g.call(0x142eac668);g.rcx(0xb8);g.call(0x142eac688);g.rcx(0xb0);g.call(0x142eac5e8)
g.rcx(0x60);g.call(0x142eb29e8);g.rcx(0x60);g.emit('ba57000000');g.call(0x142eabb90);g.rcx(0x60);g.emit('ba10000000');g.call(0x142eabca0);g.rcx(0x30);g.rdx(0x60);g.call(0x142eac1c8)
g.rel('488d0d',title);g.emit('ba0b000000');g.call(0x142eaabc0);g.emit('4889442468')
g.rcx(0x30);g.rdx(0x40);g.emit('41b8840000004c8d4c2468');g.emit('48c744242000000000');g.call(0x142eac1b0)
g.rcx(0x68);g.call(0x142eaab78);g.rcx(0x60);g.call(0x142eac458);g.rcx(0x70);g.call(0x142eac1d8);g.rcx(0x30);g.call(0x142eac670);g.emit('4881c4000100005bc3')
assert len(g.code)<0x300
patch(g.start,g.code,b'\xcc'*len(g.code))
patch(title,b'ALL FICTION\0',b'\xcc'*12)
patch(half,struct.pack('<d',0.5),b'\xcc'*8);patch(one,struct.pack('<d',1.0),b'\xcc'*8);patch(left,struct.pack('<d',0.35),b'\xcc'*8);patch(right,struct.pack('<d',0.65),b'\xcc'*8)
slot=0x14251ede0+0xd8;patch(slot,struct.pack('<Q',g.start),struct.pack('<Q',0x140084400))
out=root/'MuMuNxDevice.title-wave-bold.exe';out.write_bytes(data)
m={'source_sha256':'6a5dd573e3e81ae9d1b0a4b277237e4f350c9315191d53cdd12e9861486051b3','patched_sha256':hashlib.sha256(data).hexdigest()}
(root/'exe-theme-wave-bold-manifest.json').write_text(json.dumps(m))
print(m,'timer bytes',len(t.code),'painter bytes',len(g.code))


