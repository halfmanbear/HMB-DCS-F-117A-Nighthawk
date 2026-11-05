"""Create vector stencil sources; run with Python or Blender Python.

Pixel coordinates are traced against the existing 4096px UV atlases. The sensor
control legends use TO 1F-117A-1 Figure 4-17, PDF page 199. No gauge needle or
numeric readout is baked into these fixed legends.
"""
from pathlib import Path
import json
import math

ROOT = Path(r'E:\Saved Games\DCS\Mods\aircraft\F-117-Nighthawk')
OUT = ROOT / 'dist/cockpit-texture-remake/sources'


def legend(x,y,width,text,size=12,rotate=None,background='#383b40'):
    # Cover only the old glyphs: retain the switch/knob footprints and plate edges.
    transform = f' transform="rotate({rotate},{x},{y})"' if rotate else ''
    return (f'<g{transform}><rect x="{x-width/2}" y="{y-size}" '
            f'width="{width}" height="{size+4}" fill="{background}"/>'
            f'<text x="{x}" y="{y}" fill="#deded5" '
            f'font-family="Arial" font-size="{size}" text-anchor="middle" '
            f'letter-spacing="0.35">{text}</text></g>')


def write(stem,body):
    (OUT/(stem+'.svg')).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="4096" height="4096" '
        'viewBox="0 0 4096 4096">'+''.join(body)+'</svg>',encoding='utf8')


write('f117_cpt_instrument_stencils',[
    legend(1908,3630,91,'BRIGHTNESS',12),
    legend(1993,3633,70,'CONTRAST',12),
    legend(2089,3627,69,'SYM BRT',12),
    legend(2184,3632,62,'STATUS',12),
    legend(2259,3631,27,'ON',12),
    legend(2288,3661,25,'PWR',9),
    legend(2261,3691,30,'OFF',12),
])
# These legends are traced from the existing texture; their colour is editorial.
write('f117_cpt_console_stencils',[
    legend(2008,672,84,'COM 2',18,background='#292a29'),
    legend(2014,827,138,'OXYGEN REGULATOR',11,background='#292a29'),
    legend(2013,810,81,'PUSH TO SYNC',8,background='#292a29'),
    legend(2000,858,37,'FLOW',9,background='#292a29'),
    legend(2132,861,42,'R.S.L',10,background='#292a29'),
])


def calibrated_faces():
    data=json.loads((OUT.parent/'calibrated-gauge-layout.json').read_text())
    body=[]
    for gauge in data['samples']:
        cx,cy=gauge['center']; radius=gauge['radius']
        coeff=gauge['registration']['world_to_pixel_yz']
        a,b=-coeff[0][0],-coeff[0][1]
        c,d=-coeff[1][0],-coeff[1][1]
        n=math.hypot(a,b);a,b=a/n,b/n
        n=math.hypot(c,d);c,d=c/n,d/n
        determinant=a*d-b*c
        body.append(f'<g transform="matrix({a},{b},{c},{d},{cx},{cy})">')
        body.append(f'<circle r="{radius+1}" fill="#131719"/>')
        body.append(f'<circle r="{radius*.95}" fill="none" stroke="#666963" stroke-width="0.6"/>')
        for sample in gauge['samples']:
            ux,uy=sample['uv_direction']
            x=(d*ux-c*uy)/determinant;y=(-b*ux+a*uy)/determinant
            n=math.hypot(x,y);x,y=x/n,y/n
            value=sample['value'];major=value%100==0
            ri=radius*(.77 if major else .85);ro=radius*.93
            body.append(f'<path d="M{x*ri},{y*ri} L{x*ro},{y*ro}" stroke="#deded5" stroke-width="{1.2 if major else .7}"/>')
            if major:
                tx,ty=x*radius*.65,y*radius*.65
                body.append(f'<text x="{tx}" y="{ty}" text-anchor="middle" dominant-baseline="central" font-family="Arial" font-size="{radius*.17}" fill="#e3e2d9">{value//100}</text>')
        labels=[('ALT',-.17),('FEET',.26)] if gauge['instrument']=='altimeter' else [('AIRSPEED',-.20),('KNOTS',.18),('X100',.34)]
        for text,y in labels:
            body.append(f'<text x="0" y="{radius*y}" text-anchor="middle" font-family="Arial" font-size="{radius*.105}" fill="#d9dbd3">{text}</text>')
        body.append('</g>')
    write('f117_cpt_calibrated_gauge_faces',body)


if (OUT.parent/'calibrated-gauge-layout.json').exists():
    calibrated_faces()
