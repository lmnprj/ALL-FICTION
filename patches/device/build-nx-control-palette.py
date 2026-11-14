from pathlib import Path
import hashlib,json,pefile

root=Path(__file__).resolve().parent
source=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\nemu-ui-lib.dll')
original=source.read_bytes();pe=pefile.PE(data=original,fast_load=True);out=bytearray(original)
# NxColor's blue map is initialized from these distinct strings, confirmed in
# Ghidra's 0x1800410a0 initializer. Preserve the existing alpha bytes.
changes=[
 (0x180140498,b'#3485ff',b'#ac81d5'),
 (0x1801404a0,b'#01a4ff',b'#b983ed'),
 (0x1801404a8,b'#3485ffcc',b'#ac81d5cc'),
 (0x1801404b8,b'#3dbaff',b'#c99afa'),
 (0x1801404c0,b'#02bfff',b'#b983ed'),
 (0x1801404c8,b'#12d4ff',b'#d4aaff'),
 (0x1801404d0,b'#7addff',b'#e3c7ff'),
 (0x1801404d8,b'#3485ff2e',b'#ac81d52e'),
]
for addr,before,after in changes:
 assert len(before)==len(after)
 offset=pe.get_offset_from_rva(addr-pe.OPTIONAL_HEADER.ImageBase)
 assert bytes(out[offset:offset+len(before)])==before,(hex(addr),bytes(out[offset:offset+len(before)]))
 out[offset:offset+len(before)]=after
result=root/'nemu-ui-lib.nx-purple-candidate.dll';result.write_bytes(out)
(root/'nx-control-palette-manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(out).hexdigest(),'changes':[{'va':hex(a),'before':b.decode(),'after':c.decode()} for a,b,c in changes]},indent=2))
print('Prepared',result)
