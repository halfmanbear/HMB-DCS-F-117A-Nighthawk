"""Numerical colour masks and export validation for the GIMP exterior workflow."""
from pathlib import Path
import sys, json, hashlib, struct, math
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'dist/exterior-texture-remake'
TEX=ROOT/'Textures/F-117-NightHawk-TEXTURES'
if (WORK/'originals').exists():TEX=WORK/'originals'

def mask(original, kind, destination):
    im=Image.open(original).convert('RGBA')
    w,h=im.size
    out=Image.new('RGBA', im.size)
    changed=0
    for y in range(0,h,128):
        a=np.asarray(im.crop((0,y,w,min(h,y+128))))
        rgb=a[:,:,:3].astype(np.float32)
        lo=rgb.min(2); hi=rgb.max(2)
        lum=(rgb[:,:,0]*54+rgb[:,:,1]*183+rgb[:,:,2]*19)/256
        if kind=='airframe':
            chosen=(lum>18)&(lum<115)&(hi-lo<30)
            grey=34+(lum-34)*.70
            target=np.stack([grey*.98,grey,grey*1.025],2)
            new=np.rint(rgb*.30+target*.70)
        elif kind=='gear':
            chosen=(lum>65)&(lum<230)&(hi-lo<22)
            target=np.minimum(240,lum*1.025+2)
            new=np.rint(rgb*.55+target[:,:,None]*.45)
        else:
            chosen=np.zeros(lum.shape,dtype=bool)
            new=rgb
        rgba=np.zeros(a.shape,dtype=np.uint8)
        rgba[:,:,:3]=np.clip(new,0,255).astype(np.uint8)
        chosen &= np.any(rgba[:,:,:3]!=a[:,:,:3],2)
        rgba[:,:,3]=np.where(chosen,a[:,:,3],0)
        changed+=int(chosen.sum())
        out.paste(Image.fromarray(rgba),(0,y))
    out.save(destination)
    print(json.dumps({'changed_pixels':changed,'width':w,'height':h}))

def validate():
    manifest=json.loads((WORK/'texture-manifest.json').read_text())
    report={'errors':[],'textures':[]}
    for row in manifest['textures']:
        path=WORK/'replacements'/row['original']
        header=path.read_bytes()[:148]
        height,width=struct.unpack_from('<II',header,12)
        mips=struct.unpack_from('<I',header,28)[0]
        fourcc=header[84:88].decode('ascii')
        dxgi=struct.unpack_from('<I',header,128)[0] if fourcc=='DX10' else None
        normal=row['original'].endswith('_nm.dds')
        green=row['original']=='nighthawkgreen.dds'
        lossless=green or row['original']=='F-117_frontmesh.dds'
        if normal and fourcc!='ATI2': report['errors'].append(path.name+': expected BC5')
        if not normal and not lossless and dxgi!=98: report['errors'].append(path.name+': expected BC7')
        if lossless and struct.unpack_from('<I',header,88)[0]!=32: report['errors'].append(path.name+': expected RGBA8')
        if mips!=math.floor(math.log2(max(width,height)))+1:report['errors'].append(path.name+': incomplete mip chain')
        size=148 if fourcc=='DX10' else 128
        for level in range(mips):
            w,h=max(1,width>>level),max(1,height>>level)
            size+=w*h*4 if lossless else max(1,(w+3)//4)*max(1,(h+3)//4)*16
        if size!=path.stat().st_size:report['errors'].append(path.name+': byte size mismatch')
        source=Image.open(WORK/'sources'/(row['stem']+'.png')).convert('RGBA')
        decoded=Image.open(path).convert('RGBA')
        if source.size!=decoded.size:report['errors'].append(path.name+': source dimensions mismatch')
        old=Image.open(TEX/path.name).convert('RGBA')
        if hashlib.sha256((TEX/path.name).read_bytes()).hexdigest()!=row['original_sha256']:report['errors'].append(path.name+': original changed before installation')
        if not green and old.size!=source.size:report['errors'].append(path.name+': original dimensions mismatch')
        squared=0.; count=0; alpha_max=0; preserve_max=0
        for y in range(0,height,128):
            box=(0,y,width,min(height,y+128))
            a=np.asarray(source.crop(box)).astype(np.int16)
            b=np.asarray(decoded.crop(box)).astype(np.int16)
            squared+=float(np.sum((a[:,:,:3].astype(float)-b[:,:,:3])**2))
            count+=a[:,:,:3].size
            alpha_max=max(alpha_max,int(np.abs(a[:,:,3]-b[:,:,3]).max()))
            if row['action']=='preserve_pixels':
                o=np.asarray(old.crop(box)).astype(np.int16)
                preserve_max=max(preserve_max,int(np.abs(o-a).max()))
        if lossless and alpha_max!=0:report['errors'].append(path.name+': lossless alpha changed')
        if alpha_max>4:report['errors'].append(path.name+': alpha error exceeds 4')
        if preserve_max:report['errors'].append(path.name+': preserved source pixels changed')
        if green:
            colour=np.asarray(source)[0,0]
            if not np.all(np.asarray(old)==colour) or not np.array_equal(np.asarray(source),np.asarray(decoded)):report['errors'].append(path.name+': green tile changed')
        rmse=math.sqrt(squared/count)
        if not normal and rmse>5: report['errors'].append(path.name+': compression RMSE exceeds 5')
        report['textures'].append({'name':path.name,'size':[width,height],'fourcc':fourcc,'dxgi':dxgi,'mips':mips,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgb_rmse':None if normal else rmse,'alpha_max_error':alpha_max,'preserved_source_max_error':preserve_max})
        del source,decoded,old
    (WORK/'validation.json').write_text(json.dumps(report,indent=2))
    for start in range(0,len(manifest['textures']),4):
        group=manifest['textures'][start:start+4]
        sheet=Image.new('RGB',(1440,len(group)*390),'#232629')
        draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(group):
            draw.text((12,i*390+8),row['original']+' | ORIGINAL / RESTORED',fill='white')
            for x,p in [(10,TEX/row['original']),(725,WORK/'sources'/(row['stem']+'.png'))]:
                im=Image.open(p).convert('RGB')
                im.thumbnail((700,350))
                sheet.paste(im,(x+(700-im.width)//2,i*390+32))
        sheet.save(WORK/('review-sheet-'+str(start//4+1)+'.jpg'),quality=93)
    print(json.dumps({'errors':report['errors'],'checked':len(report['textures'])}))
if __name__=='__main__':
    if sys.argv[1]=='mask':mask(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))
    elif sys.argv[1]=='validate':validate()
