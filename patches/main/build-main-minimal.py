from pathlib import Path
import hashlib,json,pefile,struct
root=Path(__file__).resolve().parent
src=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuNxMain.exe')
data=bytearray(src.read_bytes());before=hashlib.sha256(data).hexdigest()
assert before=='45d6b561a26eacc1466b559a377e80c1f2927172037241a4565862b69af98759'
pe=pefile.PE(data=data,fast_load=True);pe.parse_data_directories(directories=[3]);base=pe.OPTIONAL_HEADER.ImageBase;changes=[]
def off(a):return pe.get_offset_from_rva(a-base)
def patch(a,old,new,label):
 o=off(a);assert len(old)==len(new) and data[o:o+len(old)]==old,(hex(a),bytes(data[o:o+len(old)]).hex(),old.hex());data[o:o+len(new)]=new
 changes.append({'address':hex(a),'before':old.hex(),'after':new.hex(),'purpose':label})
helper=0x140080000;add=0x1427b4550;hide=0x1427b46a8
assert not any(base+e.struct.BeginAddress < helper+40 and base+e.struct.EndAddress > helper for e in pe.DIRECTORY_ENTRY_EXCEPTION)
stub=bytearray.fromhex('53 48 83 ec 20 48 8b da')
def call(dest):stub.extend(b'\xff\x15'+struct.pack('<i',dest-helper-len(stub)-6))
call(add);stub.extend(bytes.fromhex('48 8b cb'));call(hide);stub.extend(bytes.fromhex('48 83 c4 20 5b c3'))
patch(helper,b'\xcc'*len(stub),bytes(stub),'Add widget then hide it, preserving its object and signals')
for site,label in [
 (0x140295b3c,'avatar'),(0x140296066,'title menu'),
 (0x14029a18b,'batch'),(0x14029a6bc,'arrange'),
 (0x14029ac4f,'search'),(0x14029b1d3,'sort'),
 (0x14029bb56,'display mode'),(0x1403447b6,'instance menu')]:
 old=bytes(data[off(site):off(site)+6]);assert old[:2]==b'\xff\x15' and site+6+struct.unpack('<i',old[2:])[0]==add,(hex(site),old.hex())
 patch(site,old,b'\xe8'+struct.pack('<i',helper-site-5)+b'\x90',label)
# The sidebar owns only navigation/remote/feedback; preserve objects but remove its width.
patch(0x140291818,bytes.fromhex('ba48000000'),bytes.fromhex('ba00000000'),'collapse sidebar')
dst=root/'MuMuNxMain.minimal-candidate.exe';dst.write_bytes(data)
(root/'main-minimal-manifest.json').write_text(json.dumps({'source_sha256':before,'candidate_sha256':hashlib.sha256(data).hexdigest(),'changes':changes},indent=2))
print('Built',dst,'with',len(changes),'address-checked edits')
