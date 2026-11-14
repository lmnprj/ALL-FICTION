from pathlib import Path
import hashlib,json,struct,pefile
r=Path('mumu-analysis/theme-work');target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='cbf6bd28492eba9df8604d25143530156644fc3a54083366af90377faeaa0021';(r/'MuMuNxDevice.before-settings-switch.exe').write_bytes(d);p=pefile.PE(data=d,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
g=Code(0x14008c000);g.emit('534881ecc0000000488bd9')
g.emit('488bcb');g.call(0x142eb2fd8);g.emit('0fb6c0898424a0000000')
g.emit('488bcb');g.call(0x142eaf078);g.emit('898424a4000000')
g.emit('488bcb');g.call(0x142eaf070);g.emit('898424a8000000')
g.emit('488d5310488d4c2450');g.call(0x142eac678);g.emit('488d4c2450ba0100000041b801000000');g.call(0x142eac640);g.emit('488d4c245033d2');g.call(0x142eac258)
# Track colour depends on actual switch state.
g.emit('83bca4a000000000') if False else None
g.emit('83bca424a000000000') if False else None
g.emit('83bc24a000000000b8423348ffbadd81acff0f45c2')
g.emit('488d8c24800000008bd0');g.call(0x142eabb00)
def applybrush():
 g.emit('488d8c2490000000488d94248000000041b801000000');g.call(0x142eac5f0);g.emit('488d4c2450488d942490000000');g.call(0x142eac250);g.emit('488d8c2490000000');g.call(0x142eac5e8)
applybrush();g.emit('8b8424a800000083e80289442420');g.rel('f20f1005',0x140089e10);g.emit('f20f11442428f20f11442430c744243800000000488d4c2450ba0100000041b801000000448b8c24a40000004183e902');g.call(0x142eac1b8)
# White thumb, on right or left; renderer is local to switch widget.
g.emit('488d8c2480000000baece5f3ff');g.call(0x142eabb00);applybrush();g.emit('8b8424a800000083e8068944242083bc24a000000000ba0300000074118b9424a40000002b9424a800000083c203488d4c245041b803000000448b8c24a80000004183e906');g.call(0x142eabf00)
g.emit('488d4c2450');g.call(0x142eac670);g.emit('4881c4c00000005bc3');patch(g.start,g.code,b'\xcc'*len(g.code));patch(0x142590030,struct.pack('<Q',g.start),struct.pack('<Q',0x141fc871e))
(r/'MuMuNxDevice.settings-switch.exe').write_bytes(d);(r/'exe-settings-switch-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('candidate',h(d),'code',len(g.code))

