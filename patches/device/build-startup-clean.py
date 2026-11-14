from pathlib import Path
import hashlib,struct,json,pefile
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='6d9e3caf3a219639790ed8aeb5a2f86b872c56582a30c85c118c87f573fc29cd';p=pefile.PE(data=d,fast_load=True)
def patch(a,b,e):
 o=p.get_offset_from_rva(a-0x140000000);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
start=0x140087400;c=bytearray()
def emit(x):c.extend(bytes.fromhex(x))
def rel(op,dest):
 v=bytes.fromhex(op);c.extend(v+struct.pack('<i',dest-start-len(c)-len(v)-4))
emit('534883ec20488bd9');rel('e8',0x14004d6ad)
emit('488b4b30');rel('ff15',0x142eaea70)
emit('488b4b38');rel('ff15',0x142eaea70)
emit('4883c4205bc3');patch(start,c,b'\xcc'*len(c));a=0x1404b1ab1;patch(a,b'\xe8'+struct.pack('<i',start-a-5),bytes.fromhex('e8f7bbb9ff'))
(root/'MuMuNxDevice.startup-clean.exe').write_bytes(d);(root/'exe-startup-clean-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print(h(d))
