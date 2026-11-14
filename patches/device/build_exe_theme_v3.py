from pathlib import Path
import pefile,struct,json,hashlib
R=Path(__file__).resolve().parent
target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe')
installed=target.read_bytes(); installed_hash=hashlib.sha256(installed).hexdigest()
assert installed_hash=='94d5cf87627fde6625b6ff44721a8776bcf7d96a05b3f7ce7380c7eac2d15042'
base=(R/'MuMuNxDevice.before-all-fiction.exe').read_bytes()
assert hashlib.sha256(base).hexdigest()=='295d19fca7ed25650237673a86bdefe8e7136e3da3000fbb4b575847f6a613a4'
p=pefile.PE(data=base,fast_load=True);data=bytearray(base); changes=[]
def patch(va,new,label):
 off=p.get_offset_from_rva(va-0x140000000);data[off:off+len(new)]=new
 changes.append(dict(va=hex(va),label=label,after=new.hex()))
# Retain only the verified isolated tab-background/brand and settings-binding edits.
m=json.loads((R/'exe-theme-v2-manifest.json').read_text())
for c in m['changes']:
 if c['label'] in ['Floating rounded native tab backgrounds','Nine-pixel tab corner radius',
 'Brand for home tab','Home tab brand string','Prevent VM name overriding brand',
 'Menu button opens device settings directly','Built-in settings icon','Settings icon path length']:
  patch(int(c['va'],16),bytes.fromhex(c['after']),c['label'])

hide=['kHome','kBack','kWinTopmost','kMiniMode','kScreenRotation','kFullScreen',
'kOperationRecorder','kMultiPlayer','kSync','kCloneApp','kUU','kGameTools','kUURemote',
'kScreenShot','kScreenRecorder','kApkInstall','kFileTransfer','kShake','kGps','kLogin',
'kMessageCenter','kMainMenu','kSegLine','kAdsUURemote','kMultiTask','kSettingCenter',
'kReboot','kDiagnosis','kPhoneModel','kLineupAssistant','kMuMuRemote','kGameToolCollection']
css=('#%1{background:#140e1a;}/*%2*/'+
 ','.join('#TitleBar #'+n for n in hide)+'{min-width:0;max-width:0;margin:0;padding:0;border:0;}'+
 ','.join('#TitleBar #'+n for n in ['kKeymap','kVolume','kToolMenu','kWinMini','kWinMax','kWinClose'])+
 '{background:#261a32;border:1px solid #483154;border-radius:9px;margin:5px 3px;}').encode()
# Put stylesheet data in its own read-only PE section, not inside live paint code.
align=lambda v,a:(v+a-1)//a*a
last=p.sections[-1]
rva=align(last.VirtualAddress+max(last.Misc_VirtualSize,last.SizeOfRawData),p.OPTIONAL_HEADER.SectionAlignment)
raw=align(len(data),p.OPTIONAL_HEADER.FileAlignment);size=align(len(css)+1,p.OPTIONAL_HEADER.FileAlignment)
header=last.get_file_offset()+40
assert header+40<=p.OPTIONAL_HEADER.SizeOfHeaders
assert not any(data[header:header+40])
data.extend(b'\0'*(raw+size-len(data)));data[raw:raw+len(css)]=css
struct.pack_into('<8sIIIIIIHHI',data,header,b'.afstyle',len(css)+1,rva,size,raw,0,0,0,0,0x40000040)
struct.pack_into('<H',data,p.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),len(p.sections)+1)
struct.pack_into('<I',data,p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),align(rva+len(css)+1,p.OPTIONAL_HEADER.SectionAlignment))
struct.pack_into('<I',data,p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfInitializedData'),p.OPTIONAL_HEADER.SizeOfInitializedData+size)
for va in [0x14041a496,0x14041b213]:
 patch(va+3,struct.pack('<i',0x140000000+rva-va-7),'Embedded stylesheet reference')
 patch(va-4,struct.pack('<I',len(css)),'Embedded stylesheet length')
out=R/'MuMuNxDevice.all-fiction-v3.exe';out.write_bytes(data)
check=pefile.PE(data=data,fast_load=True)
assert check.get_data(rva,len(css))==css
# Explicitly verify that window-related vtables, button lookup and availability
# functions match the original FPS-patched executable.
for va,n in [(0x14251c7c0,0x1c0),(0x14251f030,0x1c0),(0x1404361f0,16),(0x14044bb60,0x60),(0x14042e390,0x593)]:
 assert check.get_data(va-0x140000000,n)==p.get_data(va-0x140000000,n)
(R/'exe-theme-v3-manifest.json').write_text(json.dumps(dict(source_sha256=installed_hash,patched_sha256=hashlib.sha256(data).hexdigest(),changes=changes),indent=2))
print(hashlib.sha256(data).hexdigest())
