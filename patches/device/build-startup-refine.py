from pathlib import Path
import hashlib,struct,json,pefile
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');data=bytearray(target.read_bytes()); h=lambda b:hashlib.sha256(b).hexdigest();before=h(data);assert before=='de73710c4ea35477d809cbd94089621c037d289bcebfca8d60a0d99e20764855';p=pefile.PE(data=data,fast_load=True)
def patch(a,b,expect):
 o=p.get_offset_from_rva(a-0x140000000);assert data[o:o+len(expect)]==expect,(hex(a),data[o:o+len(expect)].hex());data[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,d):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',d-self.start-len(self.code)-len(v)-4))
 def call(self,d):self.rel('ff15',d)
# LogoView receives a zero QSize: its children remain alive but are clipped.
zero=0x140086d00;patch(zero,b'\0'*8,b'\xcc'*8);a=0x1404b16a7;patch(a,b'\x48\x8d\x15'+struct.pack('<i',zero-a-7),bytes.fromhex('488d15da410802'))
# Paint the real QProgressBar value as two antialiased capsules.
five=0x140086d10;patch(five,struct.pack('<d',5),b'\xcc'*8)
g=Code(0x140087000);g.emit('53564881ecb8000000488bd9')
g.emit('488d5310488d4c2450');g.call(0x142eac678)
g.emit('488d4c2450ba0100000041b801000000');g.call(0x142eac640) # render hint
g.emit('488d4c2450ba00000000');g.call(0x142eac258) # no pen
for col in (0xff292032,0xffa787d5):
 g.emit('488d4c2470ba'+struct.pack('<I',col).hex());g.call(0x142eabb00)
 g.emit('488d8c2480000000488d54247041b801000000');g.call(0x142eac5f0)
 g.emit('488d4c2450488d942480000000');g.call(0x142eac250)
 g.emit('488d8c2480000000');g.call(0x142eac5e8)
 if col==0xffa787d5:
  g.emit('488bcb');g.call(0x142eadaf0);g.emit('69c04001000099b964000000f7f989c6')
 else:g.emit('be40010000')
 g.emit('c74424200a000000');g.rel('f20f1005',five);g.emit('f20f11442428f20f11442430c744243800000000488d4c245033d24533c0448bce');g.call(0x142eac1b8)
g.emit('488d4c2450');g.call(0x142eac670);g.emit('4881c4b80000005e5bc3');patch(g.start,g.code,b'\xcc'*len(g.code));patch(0x1425352e0,struct.pack('<Q',g.start),struct.pack('<Q',0x141fc7c6e))
(root/'MuMuNxDevice.startup-refined.exe').write_bytes(data);(root/'exe-startup-refined-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(data)}));print('built',h(data),len(g.code))

