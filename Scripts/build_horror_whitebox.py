import unreal as u
import json
from pathlib import Path
ROOT='/Game/HorrorWhitebox'
MAP=ROOT+'/Maps/L_Horror_Floorplan_Whitebox'
assets=u.EditorAssetLibrary
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
if assets.does_asset_exist(MAP):
    raise RuntimeError('Refusing to overwrite existing map: '+MAP)
assert levels.new_level(MAP)
cube=assets.load_asset('/Engine/BasicShapes/Cube')
cylinder=assets.load_asset('/Engine/BasicShapes/Cylinder')
count={}
def material(name,color):
    m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT+'/Materials',u.Material,u.MaterialFactoryNew())
    e=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector)
    e.set_editor_property('constant',u.LinearColor(*color))
    u.MaterialEditingLibrary.connect_material_property(e,'',u.MaterialProperty.MP_BASE_COLOR)
    u.MaterialEditingLibrary.recompile_material(m)
    assets.save_loaded_asset(m)
    return m
white=material('M_Whitebox_Wall',(0.68,0.7,0.72,1))
floor=material('M_Whitebox_Floor',(0.23,0.25,0.27,1))
trim=material('M_Whitebox_DoorGuide',(0.19,0.33,0.29,1))
ceiling=material('M_Whitebox_Ceiling',(0.42,0.44,0.46,1))
def pos(x,y,z):return u.Vector((x-1030)*2,(y-480)*2,z)
def box(name,x1,y1,x2,y2,z,h,mat=white,folder='01_Walls',mesh=None):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,pos((x1+x2)/2,(y1+y2)/2,z+h/2))
    a.set_actor_label(name);a.set_folder_path(folder)
    a.static_mesh_component.set_static_mesh(mesh or cube)
    a.set_actor_scale3d(u.Vector((x2-x1)*.02,(y2-y1)*.02,h/100))
    a.static_mesh_component.set_material(0,mat)
    a.static_mesh_component.set_collision_profile_name('BlockAll')
    count[folder]=count.get(folder,0)+1
    return a
# Coordinates trace the supplied plan in its displayed 2048x1017 coordinate space.
# Continuous exterior, including the two steps in the outline.
outline=[(116,158),(1522,158),(1522,184),(1943,184),(1943,801),(1404,801),(1404,776),(171,776),(171,467),(116,467),(116,158)]
def segment(name,a,b,z=0,h=300,folder='01_Walls',mat=white):
    x1,y1=a;x2,y2=b
    if y1==y2:return box(name,min(x1,x2)-6.5,y1-6.5,max(x1,x2)+6.5,y1+6.5,z,h,mat,folder)
    return box(name,x1-6.5,min(y1,y2)-6.5,x1+6.5,max(y1,y2)+6.5,z,h,mat,folder)
for i in range(len(outline)-1):segment('Exterior_%02d'%i,outline[i],outline[i+1])
doors=[]
def hwall(name,y,x1,x2,door=None):
    if door:
        lo,hi=door
        segment(name+'_A',(x1,y),(lo-6.5,y));segment(name+'_B',(hi+6.5,y),(x2,y))
        box(name+'_Lintel',lo,y-6.5,hi,y+6.5,220,80)
        doors.append((name,'H',y,lo,hi))
    else:segment(name,(x1,y),(x2,y))
def vwall(name,x,y1,y2,door=None):
    if door:
        lo,hi=door
        segment(name+'_A',(x,y1),(x,lo-6.5));segment(name+'_B',(x,hi+6.5),(x,y2))
        box(name+'_Lintel',x-6.5,lo,x+6.5,hi,220,80)
        doors.append((name,'V',x,lo,hi))
    else:segment(name,(x,y1),(x,y2))
