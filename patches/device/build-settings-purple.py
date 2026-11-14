from pathlib import Path
import hashlib,json,pefile,struct
r=Path('mumu-analysis/theme-work');src=r/'MuMuNxDevice.settings-purple-candidate.exe';d=bytearray(src.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();assert h(d)=='4ac42cb7aea0825219be7217c9e63383d13177b473af190ea513d4ca5d43a720'
p=pefile.PE(data=d,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex(),e.hex());d[o:o+len(b)]=b
# Per-setting-screen palette: do not change MuMu global colors.
for addr,color in [(0x14008a040,0xff241b30),(0x14008a080,0xffac81d5)]:
 code=b'\xba'+struct.pack('<I',color)+b'\xff\x25'+struct.pack('<i',0x142eabb00-(addr+11));patch(addr,code,b'\xcc'*len(code))
for a in [0x1409156ca,0x14098f86a,0x14099194a,0x14099483a,0x140997cea,0x14099ab8a,0x1409460a4,0x14094606e]:
 o=p.get_offset_from_rva(a-base);old=bytes(d[o:o+6]);assert old[:2]==b'\xff\x15';dst=0x14008a080 if a in (0x1409460a4,0x14094606e) else 0x14008a040;patch(a,b'\xe8'+struct.pack('<i',dst-a-5)+b'\x90',old)
(r/'MuMuNxDevice.settings-purple.exe').write_bytes(d);(r/'exe-settings-purple-manifest.json').write_text(json.dumps({'source_sha256':'ab0e29a2f50a82f7b7283c30fbe1f0b2a43b5050e2ee27c93f61ba9054d0bb24','patched_sha256':h(d)}));print(h(d))

