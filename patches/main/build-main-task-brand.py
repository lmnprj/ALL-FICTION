from pathlib import Path
import ctypes,hashlib,json,pefile,shutil,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'qt-tools'))
from PyQt5.QtCore import QResource,QFile,QIODevice
from PyQt5.QtGui import QImageReader
root=Path(__file__).resolve().parent;install=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_main')
sha=lambda b:hashlib.sha256(b).hexdigest()
exe=(install/'MuMuNxMain.exe').read_bytes();rcc=(install/'rcc/NxMainResource.rcc').read_bytes();ico=(root/'theme-work/af-resource.ico').read_bytes()
assert sha(exe)==json.loads((root/'main-theme-manifest.json').read_text())[0]['after']
assert sha(rcc)==json.loads((root/'main-theme-manifest.json').read_text())[2]['after']
assert QImageReader(str(root/'theme-work/af-resource.ico')).canRead()

# Change only the actual main window caption; do not change QApplication's
# application name, which MuMu may use for configuration paths.
pe=pefile.PE(data=exe);base=pe.OPTIONAL_HEADER.ImageBase;data=bytearray(exe);site=0x1401ec6d0;target=0x1400801c0
o=pe.get_offset_from_rva(site-base);old=bytes(data[o:o+7]);assert old[:3]==bytes.fromhex('4c8d05') and site+7+struct.unpack('<i',old[3:])[0]==0x141faebb0
assert pe.get_data(target-base,12)==b'ALL FICTION\0';new=old[:3]+struct.pack('<i',target-site-7);data[o:o+7]=new

# Rewrite the existing version-information tree, retaining all other values.
def align(n):return (n+3)&~3
def read_node(raw,start=0):
 length,vlen,typ=struct.unpack_from('<HHH',raw,start);end=start+length;pos=start+6;chars=[]
 while True:
  c=struct.unpack_from('<H',raw,pos)[0];pos+=2
  if not c:break
  chars.append(c)
 key=bytes().join(struct.pack('<H',x) for x in chars).decode('utf-16le');pos=align(pos)
 size=vlen*2 if typ==1 else vlen;value=raw[pos:pos+size];pos=align(pos+size);children=[]
 while pos+6<=end:
  size=struct.unpack_from('<H',raw,pos)[0]
  if not size:break
  child=read_node(raw,pos);children.append(child);pos=align(pos+size)
 assert end<=len(raw)
 return [key,typ,value,children]
def build_node(node):
 key,typ,value,children=node
 if key in ('FileDescription','ProductName'):value='ALL FICTION\0'.encode('utf-16le')
 buf=bytearray(6);buf.extend((key+'\0').encode('utf-16le'));buf.extend(b'\0'*(align(len(buf))-len(buf)));buf.extend(value);buf.extend(b'\0'*(align(len(buf))-len(buf)))
 for child in children:
  buf.extend(build_node(child));buf.extend(b'\0'*(align(len(buf))-len(buf)))
 struct.pack_into('<HHH',buf,0,len(buf),len(value)//2 if typ==1 else len(value),typ)
 return bytes(buf)
entries={e.id:e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id in (14,16)}
vnode=entries[16].directory.entries[0].directory.entries[0];vs=vnode.data.struct;vraw=pe.get_data(vs.OffsetToData,vs.Size);version=build_node(read_node(vraw))
assert len(version)==len(vraw)
version_offset=pe.get_offset_from_rva(vs.OffsetToData);assert data[version_offset:version_offset+len(vraw)]==vraw
data[version_offset:version_offset+len(vraw)]=version
_,kind,count=struct.unpack_from('<HHH',ico,0);assert kind==1 and count==9
icon_type=next(x for x in pe.DIRECTORY_ENTRY_RESOURCE.entries if x.id==3)
group=bytearray(struct.pack('<HHH',0,1,count))
for i in range(count):
 w,h,colors,res,planes,bits,size,offset=struct.unpack_from('<BBBBHHII',ico,6+16*i)
 blob=ico[offset:offset+size];assert len(blob)==size
 entry=next(x for x in icon_type.directory.entries if x.id==i+1).directory.entries[0].data.struct
 at=pe.get_offset_from_rva(entry.OffsetToData);assert size<=entry.Size
 data[at:at+entry.Size]=blob+bytes(entry.Size-size)
 struct.pack_into('<I',data,entry.get_file_offset()+4,size)
 group.extend(struct.pack('<BBBBHHIH',w,h,colors,res,planes,bits,size,i+1))
group_entry=next(x for x in entries[14].directory.entries if x.id==101).directory.entries[0].data.struct
assert len(group)==group_entry.Size
group_at=pe.get_offset_from_rva(group_entry.OffsetToData);data[group_at:group_at+group_entry.Size]=group
candidate=root/'MuMuNxMain.task-brand-candidate.exe';candidate.write_bytes(data);final=bytes(data);patched=pefile.PE(data=final)
for sec in pe.sections:
 other=next((x for x in patched.sections if x.Name==sec.Name),None)
 assert other is not None and other.VirtualAddress==sec.VirtualAddress and other.PointerToRawData==sec.PointerToRawData
values=[t.entries for group in patched.FileInfo for x in group if hasattr(x,'StringTable') for t in x.StringTable];assert values and all(v.get(b'FileDescription')==b'ALL FICTION' and v.get(b'ProductName')==b'ALL FICTION' for v in values)

# The window icon is loaded separately from Qt's RCC, so replace that resource
# too; leave the other resources, including the previously themed logo, alone.
assert QResource.registerResource(str(install/'rcc/NxMainResource.rcc'))
item=QResource(':/resources/icon/nx_main.ico');assert item.isValid() and not item.isCompressed();old_icon=bytes(item.data());needle=struct.pack('>I',len(old_icon))+old_icon
pos=rcc.find(needle);assert pos>=0 and rcc.find(needle,pos+1)<0 and len(ico)<=len(old_icon)
new_rcc=bytearray(rcc);new_rcc[pos:pos+len(needle)]=struct.pack('>I',len(ico))+ico+bytes(len(old_icon)-len(ico));rcc_candidate=root/'NxMainResource.task-brand-candidate.rcc';rcc_candidate.write_bytes(new_rcc)
assert QResource.registerResource(str(rcc_candidate),'/verify');f=QFile(':/verify/resources/icon/nx_main.ico');assert f.open(QIODevice.ReadOnly) and bytes(f.readAll())==ico
(root/'main-task-brand-manifest.json').write_text(json.dumps([{'name':'exe','before':sha(exe),'after':sha(final),'candidate':candidate.name},{'name':'rcc','before':sha(rcc),'after':sha(new_rcc),'candidate':rcc_candidate.name}],indent=2))
print('Candidate built; native title, version description and icons checked.')