hwall('R1_South',378,116,591,(191,261));vwall('R1_East',591,158,378)
hwall('R2_North',247,681,1012,(779,849));hwall('R2_South',467,681,1012);vwall('R2_West',681,247,467);vwall('R2_East',1012,247,467)
hwall('R3_North',273,1102,1433,(1312,1382));hwall('R3_R7_Shared',493,1102,1433,(1224,1294));hwall('R7_South',712,1102,1433);vwall('R3_R7_West',1102,273,712);vwall('R3_R7_East',1433,273,712)
vwall('R4_West',1522,184,403);vwall('R4_East',1854,184,403);hwall('R4_South',403,1522,1854,(1583,1653))
hwall('R5_North',467,260,591);hwall('R5_South',687,260,591,(324,394));vwall('R5_West',260,467,687);vwall('R5_East',591,467,687)
hwall('R6_North',556,681,1012);vwall('R6_West',681,556,776,(609,679));vwall('R6_East',1012,556,776)
hwall('R8_North',493,1522,1854);hwall('R8_South',712,1522,1854,(1718,1788));vwall('R8_West',1522,493,712);vwall('R8_East',1854,493,712)
# Exact stepped footprint; ceiling hidden only in the editor, visible in play.
for i,(x1,y1,x2,y2) in enumerate([(109.5,151.5,1528.5,177.5),(109.5,177.5,1949.5,473.5),(164.5,473.5,1949.5,782.5),(1397.5,782.5,1949.5,807.5)]):
    box('Floor_%02d'%i,x1,y1,x2,y2,-20,20,floor,'02_Floors')
    a=box('Ceiling_%02d'%i,x1,y1,x2,y2,300,15,ceiling,'03_Ceilings (hidden in editor)')
    a.set_is_temporarily_hidden_in_editor(True)
box('Plan_Circular_Column',1035,607,1075,647,0,300,white,'01_Walls',cylinder)
# Clear openings, with subtle threshold markers: all eight passages stay walkable.
for name,axis,c,lo,hi in doors:
    if axis=='H':box(name+'_Threshold',lo,c-7,hi,c+7,0,1,trim,'04_Doorways')
    else:box(name+'_Threshold',c-7,lo,c+7,hi,0,1,trim,'04_Doorways')
rooms=[(1,354,268),(2,847,357),(3,1267,383),(4,1688,294),(5,425,577),(6,847,666),(7,1267,603),(8,1688,603)]
for n,x,y in rooms:
    a=actors.spawn_actor_from_class(u.TextRenderActor,pos(x,y,2),u.Rotator(90,0,0))
    a.set_actor_label('Room_%02d_Number'%n);a.set_folder_path('05_Room_Numbers')
    t=a.text_render;t.set_text(str(n));t.set_world_size(110);t.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER);t.set_text_render_color(u.Color(210,220,215,255))
# Light fixtures remain deliberately sparse for atmosphere but readable for blockout testing.
lights=[(x,y) for _,x,y in rooms]+[(220,426),(635,350),(845,205),(1056,370),(1056,675),(630,736),(380,736),(1260,222),(1480,450),(1895,390),(1700,760)]
for i,(x,y) in enumerate(lights):
    a=actors.spawn_actor_from_class(u.PointLight,pos(x,y,265))
    a.set_actor_label('Practical_%02d'%i);a.set_folder_path('06_Lighting')
    c=a.point_light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(1100 if i<8 else 750);c.set_attenuation_radius(800);c.set_light_color(u.LinearColor(.78,.87,1,1))
    box('Fixture_%02d'%i,x-15,y-6,x+15,y+6,288,8,white,'06_Lighting')
start=actors.spawn_actor_from_class(u.PlayerStart,pos(320,425,100),u.Rotator(0,0,0));start.set_actor_label('PlayerStart_MainCorridor');start.set_folder_path('07_Gameplay')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
gm=assets.load_blueprint_class('/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode')
world.get_world_settings().set_editor_property('default_game_mode',gm)
world.get_world_settings().set_editor_property('force_no_precomputed_lighting',True)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,3900),u.Rotator(-90,-90,0))
assert levels.save_current_level()
assets.save_directory(ROOT)
report={'map':MAP,'actors':len(actors.get_all_level_actors()),'geometry':count,'rooms':8,'openings':len(doors),'wall_height_cm':300,'door_height_cm':220,'door_width_cm':140,'player_start':str(start.get_actor_location()),'notes':'Ceilings hidden in editor only; visible during play. Room 7 access through room 3 only.'}
Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/whitebox_build_report.json').write_text(json.dumps(report,indent=2))
u.log('WHITEBOX_BUILD_SUCCESS '+json.dumps(report))
