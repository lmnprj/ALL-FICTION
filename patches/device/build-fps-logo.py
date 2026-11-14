from pathlib import Path
import struct,hashlib,json,pefile
r=Path('mumu-analysis/theme-work');t=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\device\libRenderer.dll');d=bytearray(t.read_bytes());h=lambda b:hashlib.sha256(b).hexdigest();before=h(d);assert before=='d7f3b95dbf808c35c8149b8dc70a94c77c87d08db20021db9ec9a360eba72261';(r/'libRenderer.before-fps-logo.dll').write_bytes(d);p=pefile.PE(data=d);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex(),e.hex());d[o:o+len(b)]=b
# Place counter at the left edge with 4 px margin.
patch(0x18009eed5,bytes.fromhex('31c990909090'),bytes.fromhex('8b4e084429c1'))
a=0x18009eee6;o=p.get_offset_from_rva(a-base);old=bytes(d[o:o+8]);patch(a,old[:4]+struct.pack('<i',0x1803f045a-(a+8)),old)
# Allocate inline logo after every digit count and retain the internal real FPS value.
patch(0x18009f4c0,bytes.fromhex('b1019090'),bytes.fromhex('0fb64e04'))
patch(0x18009f727,bytes.fromhex('41b30190'),bytes.fromhex('44225e04'))
patch(0x18009f730,bytes.fromhex('9090'),bytes.fromhex('7408'))
# Size of logo quad and space for 1, 2 or 3 digit FPS values.
patch(0x180002df0,struct.pack('<ffff',14.,14.,0.,0.),b'\xcc'*16)
patch(0x180003400,struct.pack('<ffff',36.,46.,56.,17.),b'\xcc'*16)
for a,dest in [(0x18009f665,0x180003408),(0x18009f66f,0x180003404),(0x18009f679,0x180003400),(0x18009f732,0x18000340c),(0x18009f912,0x180002df0)]:
 o=p.get_offset_from_rva(a-base);old=bytes(d[o:o+8]);assert old[0:2] in (b'\xf3\x0f',b'\x0f\x59'),(hex(a),old.hex());patch(a,old[:4]+struct.pack('<i',dest-(a+8)),old)
patch(0x18009f8e2,bytes.fromhex('b80e000000'),bytes.fromhex('b809000000'))
# Resource 117: 10 single-channel digit bitmaps followed by an RGBA inline logo.
res=next(e for e in p.DIRECTORY_ENTRY_RESOURCE.entries if str(e.name)=='BINARY');entry=next(x for x in res.directory.entries if x.id==117).directory.entries[0].data.struct;off=p.get_offset_from_rva(entry.OffsetToData);size=entry.Size;original=bytes(d[off:off+size]);new=bytearray(original);g=(r/'fps-bold-glyphs.bin').read_bytes();logo=(r/'fps-logo-rgba.bin').read_bytes();assert len(logo)==7040;pos=0;gp=0
for i in range(10):
 hdr=struct.unpack_from('<5i',new,pos);n=hdr[3]*hdr[4];new[pos+20:pos+20+n]=g[gp:gp+n];gp+=n;pos+=20+n
assert gp==len(g) and pos==4465 and struct.unpack_from('<5i',new,pos)==(40,44,40,40,44);new[pos+20:pos+20+len(logo)]=logo;assert len(new)==size;d[off:off+size]=new
(r/'libRenderer.fps-logo.dll').write_bytes(d);(r/'fps-logo-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('candidate',h(d))
