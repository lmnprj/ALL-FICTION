from pathlib import Path
import hashlib,struct,json,pefile
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='af8d459f62ea5cba8b39e84e20aa64787d3e67dd7541b015eac390a7f04dcfff';(root/'MuMuNxDevice.before-startup-animation.exe').write_bytes(d);p=pefile.PE(data=d,fast_load=True)
def patch(a,b,e):
 o=p.get_offset_from_rva(a-0x140000000);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
 def direct(self,dest):self.rel('e8',dest)
# Disable legacy blue glow, preserving its layout and lifecycle.
patch(0x1404b1393,b'\x32\xd2',bytes.fromhex('b201'))
# Widget-owned repaint timer, only active during boot.
t=Code(0x140088600);t.emit('53564883ec58488bf3');t.call(0x142eaab78) # original QString destructor, rsi=progress
t.emit('b940000000');t.direct(0x140005c77);t.emit('4885c0');j=len(t.code);t.emit('7400');t.emit('488bd8488bc8488bd6');t.call(0x142eaa4a8)
t.emit('488d4c2438488bd3');t.rel('4c8d05',0x140084c00);t.emit('4c8bce');t.rel('488d05',0x140084c10);t.emit('4889442420c744242800000000');t.call(0x142eaa9e8);t.emit('488d4c2438');t.call(0x142eaada0);t.emit('488bcbba21000000');t.call(0x142eaa490);t.code[j+1]=len(t.code)-(j+2);t.emit('4883c4585e5bc3');patch(t.start,t.code,b'\xcc'*len(t.code))
a=0x140086869;patch(a,b'\xe8'+struct.pack('<i',t.start-a-5)+b'\x90',bytes.fromhex('ff150943e202'))
# Progress painter, two rounded capsules and a small animated light inside the filled area.
g=Code(0x140088000);g.emit('53564881ecb8000000488bd9');g.emit('488d5310488d4c2450');g.call(0x142eac678);g.emit('488d4c2450ba0100000041b801000000');g.call(0x142eac640);g.emit('488d4c245033d2');g.call(0x142eac258)
def brush(color):
 g.emit('488d4c2470ba'+struct.pack('<I',color).hex());g.call(0x142eabb00);g.emit('488d8c2480000000488d54247041b801000000');g.call(0x142eac5f0);g.emit('488d4c2450488d942480000000');g.call(0x142eac250);g.emit('488d8c2480000000');g.call(0x142eac5e8)
def rounded(xhex,widthhex):
 g.emit('c74424200a000000');g.rel('f20f1005',0x140086d10);g.emit('f20f11442428f20f11442430c744243800000000488d4c2450'+xhex+'4533c0'+widthhex);g.call(0x142eac1b8)
brush(0xff292032);g.emit('be3e010000');rounded('ba01000000','448bce')
brush(0xffa787d5);g.emit('488bcb');g.call(0x142eadaf0);g.emit('69c03e01000099b964000000f7f989c6');rounded('ba01000000','448bce')
# millisecond phase travels from left to right; only paint if inside filled portion

g.call(0x142eaa740);g.emit('31d2b96809000048f7f1488bc269c02c01000031d2b968090000f7f1ffc0898424a00000008d481239f1');j=len(g.code);g.emit('0f8700000000')
brush(0x88f5e8ff);rounded('8b9424a0000000','41b912000000');g.code[j+2:j+6]=struct.pack('<i',len(g.code)-(j+6))
g.emit('488d4c2450');g.call(0x142eac670);g.emit('4881c4b80000005e5bc3');patch(g.start,g.code,b'\xcc'*len(g.code));patch(0x1425352e0,struct.pack('<Q',g.start),struct.pack('<Q',0x140087000))
(root/'MuMuNxDevice.startup-animation.exe').write_bytes(d);(root/'exe-startup-animation-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('built',h(d),'painter',len(g.code),'timer',len(t.code))

