from pathlib import Path
import hashlib,json,pefile
root=Path(__file__).resolve().parent
path=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_main\nemu-ui-lib.dll')
original=path.read_bytes();before=hashlib.sha256(original).hexdigest()
assert before=='4baf75936da263dce153e1822714913ca4e577f185d5adb646a2f2993abc46fb'
pe=pefile.PE(data=original,fast_load=True);out=bytearray(original)
colors=[(0x180140498,b'#3485ff',b'#ac81d5'),(0x1801404a0,b'#01a4ff',b'#b983ed'),(0x1801404a8,b'#3485ffcc',b'#ac81d5cc'),(0x1801404b8,b'#3dbaff',b'#c99afa'),(0x1801404c0,b'#02bfff',b'#b983ed'),(0x1801404c8,b'#12d4ff',b'#d4aaff'),(0x1801404d0,b'#7addff',b'#e3c7ff'),(0x1801404d8,b'#3485ff2e',b'#ac81d52e')]
for addr,old,new in colors:
 assert len(old)==len(new);pos=pe.get_offset_from_rva(addr-pe.OPTIONAL_HEADER.ImageBase);assert out[pos:pos+len(old)]==old;out[pos:pos+len(new)]=new
candidate=root/'nemu-ui-lib.main-purple-candidate.dll';candidate.write_bytes(out)
(root/'main-palette-manifest.json').write_text(json.dumps({'source_sha256':before,'candidate_sha256':hashlib.sha256(out).hexdigest(),'colors':[{'address':hex(a),'before':b.decode(),'after':c.decode()} for a,b,c in colors]},indent=2))
print('Prepared main-window purple palette.')
