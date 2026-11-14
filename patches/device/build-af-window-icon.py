from pathlib import Path
import struct,hashlib,json,pefile
r=Path('mumu-analysis/theme-work');t=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(t.read_bytes());h=lambda b:hashlib.sha256(b).hexdigest();before=h(d);assert before=='c0755ebb430c6c3c3c7fe692dcb334a5abe3a06875af68e7cb4ccd3530579901';(r/'MuMuNxDevice.before-af-window-icon.exe').write_bytes(d);p=pefile.PE(data=d,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
 def direct(self,dest):self.rel('e8',dest)
img=(r/'af-embedded.png').read_bytes();assert len(img)<18000;imgaddr=0x14008e000;patch(imgaddr,img,b'\xcc'*len(img))
c=Code(0x14008d800);c.emit('53564881ec88000000488bd9488bf2') # rbx=&window, rsi=original icon
c.emit('488d4c2440');c.rel('488d15',imgaddr);c.emit('41b8'+struct.pack('<I',len(img)).hex());c.call(0x142ea8980)
c.emit('488d4c2450');c.call(0x142eac4c0)
c.emit('488d4c2450488d5424404533c04533c9');c.call(0x142eac480)
c.emit('488d4c2460488d542450');c.call(0x142eac418)
c.emit('488d4c2460');c.call(0x142eaf090)
c.emit('488b0b488d542460');c.call(0x142ead608)
c.emit('488d4c2470488d542460');c.call(0x142eac410)
c.emit('488bcb488d542470');c.direct(0x1403066d0)
c.emit('488bce');c.call(0x142eab850)
c.emit('488d4c2460');c.call(0x142eab850)
c.emit('488d4c2450');c.call(0x142eac610)
c.emit('488d4c2440');c.call(0x142eaab88)
c.emit('4881c4880000005e5bc3');patch(c.start,c.code,b'\xcc'*len(c.code))
for a,old in [(0x1404078fb,'e8d0edefff'),(0x140407a9d,'e82eecefff')]:patch(a,b'\xe8'+struct.pack('<i',c.start-a-5),bytes.fromhex(old))
(r/'MuMuNxDevice.af-window-icon.exe').write_bytes(d);(r/'exe-af-window-icon-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('candidate',h(d),'icon',len(img),'code',len(c.code))
