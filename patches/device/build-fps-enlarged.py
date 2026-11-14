from pathlib import Path
import pefile,hashlib,struct,json
r=Path('mumu-analysis/theme-work');target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\device\libRenderer.dll');d=bytearray(target.read_bytes());h=lambda b:hashlib.sha256(b).hexdigest();before=h(d);assert before=='bc17b9e16d99786bf5b7dc01477bc5f4d898cc52255ed4b1350e4292fae20c66';(r/'libRenderer.before-fps-enlarge.dll').write_bytes(d);p=pefile.PE(data=d);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex(),e.hex());d[o:o+len(b)]=b
# Increase digit bearing/advance and rendering size about 25%; preserve source textures.
res=next(e for e in p.DIRECTORY_ENTRY_RESOURCE.entries if str(e.name)=='BINARY');e=next(x for x in res.directory.entries if x.id==117).directory.entries[0].data.struct;off=p.get_offset_from_rva(e.OffsetToData);pos=off
for _ in range(10):
 vals=struct.unpack_from('<5i',d,pos);assert vals[3]>0 and vals[4]>0
 struct.pack_into('<3i',d,pos,*[round(v*1.25) for v in vals[:3]]);pos+=20+vals[3]*vals[4]
patch(0x180002df0,struct.pack('<ffff',18.,18.,0.,0.),struct.pack('<ffff',14.,14.,0.,0.))
patch(0x180003400,struct.pack('<ffff',40.,52.,64.,21.),struct.pack('<ffff',36.,46.,56.,17.))
patch(0x18009f8e2,bytes.fromhex('b812000000'),bytes.fromhex('b80e000000'))
# Move the viewport further below Android status icons; preserve the 4px left inset.
patch(0x180006600,struct.pack('<ffff',-20.,20.,30.,0.),b'\xcc'*16)
for a,dest in [(0x18009eec5,0x180006600),(0x18009ee6f,0x180006604),(0x18009f686,0x180006608)]:
 o=p.get_offset_from_rva(a-base);old=bytes(d[o:o+8]);assert old[:3]==bytes.fromhex('f30f10');patch(a,old[:4]+struct.pack('<i',dest-(a+8)),old)
(r/'libRenderer.fps-enlarged.dll').write_bytes(d);(r/'fps-enlarged-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('candidate',h(d))
