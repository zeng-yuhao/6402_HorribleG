import unreal as u,time
S=u.get_editor_subsystem(u.EditorActorSubsystem)
L=u.get_editor_subsystem(u.LevelEditorSubsystem)
L.load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox1')
for a in S.get_all_level_actors():
 if a.get_actor_label()=='AS_R8_Autopsy':
  p=a.get_actor_location();p.y=130;a.set_actor_location(p,False,False)
 if str(a.get_folder_path()).startswith('03_Ceilings'):a.set_is_temporarily_hidden_in_editor(False)
L.save_current_level()
u.AutomationLibrary.finish_loading_before_screenshot()
cams={a.get_actor_label():a for a in S.get_all_level_actors() if isinstance(a,u.CameraActor)}
names=['AS_View_Reception','AS_View_Ward','AS_View_Treatment','AS_View_Corridor']
state={'i':0,'next':time.time()+10}
def tick(dt):
 if time.time()<state['next']:return
 if state['i']>=len(names):
  u.unregister_slate_post_tick_callback(handle);u.log('ASYLUM_SCREENSHOTS_DONE');return
 name=names[state['i']]
 u.AutomationLibrary.take_high_res_screenshot(1440,900,'/tmp/'+name+'.png',cams[name],delay=2.0)
 state['i']+=1;state['next']=time.time()+12
handle=u.register_slate_post_tick_callback(tick)
