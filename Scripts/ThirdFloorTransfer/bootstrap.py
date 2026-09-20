import unreal, pathlib, json, traceback, time
_transfer_dir = pathlib.Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer')
_transfer_seen = None
_transfer_busy = False
def _transfer_tick(dt):
    global _transfer_seen, _transfer_busy
    p = _transfer_dir / 'job.json'
    if _transfer_busy or not p.exists(): return
    job = json.loads(p.read_text())
    if job['id'] == _transfer_seen: return
    _transfer_seen = job['id']; _transfer_busy = True
    result = {'id': job['id'], 'started': time.time()}
    try:
        source = pathlib.Path(job['script'])
        exec(compile(source.read_text(),str(source),'exec'),{'__name__':'__main__'})
        result['success'] = True
    except Exception:
        result['success'] = False; result['error'] = traceback.format_exc(); unreal.log_error(result['error'])
    result['finished'] = time.time()
    (_transfer_dir/'result.json').write_text(json.dumps(result,indent=2))
    _transfer_busy = False
_transfer_handle = unreal.register_slate_post_tick_callback(_transfer_tick)
unreal.log('THIRDFLOOR_LOCAL_SCRIPT_READY')
