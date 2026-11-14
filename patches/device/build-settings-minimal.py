from pathlib import Path
import hashlib,json,struct,pefile
r=Path('mumu-analysis/theme-work');target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');d=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(d);assert before=='73beb086a72238c0119c29e943d97c2b5a404c0277c62f38561890cdf2dcdc03';(r/'MuMuNxDevice.before-settings-minimal.exe').write_bytes(d);p=pefile.PE(data=d,fast_load=True);base=p.OPTIONAL_HEADER.ImageBase
def patch(a,b,e):
 o=p.get_offset_from_rva(a-base);assert d[o:o+len(e)]==e,(hex(a),d[o:o+len(e)].hex());d[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,dest):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',dest-self.start-len(self.code)-len(v)-4))
 def call(self,dest):self.rel('ff15',dest)
# Add selected navigation items to layout then explicitly hide; retained internal objects remain valid.
c=Code(0x14008b000);c.emit('534883ec20488bda');c.call(0x142eae918);c.emit('488bcb');c.call(0x142eaea70);c.emit('4883c4205bc3');patch(c.start,c.code,b'\xcc'*len(c.code))
for a in [0x140942422,0x140942a29,0x140943030,0x140943351,0x140943654]:
 o=p.get_offset_from_rva(a-base);old=bytes(d[o:o+6]);assert old[:2]==b'\xff\x15' and a+6+struct.unpack('<i',old[2:])[0]==0x142eae918;patch(a,b'\xe8'+struct.pack('<i',c.start-a-5)+b'\x90',old)
# Scoped QSS applies only to settings. Keep controls and state intact.
css=(b'QComboBox { background-color: #2b2036; color: #f0eaf5; border: 1px solid #473650; border-radius: 6px; padding: 5px 9px; } '
 b'QComboBox:hover { background-color: #382844; border-color: #77558d; } '
 b'QComboBox QAbstractItemView { background-color: #21162b; color: #f0eaf5; selection-background-color: #694283; border: 1px solid #473650; } '
 b'QScrollBar:vertical { background: transparent; width: 6px; margin: 0px; } '
 b'QScrollBar::handle:vertical { background: #675176; border-radius: 3px; min-height: 24px; } '
 b'QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; } '
 b'QLabel#subTitleLabel { color: transparent; font-size: 1px; max-height: 0px; } '
 b'QLabel[objectName^="descriptionLabel_"] { color: transparent; font-size: 1px; max-height: 0px; }\0')
cssaddr=0x14008b800;patch(cssaddr,css,b'\xcc'*len(css))
t=Code(0x14008b100);t.emit('534883ec40488bd9');t.call(0x142eb1ab8);t.rel('488d0d',cssaddr);t.emit('ba'+struct.pack('<I',len(css)-1).hex());t.call(0x142eaabc0);t.emit('4889442430488bcb488d542430');t.call(0x142eaeac8);t.emit('488d4c2430');t.call(0x142eaab78);t.emit('4883c4405bc3');patch(t.start,t.code,b'\xcc'*len(t.code))
a=0x140904053;patch(a,b'\xe8'+struct.pack('<i',t.start-a-5)+b'\x90',bytes.fromhex('ff155fda5a02'))
(r/'MuMuNxDevice.settings-minimal.exe').write_bytes(d);(r/'exe-settings-minimal-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(d)}));print('candidate',h(d),'css bytes',len(css))
