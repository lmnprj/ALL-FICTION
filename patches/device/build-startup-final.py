from pathlib import Path
import hashlib,struct,json,pefile
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='ae3320caa45dd99eca00855237d898ade4a42b97ef183e73f893f9e9e3b96cc3';p=pefile.PE(data=d,fast_load=True)
def patch(a,b,e):
 o=p.get_offset_from_rva(a-0x140000000);assert d[o:o+len(e)]==e;d[o:o+len(b)]=b
start=0x140087500;code=b'\x33\xd2\xe9'+struct.pack('<i',0x141fc8bd4-(start+7));patch(start,code,b'\xcc'*len(code));patch(0x142535908,struct.pack('<Q',start),struct.pack('<Q',0x141fc8bd4));(root/'MuMuNxDevice.startup-final.exe').write_bytes(d);(root/'exe-startup-final-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print(h(d))
