from pathlib import Path
import hashlib,json,struct,pefile
root=Path(__file__).resolve().parent;target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\MuMuNxDevice.exe');data=bytearray(target.read_bytes());h=lambda x:hashlib.sha256(x).hexdigest();before=h(data);assert before=='201674bd2927f3b6831b90f13245dac07d61bf65e0591ee9a39e70369259efa5';(root/'MuMuNxDevice.before-startup-redesign.exe').write_bytes(data);p=pefile.PE(data=data,fast_load=True)
def patch(a,b,expect):
 o=p.get_offset_from_rva(a-0x140000000);assert data[o:o+len(expect)]==expect,(hex(a),data[o:o+len(expect)].hex());data[o:o+len(b)]=b
class Code:
 def __init__(self,s):self.start=s;self.code=bytearray()
 def emit(self,x):self.code.extend(bytes.fromhex(x))
 def rel(self,op,d):
  v=bytes.fromhex(op);self.code.extend(v+struct.pack('<i',d-self.start-len(self.code)-len(v)-4))
 def call(self,d):self.rel('ff15',d)
 def direct(self,d):self.rel('e8',d)
# Footer anchor: horizontal stretch, vertically centered.
anchor=0x140086c00;patch(anchor,b'0,|0,-0,@-\0',b'\xcc'*11)
a=0x1403a48d9;patch(a,b'\x48\x8d\x0d'+struct.pack('<i',anchor-a-7),bytes.fromhex('488d0df0941602'))
# Hide the footer strip containing help text and percentages.
patch(0x1404ae86b,bytes.fromhex('33d290909090'),bytes.fromhex('8b92a8000000'))
# Insert styling for the real progress bar and center it in the footer layout.
css=b'QProgressBar{border:0;background:#292032;border-radius:5px;} QProgressBar::chunk{background:#a787d5;border-radius:5px;}\0';cssaddr=0x140086c40;patch(cssaddr,css,b'\xcc'*len(css))
c=Code(0x140086800);c.emit('53564883ec58488bda488bf1') # rbx=bar rsi=layout
c.emit('41b904000000');c.call(0x142eae918) # addWidget(layout, bar, stretch=0, AlignHCenter)
c.emit('488bcbba40010000');c.call(0x142eaeaf8)
c.emit('488bcbba0a000000');c.call(0x142eaeaf0)
c.emit('488bcb33d2');c.call(0x142ead9f0)
c.rel('488d0d',cssaddr);c.emit('ba'+struct.pack('<I',len(css)-1).hex());c.call(0x142eaabc0);c.emit('4889442430')
c.emit('488bcb488d542430');c.call(0x142eaeac8);c.emit('488d4c2430');c.call(0x142eaab78)
c.emit('4883c4585e5bc3');patch(c.start,c.code,b'\xcc'*len(c.code))
a=0x1404ae823;patch(a,b'\xe8'+struct.pack('<i',c.start-a-5)+b'\x90',bytes.fromhex('ff15ef00a002'))
# Startup background painter: deep purple and centered wordmark.
g=Code(0x140086000);g.emit('534881ec90000000488bd9')
g.emit('488d5310');g.emit('488d4c2430');g.call(0x142eac678)
g.emit('488bcb488d542440');g.call(0x142eaeb30)
g.emit('488d4c2450ba100a18ff');g.call(0x142eabb00)
g.emit('488d4c2430488d5424404c8d442450');g.call(0x142eac1a8)
g.emit('488d4c2450bae9e0f0ff');g.call(0x142eabb00)
g.emit('488d4c2430488d542450');g.call(0x142eac178)
g.emit('488d4c2460');g.call(0x142eb29e8);g.emit('488d4c2460ba57000000');g.call(0x142eabb90);g.emit('488d4c2460ba16000000');g.call(0x142eabca0);g.emit('488d4c2430488d542460');g.call(0x142eac1c8)
g.emit('488bcb');g.call(0x142eaf070);g.emit('d1f883e83e8944244483c0238944244c')
g.rel('488d0d',0x140084c30);g.emit('ba0b000000');g.call(0x142eaabc0);g.emit('4889442468')
g.emit('488d4c2430488d54244041b8840000004c8d4c246848c744242000000000');g.call(0x142eac1b0)
g.emit('488d4c2468');g.call(0x142eaab78);g.emit('488d4c2460');g.call(0x142eac458);g.emit('488d4c2430');g.call(0x142eac670);g.emit('4881c4900000005bc3')
patch(g.start,g.code,b'\xcc'*len(g.code));patch(0x14251ac58,struct.pack('<Q',g.start),struct.pack('<Q',0x14002fd42))
(root/'MuMuNxDevice.startup-redesign.exe').write_bytes(data);(root/'exe-startup-redesign-manifest.json').write_text(json.dumps({'source_sha256':before,'patched_sha256':h(data)}));print('built',h(data),'painter',len(g.code),'hook',len(c.code))

