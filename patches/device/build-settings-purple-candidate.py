from pathlib import Path
import hashlib,json,pefile,struct
root=Path('mumu-analysis/theme-work');target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='ab0e29a2f50a82f7b7283c30fbe1f0b2a43b5050e2ee27c93f61ba9054d0bb24';p=pefile.PE(data=d,fast_load=True)
def patch(a,b,e):
 o=p.get_offset_from_rva(a-0x140000000);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
# Replace the two dark-theme background getters only for SettingCenterWin.
start=0x14008a000;code=b'\xba'+struct.pack('<I',0xff140d1c)+b'\xff\x25'+struct.pack('<i',0x142eabb00-(start+11));patch(start,code,b'\xcc'*len(code))
for a,old in [(0x140903f0a,'ff1528e95a02'),(0x140903f78,'ff15bae85a02')]:patch(a,b'\xe8'+struct.pack('<i',start-a-5)+b'\x90',bytes.fromhex(old))
(root/'MuMuNxDevice.settings-purple-candidate.exe').write_bytes(d);(root/'exe-settings-purple-candidate-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('Prepared candidate',h(d))
