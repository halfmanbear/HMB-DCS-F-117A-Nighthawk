"""Create the to-scale cockpit surface diagram from Blender measurements."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'tools/data/cockpit_display_geometry.json').read_text())
fig,axes=plt.subplots(2,3,figsize=(15,10),layout='constrained')
fig.patch.set_facecolor('#f4f6f8')
labels=['Left MFD','MFD','Right MFD','HUD glass 1','HUD glass 2']
titles=['Left MFD','Centre IRADS MFD','Right MFD','HUD pane 1 (nearer eye)','HUD pane 2 (farther forward)']
for ax,label,title in zip(axes.flat,labels,titles):
    m=data['surfaces'][label]
    xy=[(x*1000,y*1000) for x,y in m['boundary_local_m']]
    ax.add_patch(Polygon(xy,facecolor='#dbece6',edgecolor='#187557',linewidth=2))
    ax.scatter([0],[0],marker='+',color='#d27b18',s=90,zorder=4)
    ax.axhline(0,color='#929a9b',linewidth=.5)
    ax.axvline(0,color='#929a9b',linewidth=.5)
    ax.set(xlim=(-130,130),ylim=(-115,115),xlabel='Horizontal (mm)',ylabel='Vertical (mm)')
    ax.set_aspect('equal');ax.grid(alpha=.18)
    ax.set_title(f"{title}\n{m['width_m']*1000:.1f} x {m['height_m']*1000:.1f} mm | {m['surface_area_m2']*10000:.1f} cm²",fontsize=11)
axes[1,2].axis('off')
axes[1,2].text(0,1,'LIVE BLENDER GEOMETRY\n\nAll five shapes use the same mm scale.\n\nMFD origin (+): indicator connector centre.\nHUD origin (+): glass-face vertex centroid.\n\nRounded corners are measured mesh edges.\nAreas are triangulated face areas,\nnot width multiplied by height.\n\nThe centre has a second overlapping mesh;\nit is not another display.\n\nPhysical boundaries do not establish\nDCS indicator scale or HUD collimation.\nThe HUD has two separate trapezoid panes.\n\nSource: Cockpit_F-117.blend\nScene unit scale: 1.0 | frame: '+str(data['scene_frame']),
    va='top',fontsize=11,linespacing=1.5,color='#31413e')
fig.suptitle('F-117 cockpit display and HUD surface boundaries',fontsize=19,fontweight='bold')
out=ROOT/'docs/assets/cockpit-display-boundaries.png';out.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(out,dpi=150);plt.close(fig)
print(out)
