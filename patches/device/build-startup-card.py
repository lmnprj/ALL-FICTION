from pathlib import Path
import hashlib,struct,json,pefile
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='c02a6fbf9f03fd35e824f70831045976b490bf9c588a49bdd655b9c7edd05b4e';(root/'MuMuNxDevice.before-startup-card.exe').write_bytes(d);p=pefile.PE(data=d,fast_load=True)
def patch(a,b,e):
 o=p.get_offset_from_rva(a-0x140000000);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
# Align progress with Qt's 0..1000 range; 4px rather than 10px high.
patch(0x140086829,bytes.fromhex('ba04000000'),bytes.fromhex('ba0a000000'))
# Background and central card.
g=Code(0x140089000);g.emit('534881ec10010000488bd9')
g.emit('488d5310488d4c2450');g.call(0x142eac678);g.emit('488bcb488d542460');g.call(0x142eaeb30)
g.emit('488d8c2480000000ba0f0409ff');g.call(0x142eabb00)
g.emit('488d4c2450488d5424604c8d842480000000');g.call(0x142eac1a8)
# Store centered panel x/y and wordmark rect.

g.emit('488bcb');g.call(0x142eaf078);g.emit('2dae010000d1f8898424d0000000')
g.emit('488bcb');g.call(0x142eaf070);g.emit('83e832d1f8898424d4000000') # y=(height-50)/2, then offset
# panel y = height/2 - 50
g.emit('8b8424d400000083e819898424d4000000')
# brush for card and border
g.emit('488d8c2480000000ba2c0d1cff');g.call(0x142eabb00);g.emit('488d8c2490000000488d94248000000041b801000000');g.call(0x142eac5f0);g.emit('488d4c2450488d942490000000');g.call(0x142eac250);g.emit('488d8c2490000000');g.call(0x142eac5e8)
g.emit('488d8c2480000000ba743b9fff');g.call(0x142eabb00);g.emit('488d4c2450488d942480000000');g.call(0x142eac178)
g.emit('c744242064000000');g.rel('f20f1005',0x140089e10);g.emit('f20f11442428f20f11442430c744243800000000488d4c24508b9424d0000000448b8424d400000041b9ae010000');g.call(0x142eac1b8)
# Text left aligned inside panel.
g.emit('488d8c2480000000bae9e2f2ff');g.call(0x142eabb00);g.emit('488d4c2450488d942480000000');g.call(0x142eac178)
g.emit('488d8c24a0000000');g.call(0x142eb29e8);g.emit('488d8c24a0000000ba4b000000');g.call(0x142eabb90);g.emit('488d8c24a0000000ba10000000');g.call(0x142eabca0);g.emit('488d4c2450488d9424a0000000');g.call(0x142eac1c8)
g.emit('8b8424d000000083c0188944246081c07d010000894424688b8424d400000083c0108944246483c01e8944246c')
g.rel('488d0d',0x140084c30);g.emit('ba0b000000');g.call(0x142eaabc0);g.emit('48898424b0000000')
g.emit('488d4c2450488d54246041b8810000004c8d8c24b000000048c744242000000000');g.call(0x142eac1b0)
g.emit('488d8c24b0000000');g.call(0x142eaab78);g.emit('488d8c24a0000000');g.call(0x142eac458);g.emit('488d4c2450');g.call(0x142eac670);g.emit('4881c4100100005bc3')
patch(g.start,g.code,b'\xcc'*len(g.code));patch(0x14251ac58,struct.pack('<Q',g.start),struct.pack('<Q',0x140086000))
for a,v in [(0x140089e00,0.5),(0x140089e08,1.0),(0x140089e10,12.0),(0x140089e18,318.0)]:patch(a,struct.pack('<d',v),b'\xcc'*8)
# Widget paint: true 0..1000 progress, gradient fill; Qt animates the value.
f=Code(0x140089800);f.emit('53564881ec98010000488bd9');f.emit('488d5310488d4c2450');f.call(0x142eac678);f.emit('488d4c2450ba0100000041b801000000');f.call(0x142eac640);f.emit('488d4c245033d2');f.call(0x142eac258)
def brush(color):
 f.emit('488d8c2480000000ba'+struct.pack('<I',color).hex());f.call(0x142eabb00);f.emit('488d8c24d0000000488d94248000000041b801000000');f.call(0x142eac5f0);f.emit('488d4c2450488d9424d0000000');f.call(0x142eac250);f.emit('488d8c24d0000000');f.call(0x142eac5e8)
def rect(width):
 f.emit('c744242004000000');f.rel('f20f1005',0x140086d10);f.emit('f20f11442428f20f11442430c744243800000000488d4c2450ba010000004533c0'+width);f.call(0x142eac1b8)
brush(0xff382441);rect('41b93e010000')
f.emit('488bcb');f.call(0x142eadaf0);f.emit('85c0');j=len(f.code);f.emit('0f8e00000000');f.emit('69c03e01000099b9e8030000f7f989c6')
# QLinearGradient(0, 0, 318, 0)
f.emit('660f57c9660f57d2');f.rel('f20f101d',0x140089e18);f.emit('48c744242000000000488d8c2490000000');f.call(0x142eac1e0)
for color,pos in [(0xff6925a4,None),(0xffaa67db,0x140089e00),(0xffe6ccfa,0x140089e08)]:
 f.emit('488d8c2480000000ba'+struct.pack('<I',color).hex());f.call(0x142eabb00);f.emit('488d8c2490000000');f.emit('660f57c9') if pos is None else f.rel('f20f100d',pos);f.emit('4c8d842480000000');f.call(0x142eac1e8)
f.emit('488d8c24d0000000488d942490000000');f.call(0x142eac1f0);f.emit('488d4c2450488d9424d0000000');f.call(0x142eac250);f.emit('488d8c24d0000000');f.call(0x142eac5e8);rect('448bce');f.emit('488d8c2490000000');f.call(0x142eac1d8)
f.code[j+2:j+6]=struct.pack('<i',len(f.code)-(j+6));f.emit('488d4c2450');f.call(0x142eac670);f.emit('4881c4980100005e5bc3');patch(f.start,f.code,b'\xcc'*len(f.code));patch(0x1425352e0,struct.pack('<Q',f.start),struct.pack('<Q',0x140088000))
(root/'MuMuNxDevice.startup-card.exe').write_bytes(d);(root/'exe-startup-card-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('built',h(d),'background',len(g.code),'progress',len(f.code))
