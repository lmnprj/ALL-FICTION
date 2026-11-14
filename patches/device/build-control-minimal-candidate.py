from pathlib import Path
import hashlib,json,struct,pefile
root=Path(__file__).resolve().parent
source=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe')
data=bytearray(source.read_bytes());source_hash=hashlib.sha256(data).hexdigest()
assert source_hash=='e59ba53828b2a5e9b9b71692d173b9af110e291ac8c6e1d5829c46edab5b1c52'
pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;changes=[]
def off(a):return pe.get_offset_from_rva(a-base)
def patch(a,old,new,label):
 p=off(a);assert len(old)==len(new) and data[p:p+len(old)]==old,(hex(a),bytes(data[p:p+len(old)]).hex(),old.hex())
 data[p:p+len(new)]=new;changes.append({'address':hex(a),'before':old.hex(),'after':new.hex(),'purpose':label})
def indirect(calladdr):
 raw=bytes(data[off(calladdr):off(calladdr)+6]);assert raw[:2]==b'\xff\x15'
 return calladdr+6+struct.unpack('<i',raw[2:])[0],raw
class Code:
 def __init__(self,at):self.at=at;self.b=bytearray()
 def emit(self,x):self.b.extend(bytes.fromhex(x))
 def indirect(self,dest):self.b+=b'\xff\x15'+struct.pack('<i',dest-self.at-len(self.b)-6)
 def finish(self):patch(self.at,b'\xcc'*len(self.b),bytes(self.b),'UI-only helper')
def hook(a,dest,old,label):patch(a,old,b'\xe8'+struct.pack('<i',dest-a-5)+b'\x90',label)

# Retain objects and signals; hide only selected controls after they join layouts.
box,raw=indirect(0x140532941)
stub=Code(0x14008e000);stub.emit('53 48 83 ec 20 48 8b da');stub.indirect(box);stub.emit('48 8b cb');stub.indirect(0x142eaea70);stub.emit('48 83 c4 20 5b c3');stub.finish()
for a,label in [(0x140532941,'hide input tab selector'),(0x140530669,'hide text hint row'),(0x1405308ec,'hide transparency label'),(0x140530ad2,'hide transparency slider'),(0x140530c9d,'hide alternate transparency slider')]:
 target,old=indirect(a);assert target==box;hook(a,stub.at,old,label)
# Sensitivity section starts hidden; this prevents its later visibility update
# from displaying it. Keep the update's other logic untouched.
patch(0x140543ca9,bytes.fromhex('0fb6d3'),bytes.fromhex('31d290'),'keep operation section hidden')
patch(0x140543aba,bytes.fromhex('410fb6d6'),bytes.fromhex('31d29090'),'keep text hint row hidden')
# Buttons are still constructed/connected; hide share and instruction at return.
destructor,old=indirect(0x140534d1c)
s=Code(0x14008e100);s.emit('48 83 ec 28');s.indirect(destructor);s.emit('85 f6 74 0e 48 85 db 74 09 48 8b cb');s.indirect(0x142eaea70);s.emit('48 83 c4 28 c3');s.finish();hook(0x140534d1c,s.at,old,'hide instruction and share buttons')
# Only the editor bar's own background getter is replaced with a violet-black
# QColor; the global palette and its other consumers are not altered.
getter,old=indirect(0x1404e8eea)
bar=Code(0x14008e200);bar.emit('ba 211119ff');bar.b+=b'\xff\x25'+struct.pack('<i',0x142eabb00-bar.at-len(bar.b)-6);bar.finish();hook(0x1404e8eea,bar.at,old,'editor top bar background')
out=root/'MuMuNxDevice.control-minimal-candidate.exe';out.write_bytes(data)
manifest={'source_sha256':source_hash,'candidate_sha256':hashlib.sha256(data).hexdigest(),'changes':changes}
(root/'control-minimal-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Built candidate with',len(changes),'verified edits')
