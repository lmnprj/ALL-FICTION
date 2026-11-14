from pathlib import Path
import pefile,hashlib,json,struct
root=Path('mumu-analysis/theme-work');p=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\device\libRenderer.dll');data=bytearray(p.read_bytes());h=lambda b:hashlib.sha256(b).hexdigest();orig=h(data);assert orig=='541b26e3935788817625201ca25aa20469b780c6ccba01123f8cc310cdcde994';(root/'libRenderer.before-fps-theme.dll').write_bytes(data);pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=pe.get_offset_from_rva(a-base);assert data[o:o+len(e)]==e,(hex(a),data[o:o+len(e)].hex(),e.hex());data[o:o+len(b)]=b
# Colours for FPS digits and insets live in unused executable-section alignment padding.
cave=0x1803f044a;values=struct.pack('<fffff',0.87,0.76,0.96,-4.0,4.0);patch(cave,values,b'\xcc'*len(values))
for j,a in enumerate([0x18009eff6,0x18009effe,0x18009f006,0x18009f010,0x18009f018,0x18009f020]):
 off=pe.get_offset_from_rva(a-base);old=bytes(data[off:off+8]);assert old[:3]==b'\xf3\x0f\x10';new=old[:4]+struct.pack('<i',cave+(j%3)*4-(a+8));patch(a,new,old)
for a,dest in [(0x18009ee6f,cave+16),(0x18009eec5,cave+12),(0x18009eee6,cave+12)]:
 off=pe.get_offset_from_rva(a-base);old=bytes(data[off:off+8]);assert old[:2]==b'\xf3\x0f';patch(a,old[:4]+struct.pack('<i',dest-(a+8)),old)
# Edit only FPS-specific fragment shader, keeping source string and binary offsets unchanged.
a=0x180c43828;o=pe.get_offset_from_rva(a-base);end=data.index(0,o);old=bytes(data[o:end]);assert old.count(b'0.08235, 0.09412, 0.125490, 0.7 * mix')==1;new=old.replace(b'0.08235, 0.09412, 0.125490, 0.7 * mix',b'0.10588, 0.05490, 0.160784, 0.9 * mix');assert len(new)==len(old);patch(a,new,old)
(root/'libRenderer.fps-purple.dll').write_bytes(data);(root/'fps-purple-manifest.json').write_text(json.dumps({'source_sha256':orig,'patched_sha256':h(data)}));print('candidate',h(data))
