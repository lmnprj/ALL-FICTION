from pathlib import Path
import pefile,struct,hashlib,json
root=Path(__file__).resolve().parent
src=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');data=bytearray(src.read_bytes());before=hashlib.sha256(data).hexdigest()
assert before=='f360fea2e39dfebfc236432829c2e7276c69688209e58d02477ddf70fb5c9846'
pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;addr=0x14008e100;pos=pe.get_offset_from_rva(addr-base)
old=bytes(data[pos:pos+35]);assert old==bytes.fromhex('4883ec28ff156ecae10285f6740e4885db7409488bcbff155409e2024883c428c3cccc')
code=bytearray.fromhex('48 83 ec 28')
def call(dest):code.extend(b'\xff\x15'+struct.pack('<i',dest-addr-len(code)-6))
call(0x142eaab78)
# The factory saves its type at [rbp+0x10] before reusing ESI.
code.extend(bytes.fromhex('83 7d 10 00 74 0e 48 85 db 74 09 48 8b cb'))
call(0x142eaea70);code.extend(bytes.fromhex('48 83 c4 28 c3'))
assert len(code)==len(old)
data[pos:pos+len(code)]=code
out=root/'MuMuNxDevice.control-edit-restore-candidate.exe';out.write_bytes(data)
(root/'control-edit-restore-manifest.json').write_text(json.dumps({'source_sha256':before,'candidate_sha256':hashlib.sha256(data).hexdigest(),'offset':hex(pos),'before':old.hex(),'after':code.hex()},indent=2))
print('Candidate restores the edit button while leaving other controls hidden.')
