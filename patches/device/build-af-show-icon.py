from pathlib import Path
import struct,hashlib,json,pefile
r=Path('mumu-analysis/theme-work');t=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(t.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='920df46e0db1e2bc63ad4df08ca94fdec4f328466e8553a34ecc551ecc2a1479';p=pefile.PE(data=d,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
 def direct(self,dest):self.rel('e8',dest)
img=(r/'af-embedded.png').read_bytes();c=Code(0x14008d700);c.emit('534883ec60488bd9');c.direct(0x14003e4dc)
c.emit('488d4c2430');c.rel('488d15',0x14008e000);c.emit('41b8'+struct.pack('<I',len(img)).hex());c.call(0x142ea8980)
c.emit('488d4c2440');c.call(0x142eac4c0);c.emit('488d4c2440488d5424304533c04533c9');c.call(0x142eac480)
c.emit('488d4c2450488d542440');c.call(0x142eac418);c.emit('488d4c2450');c.call(0x142eaf090);c.emit('488bcb488d542450');c.call(0x142ead608)
c.emit('488d4c2450');c.call(0x142eab850);c.emit('488d4c2440');c.call(0x142eac610);c.emit('488d4c2430');c.call(0x142eaab88);c.emit('4883c4605bc3');patch(c.start,c.code,b'\xcc'*len(c.code))
a=0x140307f61;patch(a,b'\xe8'+struct.pack('<i',c.start-a-5),bytes.fromhex('e87665d3ff'))
(r/'MuMuNxDevice.af-show-icon.exe').write_bytes(d);(r/'exe-af-show-icon-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print(h(d),len(c.code))
