from pathlib import Path
import sys,zlib,struct,hashlib,json
sys.path.insert(0,'mumu-analysis/qt-tools')
from PyQt5.QtCore import QResource,QFile,QIODevice,QByteArray
from PyQt5.QtSvg import QSvgRenderer
root=Path('mumu-analysis/theme-work'); target=Path(r'C:\Program Files\Netease\MuMuPlayer\nx_device\15.0\shell\rcc\NxDeviceResource.rcc'); src=target.read_bytes(); out=bytearray(src);assert QResource.registerResource(str(target))
# All shapes use the same 20px grid and round strokes.
shapes={
 'home':'<path d="M3 9 10 3l7 6M5 8v8h4v-4h2v4h4V8"/>',
 'keyboard':'<rect x="2" y="4.5" width="16" height="11" rx="2"/><path d="M5 8h1m2 0h1m2 0h1m2 0h1M5 11h1m2 0h1m2 0h1m2 0h1M6 13h8"/>',
 'volume':'<path d="M3 8v4h3l4 3V5L6 8H3Zm10 0c1.5 1 1.5 3 0 4m2-6c3 2 3 6 0 8"/>',
 'mute':'<path d="M3 8v4h3l4 3V5L6 8H3Zm10 0 4 4m0-4-4 4"/>',
 'setting':'<circle cx="10" cy="10" r="2.3"/><path d="M8 2.5h4l.5 2 1.5.7 1.8-1 2 3.4L16.3 9v2l1.5 1.4-2 3.4-1.8-1-1.5.7-.5 2H8l-.5-2-1.5-.7-1.8 1-2-3.4L3.7 11V9L2.2 7.6l2-3.4 1.8 1 1.5-.7z"/>',
 'min':'<path d="M5 10h10"/>','max':'<rect x="5" y="5" width="10" height="10" rx="1.5"/>',
 'restore':'<path d="M7 5V3h10v10h-2M3 7h11v10H3z"/>','close':'<path d="m6 6 8 8M14 6l-8 8"/>',
 'performance':'<path d="M3 14a7 7 0 1 1 14 0M10 12l4-4M7 15h6"/>',
 'display':'<rect x="2.5" y="3.5" width="15" height="11" rx="2"/><path d="M7 17h6m-3-2.5V17"/>',
 'audio':'<path d="M3 8v4h3l4 3V5L6 8H3Zm10 0c1.5 1 1.5 3 0 4m2-6c3 2 3 6 0 8"/>',
 'gpu':'<rect x="3" y="5" width="14" height="10" rx="2"/><circle cx="8" cy="10" r="2.2"/><path d="M14 8v4M5 17h3"/>',
 'render':'<path d="m10 2 7 4v8l-7 4-7-4V6l7-4Zm0 0v8m7-4-7 4-7-4m7 4v8"/>',
 'fps':'<path d="M3 14a7 7 0 1 1 14 0M10 12l4-4M6 15h8"/>',
 'resolution':'<rect x="2.5" y="4" width="15" height="12" rx="2"/><path d="M5 8V6h2m6 0h2v2M5 12v2h2m6 0h2v-2"/>',
 'microphone':'<rect x="7" y="2" width="6" height="10" rx="3"/><path d="M4.5 9a5.5 5.5 0 0 0 11 0M10 14.5V18m-3 0h6"/>',
}
paths={}
title=':/resources/images/nx/device/title_bar/'
for shade in ['black','white']:
 for name,shape in [('home','home'),('keyboard','keyboard'),('volume','volume'),('mute','mute'),('setting_center','setting')]:
  paths[title+'ic_'+shade+'_'+name+'.svg']=shape
 for action,shape in [('min','min'),('max','max'),('max_revert','restore'),('close','close')]:
  for state in ['normal','hover','pressed']:
   paths[title+'ic_'+shade+'_'+action+'_'+state+'.svg']=shape
setting=':/resources/images/nx/setting/'
for shade in ['black','white']:
 for name,shape in [('setting_performance','performance'),('setting_display','display'),('setting_audio','audio'),('setting_shortcut','keyboard'),('render_mode','render'),('gpu_setting','gpu'),('high_performance_model','performance'),('performance_setting','performance'),('resolution_setting','resolution'),('frame_setting','fps'),('loudspeaker_setting','audio'),('microphone_setting','microphone')]:
  paths[setting+'ic_'+shade+'_'+name+'.svg']=shape
changes=[]; skipped=[]
for path,shape in paths.items():
 r=QResource(path)
 if not r.isValid(): skipped.append((path,'missing'));continue
 old=bytes(r.data()); prefix=struct.pack('>I',len(old));needle=prefix+old; pos=src.find(needle)
 if pos<0 or src.find(needle,pos+1)>=0:skipped.append((path,'ambiguous resource'));continue
 color='#e9dff5' if '/ic_black_' in path else '#3c2c4a'
 if '_hover' in path: color='#c99af5' if '/ic_black_' in path else '#7c429c'
 if '_pressed' in path: color='#a978d2' if '/ic_black_' in path else '#63347d'
 svg=('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="'+color+'" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">'+shapes[shape]+'</svg>').encode()
 if not QSvgRenderer(QByteArray(svg)).isValid():raise RuntimeError('invalid '+path)
 payload=struct.pack('>I',len(svg))+zlib.compress(svg,9) if r.isCompressed() else svg
 if len(payload)>len(old):skipped.append((path,f'too large {len(payload)}>{len(old)}'));continue
 if out[pos:pos+4+len(old)]!=needle: skipped.append((path,'overlap'));continue
 out[pos:pos+4+len(old)]=struct.pack('>I',len(payload))+payload+bytes(len(old)-len(payload)); changes.append((path,len(old),len(payload)))
assert len(out)==len(src) and len(changes)>20
(root/'NxDeviceResource.before-minimal-icons.rcc').write_bytes(src);candidate=root/'NxDeviceResource.minimal-icons.rcc';candidate.write_bytes(out)
# Verify every replaced resource with Qt, including existing application icon.
del r
import gc;gc.collect()
assert QResource.unregisterResource(str(target));assert QResource.registerResource(str(candidate.resolve()))
for path,_,_ in changes:
 f=QFile(path);assert f.open(QIODevice.ReadOnly),path;data=bytes(f.readAll());assert QSvgRenderer(QByteArray(data)).isValid(),path
assert QResource(':/resources/icon/nx_device.ico').isValid()
h=lambda x:hashlib.sha256(x).hexdigest();(root/'minimal-icons-manifest.json').write_text(json.dumps({'source_sha256':h(src),'patched_sha256':h(out),'changes':changes,'skipped':skipped},ensure_ascii=False,indent=2),encoding='utf8')
print('changes',len(changes),'skipped',len(skipped),'sha',h(out));print('skipped:',skipped)

