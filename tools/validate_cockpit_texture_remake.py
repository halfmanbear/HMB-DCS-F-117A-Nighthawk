"""Validate staged DDS exports and produce review sheets without touching originals."""
from pathlib import Path
import json
import struct
import math
import hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
WORK=ROOT/'dist/cockpit-texture-remake'
TEX=ROOT/'Cockpit/Textures/F-117-NightHawk-CPT-TEXTURES'
manifest=json.loads((WORK/'texture-manifest.json').read_text())
report={'errors':[],'textures':[]}
pairs=[]

for row in manifest['textures']:
    if row['original']=='nighthawk_att.dds':continue
    path=WORK/'replacements'/row['renamed'];stem=path.stem
    header=path.read_bytes()[:148]
    height,width=struct.unpack_from('<II',header,12)
    mips=struct.unpack_from('<I',header,28)[0]
    fourcc=header[84:88].decode('ascii')
    dxgi=struct.unpack_from('<I',header,128)[0] if fourcc=='DX10' else None
    normal=stem.endswith('_normal')
    green=row['original']=='nighthawkgreen.dds'
    if normal and fourcc!='ATI2':report['errors'].append(stem+': expected BC5')
    if not normal and not green and dxgi!=98:report['errors'].append(stem+': expected BC7_UNORM')
    if green and struct.unpack_from('<I',header,88)[0]!=32:report['errors'].append(stem+': expected uncompressed RGBA8')
    expected_mips=math.floor(math.log2(max(width,height)))+1
    if mips!=expected_mips:report['errors'].append(stem+': incomplete mips')
    size=148 if fourcc=='DX10' else 128
    for level in range(mips):
        w=max(1,width>>level);h=max(1,height>>level)
        size+=w*h*4 if green else max(1,(w+3)//4)*max(1,(h+3)//4)*16
    if path.stat().st_size!=size:report['errors'].append(stem+': byte count mismatch')
    source=Image.open(WORK/'sources'/(stem+'.png')).convert('RGBA')
    decoded=Image.open(path).convert('RGBA')
    if source.size!=decoded.size:report['errors'].append(stem+': dimensions changed')
    a=np.asarray(source).astype(np.int16);b=np.asarray(decoded).astype(np.int16)
    item={'name':path.name,'width':width,'height':height,'mips':mips,
          'fourcc':fourcc,'dxgi':dxgi,'bytes':path.stat().st_size,
          'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'alpha_max_error':int(np.max(np.abs(a[:,:,3]-b[:,:,3])))}
    if normal:
        xyz=a[:,:,:3]/127.5-1
        lengths=np.linalg.norm(xyz,axis=2)
        item['source_unit_normal_max_error']=float(np.max(np.abs(lengths-1)))
        item['source_unit_normal_mean_error']=float(np.mean(np.abs(lengths-1)))
        if item['source_unit_normal_max_error']>.02:report['errors'].append(stem+': non-unit source normals')
    else:
        item['source_vs_dds_rgb_rmse_u8']=float(np.sqrt(np.mean((a[:,:,:3].astype(float)-b[:,:,:3])**2)))
    if row['original']=='F-117_glass.dds':
        old=np.asarray(Image.open(TEX/row['original']).convert('RGBA')).astype(np.int16)
        item['glass_source_original_max_error']=int(np.abs(old-a).max())
        if item['glass_source_original_max_error']!=0:report['errors'].append('Glass optical source was altered')
    if row['original']=='nighthawkgreen.dds':
        old=np.asarray(Image.open(TEX/row['original']).convert('RGBA'))
        if not np.all(old==a[0,0]):report['errors'].append('Green constant colour changed')
        if not np.array_equal(a,b):report['errors'].append('Green DDS colour is not lossless')
        item['original_bytes']=(TEX/row['original']).stat().st_size
    report['textures'].append(item)
    # Review montage is inspection only; editable authored sources remain intact.
    before=Image.open(TEX/row['original']).convert('RGB');after=source.convert('RGB')
    pairs.append((stem,before,after))
    del a,b,source,decoded

for start in range(0,len(pairs),4):
    group=pairs[start:start+4]
    sheet=Image.new('RGB',(1300,365*len(group)), '#202326');draw=ImageDraw.Draw(sheet)
    for i,(name,before,after) in enumerate(group):
        draw.text((12,i*365+8),name+'   |   ORIGINAL / REPLACEMENT',fill='white')
        for x,image in [(10,before),(655,after)]:
            image=image.copy()
            if max(image.size)<16:
                image=image.resize((578,325),Image.Resampling.NEAREST)
            else:
                image.thumbnail((630,325))
            sheet.paste(image,(x+(630-image.width)//2,i*365+30))
    sheet.save(WORK/('review-sheet-'+str(start//4+1)+'.jpg'),quality=93)

(WORK/'remaining-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'errors':report['errors'],'checked':len(report['textures'])}))
