import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem)
views=[('Overview',(0,0,2550),(-90,-90,0),90),('Surgery',(-815,-100,175),(-6,-22,0),85),('Ward08',(1446,435,170),(-6,-118,0),90),('Archive',(-1342,355,165),(-4,-35,0),90),('Bathroom',(-635,328,165),(-8,-5,0),95),('Hall09',(10,460,175),(-3,-85,0),85)]
for name,loc,rot,fov in views:
 label='TF_View_'+name
 if any(a.get_actor_label()==label for a in A.get_all_level_actors()):continue
 c=A.spawn_actor_from_class(u.CameraActor,u.Vector(*loc),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2]));c.set_actor_label(label);c.set_folder_path('TF_ReviewCameras');c.camera_component.set_field_of_view(fov)
 c.camera_component.set_editor_property('constrain_aspect_ratio',False)
(D/'screenshot_api.txt').write_text(u.AutomationLibrary.take_high_res_screenshot.__doc__)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
