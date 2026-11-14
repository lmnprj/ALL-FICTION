from pathlib import Path
import hashlib, json, struct, pefile

root = Path(__file__).resolve().parent
target = Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\nemu-ui-lib.dll')
original = target.read_bytes()
pe = pefile.PE(data=original)
out = bytearray(original)
names = {x.name.decode('ascii'): x.address for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
# Brand shades used by MuMu controls; warning/error colours remain untouched.
shades = {1:(185,131,237),3:(219,190,251),4:(185,131,237),5:(185,131,237),7:(166,112,216),8:(134,86,185),9:(107,66,157)}
changes = []
for number, (red, green, blue) in shades.items():
    name = f'?getBrand{number}@NemuColor@NemuUiLib@@SA?AVQColor@@XZ'
    rva = names[name]
    off = pe.get_offset_from_rva(rva)
    code = bytes(out[off:off+65])
    for opcode, value in [(b'\xba',red),(b'\x41\xb8',green),(b'\x41\xb9',blue)]:
        at = code.find(opcode)
        if at < 0 or code.find(opcode,at+1) >= 0: raise RuntimeError(f'Unexpected instruction: {name} {opcode.hex()}')
        pos = off+at+len(opcode)
        old = struct.unpack_from('<I',out,pos)[0]
        if old > 255: raise RuntimeError('Unexpected color')
        struct.pack_into('<I',out,pos,value)
        changes.append({'function':name,'offset':pos,'before':old,'after':value})
result = root/'nemu-ui-lib.control-purple-candidate.dll'
result.write_bytes(out)
(root/'control-palette-manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(out).hexdigest(),'changes':changes},indent=2))
print('Prepared',len(changes),'channel edits:',result)
