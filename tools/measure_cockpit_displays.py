"""Run inside Blender: read-only measurements of the loaded cockpit geometry.

Writes a JSON measurement artifact; does not edit or save the Blender scene.
"""
import bpy
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np


def hull(points):
    points=sorted(set(tuple(p) for p in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in points:
        while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(points):
        while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def components(name):
    obj=bpy.data.objects[name]
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    try:
        verts=np.array([list(evaluated.matrix_world@v.co) for v in mesh.vertices])
        faces=[list(p.vertices) for p in mesh.polygons]
        adjacency={i:set() for i in range(len(verts))}
        for face in faces:
            for i in face:adjacency[i].update(face)
        seen=set();result=[]
        for i in adjacency:
            if i in seen:continue
            todo=[i];ids=set()
            while todo:
                j=todo.pop()
                if j in ids:continue
                ids.add(j);todo.extend(adjacency[j]-ids)
            seen.update(ids)
            remap={old:new for new,old in enumerate(sorted(ids))}
            result.append((verts[sorted(ids)],[[remap[k] for k in f] for f in faces if f[0] in ids]))
        return result
    finally:evaluated.to_mesh_clear()


def measure(name,points,faces,connectors=None):
    center=points.mean(axis=0)
    _,_,axes=np.linalg.svd(points-center,full_matrices=False)
    normal=axes[-1]
    right=np.array([0.,-1.,0.]);right-=normal*np.dot(right,normal);right/=np.linalg.norm(right)
    up=np.cross(normal,right)
    if up[2]<0:up=-up
    origin=center
    anchors={}
    if connectors:
        anchors={key:np.array(list(bpy.data.objects[value].matrix_world.translation)) for key,value in connectors.items()}
        origin=anchors['center']
        right=anchors['right']-origin;right/=np.linalg.norm(right)
        up=origin-anchors['down'];up-=right*np.dot(up,right);up/=np.linalg.norm(up)
    xy=np.stack(((points-origin)@right,(points-origin)@up),axis=1)
    boundary=hull(xy.tolist())
    area=0.
    for f in faces:
        for i in range(1,len(f)-1):area+=np.linalg.norm(np.cross(points[f[i]]-points[f[0]],points[f[i+1]]-points[f[0]]))/2
    return dict(object=name,vertices_world_m=points.tolist(),faces=faces,
        center_world_m=center.tolist(),basis_origin_world_m=origin.tolist(),
        right_axis_world=right.tolist(),up_axis_world=up.tolist(),normal_world=normal.tolist(),
        plane_residual_max_m=float(np.max(np.abs((points-center)@normal))),
        boundary_local_m=boundary,bounds_local_m=[xy.min(axis=0).tolist(),xy.max(axis=0).tolist()],
        width_m=float(np.ptp(xy[:,0])),height_m=float(np.ptp(xy[:,1])),surface_area_m2=float(area),
        connector_names=connectors,connectors_world_m={k:v.tolist() for k,v in anchors.items()},
        connector_width_m=float(2*np.linalg.norm(anchors['right']-origin)) if anchors else None,
        connector_height_m=float(2*np.linalg.norm(anchors['down']-origin)) if anchors else None)


project=Path(bpy.data.filepath)
if project.name.lower()!='cockpit_f-117.blend':raise RuntimeError('Load Cockpit_F-117.blend first')
scale=bpy.context.scene.unit_settings.scale_length
if abs(scale-1)>1e-6:raise RuntimeError('Unexpected scene unit scale; verify metres before exporting')
out=project.parent.parent/'tools/data/cockpit_display_geometry.json'
surfaces={}
for label,center,down,right in [
    ('MFD','MFD-PLASHKA-CENTER','MFD-PLASHKA-DOWN','MFD-PLASHKA-RIGHT'),
    ('Left MFD','MFD-PLASHKA-CENTER1','MFD-PLASHKA-DOWN1','MFD-PLASHKA-RIGHT1'),
    ('Right MFD','RADAR-PLASHKA-CENTER','RADAR-PLASHKA-DOWN','RADAR-PLASHKA-RIGHT')]:
    if label=='MFD':name='Cockpit.043';points,faces=components(name)[0]
    else:
        name='Cockpit.007'
        candidates=[c for c in components(name) if len(c[0])==20]
        points,faces=max(candidates,key=lambda c:c[0][:,1].mean()) if label=='Left MFD' else min(candidates,key=lambda c:c[0][:,1].mean())
    surfaces[label]=measure(name,points,faces,dict(center=center,down=down,right=right))
points,faces=components('Cockpit.044')[0]
surfaces['Centre secondary surface']=measure('Cockpit.044',points,faces)
glass=components('Cockpit glass.001')
# Thin glass has front/back copies and narrow edge faces. Keep the two unique
# broad faces nearest the eye (smaller world X) and report each pane separately.
large=[]
for points,faces in glass:
    m=measure('Cockpit glass.001',points,faces)
    if m['surface_area_m2']>.01:large.append(m)
large.sort(key=lambda m:m['center_world_m'][0])
panes=[]
for m in large:
    if not any(np.linalg.norm(np.array(m['center_world_m'])-p['center_world_m'])<.005 for p in panes):panes.append(m)
for i,p in enumerate(panes):surfaces['HUD glass '+str(i+1)]=p
report=dict(source_blend=str(project),measured_at_utc=datetime.now(timezone.utc).isoformat(),
    scene_frame=bpy.context.scene.frame_current,unit_scale=scale,
    axis_convention='Blender world: X forward, Y left, Z up; dimensions from evaluated world vertices',
    notes=['MFD local polygons are projected into their connector plane in metres.',
           'Mapping these metres to DCS indicator coordinates requires in-game validation.',
           'HUD panes are physical glass, not an angular HUD calibration.',
           'Centre secondary surface is a separate overlapping mesh; do not sum its area.'],surfaces=surfaces)
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('Saved',out)
for label,m in surfaces.items():
    print(label,':',round(m['width_m']*1000,2),'x',round(m['height_m']*1000,2),'mm;',
          round(m['surface_area_m2']*10000,2),'cm2; plane residual',round(m['plane_residual_max_m']*1000,4),'mm')
