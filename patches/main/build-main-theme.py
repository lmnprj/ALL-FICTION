from pathlib import Path
import ctypes,hashlib,json,pefile,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'qt-tools'))
from PyQt5.QtCore import QResource,QFile,QIODevice,QByteArray
from PyQt5.QtSvg import QSvgRenderer
from PyQt5 import sip

root=Path(__file__).resolve().parent
install=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_main')
sha=lambda b:hashlib.sha256(b).hexdigest()
exe=(install/'MuMuNxMain.exe').read_bytes();dll=(install/'nemu-ui-lib.dll').read_bytes();rcc=(install/'rcc/NxMainResource.rcc').read_bytes()
assert sha(exe)=='93a601990723bc5514e407fb8e5172e58496749f678601055060902ce2a5c998'
assert sha(dll)=='c674f72ba469b643b2a658746a5fef6fc540aaf28bc6cd851c01f6d810c84bd8'
manifest=[]
def record(label,src,out,filename,changes):
 (root/filename).write_bytes(out);manifest.append({'name':label,'before':sha(src),'after':sha(out),'candidate':filename,'changes':changes})

# Main title and its title-bar background, without changing the instance list logic.
p=pefile.PE(data=exe,fast_load=True);d=bytearray(exe);B=p.OPTIONAL_HEADER.ImageBase;edits=[]
def patch(va,old,new,label):
 at=p.get_offset_from_rva(va-B);assert len(old)==len(new) and d[at:at+len(old)]==old,(hex(va),bytes(d[at:at+len(old)]).hex());d[at:at+len(new)]=new;edits.append({'va':hex(va),'before':old.hex(),'after':new.hex(),'label':label})
string=0x140080180;brand=0x1400801c0;helper=0x140080100
patch(string,b'\xcc'*8,b'#110a1a\0','header colour')
patch(brand,b'\xcc'*12,b'ALL FICTION\0','display name')
stub=b'\x48\x8d\x15'+struct.pack('<i',string-helper-7)+b'\xff\x25'+struct.pack('<i',0x1427b2830-helper-13)
patch(helper,b'\xcc'*len(stub),stub,'construct header colour')
for site in [0x140294964,0x140294993,0x1402949c5,0x1402949f7]:
 pos=p.get_offset_from_rva(site-B);old=bytes(d[pos:pos+6]);assert old[:2]==b'\xff\x15' and site+6+struct.unpack('<i',old[2:])[0]==0x1427b2668
 patch(site,old,b'\xe8'+struct.pack('<i',helper-site-5)+b'\x90','title-bar background')
site=0x140294dc9;pos=p.get_offset_from_rva(site-B);old=bytes(d[pos:pos+7]);assert old[:3]==b'\x4c\x8d\x05' and site+7+struct.unpack('<i',old[3:])[0]==0x141faedf8
patch(site,old,b'\x4c\x8d\x05'+struct.pack('<i',brand-site-7),'header brand name')
record('exe',exe,d,'MuMuNxMain.theme-candidate.exe',edits)

# The main process has its own Qt UI DLL; only its neutral dark surface colours
# are adjusted, retaining the previous purple accent and all status colours.
p=pefile.PE(data=dll,fast_load=True);d=bytearray(dll);colors=[]
mapping=[(0x1801405d8,b'#202020',b'#17101f'),(0x1801405e0,b'#363636b2',b'#302039b2'),(0x180140708,b'#373737',b'#2b2035'),(0x180140710,b'#4e4e4e',b'#4d3a5a'),(0x180140718,b'#464646',b'#40304e'),(0x180140720,b'#282828',b'#201629')]
for va,old,new in mapping:
 pos=p.get_offset_from_rva(va-p.OPTIONAL_HEADER.ImageBase);assert len(old)==len(new) and d[pos:pos+len(old)]==old;d[pos:pos+len(old)]=new;colors.append({'va':hex(va),'before':old.decode(),'after':new.decode()})
record('dll',dll,d,'nemu-ui-lib.main-theme-candidate.dll',colors)

# Replace only the two title-logo SVGs. The silhouette follows the existing
# ALL FICTION launcher mark and remains a scalable Qt resource.
path=str(install/'rcc/NxMainResource.rcc');assert QResource.registerResource(path);out=bytearray(rcc);icons=[]
svg=b'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#261035"/><stop offset="1" stop-color="#7400d9"/></linearGradient></defs><rect width="256" height="256" rx="54" fill="url(#g)"/><path fill="#c77bff" d="M55 160 108 101q7-6 11 1l13 21 10-22q1-3 5-3h59l-13 13h-40q-4 0-6 4l-20 49-2-25q0-3-3-2l-29 3 27-8-9-17-30 33z M149 122h36l-12 12h-25q-4 0-7 6z"/></svg>'
assert QSvgRenderer(QByteArray(svg)).isValid()
qt=ctypes.WinDLL('Qt5Core.dll');get_data=getattr(qt,'?data@QResource@@QEBAPEBEXZ');get_data.argtypes=[ctypes.c_void_p];get_data.restype=ctypes.c_void_p
anchor=QResource(':/resources/images/nx/ic_black_logo.svg');anchor_old=bytes(anchor.data());anchor_file=rcc.find(struct.pack('>I',len(anchor_old))+anchor_old)
assert anchor_file>=0 and rcc.count(struct.pack('>I',len(anchor_old))+anchor_old)==1
anchor_ptr=get_data(sip.unwrapinstance(anchor))
for icon in [':/resources/images/nx/ic_black_logo.svg',':/resources/images/nx/ic_white_logo.svg']:
 r=QResource(icon);assert r.isValid() and not r.isCompressed();old=bytes(r.data());needle=struct.pack('>I',len(old))+old
 # Identify each tree entry by the address Qt mapped, so identical tray icons
 # stored elsewhere are left untouched.
 at=anchor_file+get_data(sip.unwrapinstance(r))-anchor_ptr;assert rcc[at:at+len(needle)]==needle and len(svg)<=len(old)
 out[at:at+len(needle)]=struct.pack('>I',len(svg))+svg+bytes(len(old)-len(svg));icons.append(icon)
candidate=root/'NxMainResource.theme-candidate.rcc';candidate.write_bytes(out)
assert QResource.registerResource(str(candidate),'/theme')
for icon in icons:
 f=QFile(':/theme'+icon[1:]);assert f.open(QIODevice.ReadOnly) and bytes(f.readAll())==svg
manifest.append({'name':'rcc','before':sha(rcc),'after':sha(out),'candidate':candidate.name,'changes':icons})
(root/'main-theme-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Prepared scoped main theme, verified SVG and original versions.')
