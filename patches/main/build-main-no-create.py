from pathlib import Path
import hashlib,json,pefile,struct
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuNxMain.exe')
original=target.read_bytes();data=bytearray(original);sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(original)==json.loads((root/'main-tray-brand-manifest.json').read_text())['candidate_sha256']
p=pefile.PE(data=original,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase;site=0x140299c5a;helper=0x140080000;off=p.get_offset_from_rva(site-base)
old=bytes(data[off:off+6]);assert old[:2]==b'\xff\x15' and site+6+struct.unpack('<i',old[2:])[0]==0x1427b4550
assert p.get_data(helper-base,8)==bytes.fromhex('534883ec20488bda')
new=b'\xe8'+struct.pack('<i',helper-site-5)+b'\x90';data[off:off+6]=new
dst=root/'MuMuNxMain.no-create-candidate.exe';dst.write_bytes(data)
(root/'main-no-create-manifest.json').write_text(json.dumps({'source_sha256':sha(original),'candidate_sha256':sha(data),'offset':hex(off),'before':old.hex(),'after':new.hex()},indent=2))
print('Prepared candidate; creation button is hidden.')
