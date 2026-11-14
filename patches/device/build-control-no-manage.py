from pathlib import Path
import hashlib,json,struct,pefile
root=Path(__file__).resolve().parent
source=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe')
data=bytearray(source.read_bytes());before=hashlib.sha256(data).hexdigest()
assert before=='aa43c85bf49de23fa2927ee43cbca2f822476f38ac389020bd47940f0f0e5012'
pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
site=0x14052c942;helper=0x14008e000;offset=pe.get_offset_from_rva(site-base);old=bytes(data[offset:offset+6])
assert old[:2]==b'\xff\x15' and site+6+struct.unpack('<i',old[2:])[0]==0x142eae918
helper_offset=pe.get_offset_from_rva(helper-base)
assert data[helper_offset:helper_offset+8]==bytes.fromhex('534883ec20488bda')
new=b'\xe8'+struct.pack('<i',helper-site-5)+b'\x90';data[offset:offset+6]=new
candidate=root/'MuMuNxDevice.control-no-manage-candidate.exe';candidate.write_bytes(data)
(root/'control-no-manage-manifest.json').write_text(json.dumps({'source_sha256':before,'candidate_sha256':hashlib.sha256(data).hexdigest(),'offset':hex(offset),'before':old.hex(),'after':new.hex()},indent=2))
print('Candidate ready; changed only the manage button layout call.')
