from pathlib import Path
import hashlib,json,pefile,struct
root=Path(__file__).resolve().parent;path=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_main\MuMuNxMain.exe')
data=bytearray(path.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();before=sha(data)
expected=json.loads((root/'main-task-brand-manifest.json').read_text())[0]['after'];assert before==expected
pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;site=0x140266fe5;brand=0x1400801c0
off=pe.get_offset_from_rva(site-base);old=bytes(data[off:off+7]);assert old[:3]==bytes.fromhex('4c8d05') and site+7+struct.unpack('<i',old[3:])[0]==0x141faedf8
assert pe.get_data(brand-base,12)==b'ALL FICTION\0';new=old[:3]+struct.pack('<i',brand-site-7);data[off:off+7]=new
dst=root/'MuMuNxMain.tray-brand-candidate.exe';dst.write_bytes(data)
(root/'main-tray-brand-manifest.json').write_text(json.dumps({'source_sha256':before,'candidate_sha256':sha(data),'offset':hex(off),'before':old.hex(),'after':new.hex()},indent=2))
print('Tray tooltip candidate built; only one string reference changed.')
