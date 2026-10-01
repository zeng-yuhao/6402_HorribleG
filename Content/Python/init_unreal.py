import unreal

try:
    from monster_ai.runtime import register_runtime

    register_runtime()
except Exception as exc:
    unreal.log_error(f"monster_ai init failed: {exc}")
