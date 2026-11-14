from pathlib import Path
import hashlib,json,struct,pefile
r=Path('mumu-analysis/theme-work');target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='29334360a86e06adaf5ed277d3eb233c90a00b02594d643dd2abecebde8f44ef';(r/'MuMuNxDevice.before-settings-prune.exe').write_bytes(d);p=pefile.PE(data=d,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
 def direct(self,dest):self.rel('e8',dest)
# Network navigation entry: same hide-after-add helper used by other removed entries.
a=0x14094272f;patch(a,b'\xe8'+struct.pack('<i',0x14008b000-a-5)+b'\x90',bytes.fromhex('ff15e3c15602'))
# Hide WindowSizeAndPosSection immediately after its object name is assigned.
g=Code(0x14008d000);g.emit('534883ec20488bd9');g.call(0x142eaada8);g.emit('488bcb');g.call(0x142eaea70);g.emit('4883c4205bc3');patch(g.start,g.code,b'\xcc'*len(g.code))
a=0x14090e2bb;patch(a,b'\xe8'+struct.pack('<i',g.start-a-5)+b'\x90',bytes.fromhex('ff15e7ca5902'))
# For individual named controllers, locate the first NxSettingsExpander ancestor
# of their existing control, and hide that card; limits traversal to six parents.
name=0x14008d600;patch(name,b'NX::NxSettingsExpander\0',b'\xcc'*23)
f=Code(0x14008d100);f.emit('5356574883ec20488bd9');f.direct(0x14005d18e);f.emit('488bb3f80100004885f6');j0=len(f.code);f.emit('0f8400000000');f.emit('bf06000000');loop=len(f.code)
f.emit('488bce');f.call(0x142eaf050);f.emit('488bf04885f6');j1=len(f.code);f.emit('0f8400000000');f.emit('488bce');f.rel('488d15',name);f.emit('488b06ff50084885c0');j2=len(f.code);f.emit('0f8500000000');f.emit('ffcf');j3=len(f.code);f.emit('0f8500000000');j4=len(f.code);f.emit('e900000000');found=len(f.code);f.emit('488bce');f.call(0x142eaea70);end=len(f.code);f.emit('4883c4205f5e5bc3')
for j,dest,at,n in [(j0,end,2,6),(j1,end,2,6),(j2,found,2,6),(j3,loop,2,6),(j4,end,1,5)]:f.code[j+at:j+at+4]=struct.pack('<i',dest-(j+n))
patch(f.start,f.code,b'\xcc'*len(f.code))
for a,old in [(0x14096206d,'e81cb16fff'),(0x1409778f6,'e893586eff'),(0x1409825cd,'e8bcab6dff'),(0x14099b680,'e8091b6cff')]:patch(a,b'\xe8'+struct.pack('<i',f.start-a-5),bytes.fromhex(old))
(r/'MuMuNxDevice.settings-prune.exe').write_bytes(d);(r/'exe-settings-prune-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('built',h(d),'ancestor hook',len(f.code))
