"""Rectilinear views of the supplied panorama for reference inspection only."""
from pathlib import Path
import math
import numpy as np
from PIL import Image

ROOT=Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
path=ROOT/'docs/reference/CockpitImages/equirect_11520_mix.png'
out=ROOT/'dist/cockpit-texture-remake/manual-reference'
image=np.asarray(Image.open(path).convert('RGB'))
h,w=image.shape[:2]


def view(name,yaw,pitch,fov,width=1600,height=1100):
    f=width/(2*math.tan(math.radians(fov)/2))
    x,y=np.meshgrid((np.arange(width)-(width-1)/2)/f,
                    -(np.arange(height)-(height-1)/2)/f)
    z=np.ones_like(x)
    a=math.radians(pitch);y,z=np.cos(a)*y+np.sin(a)*z,-np.sin(a)*y+np.cos(a)*z
    a=math.radians(yaw);x,z=np.cos(a)*x+np.sin(a)*z,-np.sin(a)*x+np.cos(a)*z
    lat=np.arctan2(y,np.sqrt(x*x+z*z));lon=np.arctan2(x,z)
    u=(lon/(2*np.pi)+.5)*w;v=(.5-lat/np.pi)*h
    x0=np.floor(u).astype(int)%w;y0=np.clip(np.floor(v).astype(int),0,h-2)
    fx=(u-np.floor(u))[...,None];fy=(v-np.floor(v))[...,None]
    result=(image[y0,x0]*(1-fx)*(1-fy)+image[y0,(x0+1)%w]*fx*(1-fy)
            +image[y0+1,x0]*(1-fx)*fy+image[y0+1,(x0+1)%w]*fx*fy)
    Image.fromarray(np.clip(result,0,255).astype('uint8')).save(out/name)


view('photo-main-panel.png',0,-27,65)
view('photo-left-console.png',-38,-49,55)
view('photo-right-console.png',38,-49,55)
