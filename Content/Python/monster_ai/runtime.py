import unreal

from . import config
from .controller import MonsterController

_state = {"started": False, "handle": None}


def _game_world():
    try:
        editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = editor.get_game_world()
        if world:
            return world
    except Exception:
        pass
    try:
        return unreal.EditorLevelLibrary.get_game_world()
    except Exception:
        return None


def _in_base2(actor):
    level_class = getattr(unreal, "LevelInstance", None)
    if level_class is None:
        return actor.get_actor_location().z < -2000.0
    base2 = None
    for candidate in unreal.GameplayStatics.get_all_actors_of_class(actor, level_class):
        if candidate.get_actor_label() == config.BASE2_LABEL:
            base2 = candidate
            break
    if not base2:
        return False
    delta = actor.get_actor_location() - base2.get_actor_location()
    return abs(delta.x) < 4500.0 and abs(delta.y) < 5500.0 and abs(delta.z) < 2500.0


def _tick(_delta_time):
    try:
        _tick_game()
    except Exception as exc:
        if not _state.get("error_logged"):
            unreal.log_error(f"monster_ai: {exc}")
            _state["error_logged"] = True


def _tick_game():
    world = _game_world()
    if not world:
        _state["started"] = False
        return
    if _state["started"]:
        return
    monsters = unreal.GameplayStatics.get_all_actors_with_tag(world, "Monster_Character")
    if not monsters:
        return
    monster = monsters[0]
    if not _in_base2(monster):
        monster.set_actor_hidden_in_game(True)
        monster.set_actor_enable_collision(False)
        _state["started"] = True
        unreal.log("monster_ai: Monster_Character is not in Base2, hidden")
        return
    controller = monster.get_controller()
    if not isinstance(controller, MonsterController):
        monster.set_editor_property("ai_controller_class", MonsterController.static_class())
        monster.spawn_default_controller()
        controller = monster.get_controller()
    if not isinstance(controller, MonsterController):
        if not _state.get("error_logged"):
            unreal.log_error("monster_ai: MonsterController was not possessed")
            _state["error_logged"] = True
        return
    _state["started"] = True
    unreal.log("monster_ai: MonsterController possessed Base2 monster")


def register_runtime():
    if _state["handle"] is not None:
        return
    _state["handle"] = unreal.register_slate_post_tick_callback(_tick)
    unreal.log("monster_ai: runtime registered")
