"""Run with Blender --background --python this.py; diagnostic geometry only."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2];folder=root/'godot/assets/static_sample';manifest=json.loads((folder/'manifest.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
report=[];points=[]
for row in manifest['models']:
    meshes=json.loads((root/row['mesh_json']).read_text())
    for i,m in enumerate(meshes):
        mesh=bpy.data.meshes.new(f"{row['slot']}_{i}");mesh.from_pydata(m['vertices'],[],m['faces']);mesh.update()
        assert len(mesh.vertices)==len(m['vertices']) and len(mesh.polygons)==len(m['faces'])
        assert [list(p.vertices) for p in mesh.polygons]==m['faces']
        assert all(abs(mesh.vertices[i].co[k]-v[k])<=max(1,abs(v[k]))*1e-6 for i,v in enumerate(m['vertices']) for k in range(3))
        if m['uv']:
            layer=mesh.uv_layers.new(name='SourceUV')
            for polygon in mesh.polygons:
                for li in polygon.loop_indices:layer.data[li].uv=m['uv'][mesh.loops[li].vertex_index]
        obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj);points.extend(Vector(p) for p in m['vertices'])
        report.append({'object':obj.name,'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'uv_loops':len(mesh.loops) if m['uv'] else 0})
lo=Vector(tuple(min(p[k] for p in points) for k in range(3)));hi=Vector(tuple(max(p[k] for p in points) for k in range(3)));center=(lo+hi)/2;radius=max((hi-lo).length,1)
camdata=bpy.data.cameras.new('DiagnosticCamera');cam=bpy.data.objects.new('DiagnosticCamera',camdata);bpy.context.collection.objects.link(cam);cam.location=center+Vector((1,-1,0.8)).normalized()*radius*1.5;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=radius*1.1;camdata.clip_end=radius*10;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='RANDOM';scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.filepath=str(root/'docs/static-sample-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'godot/diagnostics/map004_local_geometry.blend'))
bpy.ops.render.render(write_still=True)
(root/'original_resources/manifests/static_sample_blender_validation.json').write_text(json.dumps({'blender_version':bpy.app.version_string,'status':'geometry_loaded_and_rendered','scene_reconstruction':False,'objects':report,'vertices':sum(r['vertices'] for r in report),'faces':sum(r['faces'] for r in report)},indent=2)+'\n')
