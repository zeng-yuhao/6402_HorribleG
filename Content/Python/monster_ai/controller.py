import math
import random

import unreal

from . import config

# UE rebuilds the Python wrapper on every tick, so plain self._waiting does not survive.
_RUNTIME = {}
_WALK_ANIM = "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd"
_IDLE_ANIM = "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle"
# Authored speed of the forward walk clip, used to match foot speed to the capsule.
_WALK_REF_SPEED = 160.0


def _runtime(controller):
    try:
        key = controller.get_path_name()
    except Exception:
        key = str(id(controller))
    state = _RUNTIME.get(key)
    if state is None:
        state = {
            "waiting": False,
            "patrol_wait": 0.0,
            "repath": 0.0,
            "points": None,
            "contact_bound": False,
            "touching": False,
            "locomotion": None,
            "anims": None,
            "chase_time": 0.0,
        }
        _RUNTIME[key] = state
    return state


@unreal.uclass()
class MonsterController(unreal.AIController):
    """
    Patrol/Chase state machine.
    Perception and contact write the state; this class only moves the pawn
    and applies the 1 second lose-target rule.
    """

    behavior_tree_asset = unreal.uproperty(unreal.BehaviorTree)
    b_has_target = unreal.uproperty(bool)
    target_actor = unreal.uproperty(unreal.Actor)
    last_known_location = unreal.uproperty(unreal.Vector)
    b_is_chasing = unreal.uproperty(bool)
    lost_timer = unreal.uproperty(float)
    patrol_index = unreal.uproperty(int)

    @unreal.ufunction(override=True)
    def receive_possess(self, possessed_pawn):
        super(MonsterController, self).receive_possess(possessed_pawn)
        self.lost_timer = 0.0
        self.patrol_index = 0
        state = _runtime(self)
        state["patrol_wait"] = 0.0
        state["waiting"] = False
        state["repath"] = 0.0
        state["points"] = None
        state["chase_time"] = 0.0
        self.set_actor_tick_enabled(True)
        self._bind_pawn(possessed_pawn)
        _set_speed(possessed_pawn, False)
        _update_locomotion(possessed_pawn, state)
        self._move_to_current_patrol()

    @unreal.ufunction(override=True)
    def receive_tick(self, delta_seconds):
        super(MonsterController, self).receive_tick(delta_seconds)
        pawn = self.get_controlled_pawn()
        if not pawn:
            return
        dt = float(delta_seconds)
        state = _runtime(self)
        self._report_footsteps(pawn)
        if not state.get("contact_bound"):
            self._poll_contact(pawn)
        _update_locomotion(pawn, state)
        if not self.b_has_target:
            _notice_player(self, pawn)
        if self.b_has_target:
            self._tick_chase(pawn, dt)
        else:
            self._tick_patrol(pawn, dt)

    def notify_player_seen(self, player):
        if not player:
            return
        self.b_has_target = True
        self.target_actor = player
        self.last_known_location = player.get_actor_location()
        self.b_is_chasing = True
        self.lost_timer = 0.0
        state = _runtime(self)
        state["waiting"] = False
        state["chase_time"] = 0.0
        state["repath"] = config.REPATH_INTERVAL
        pawn = self.get_controlled_pawn()
        if pawn:
            _set_speed(pawn, True, 0.0)

    def notify_contact(self):
        self._clear_chase()

    def _bind_pawn(self, pawn):
        # Sight and hearing are done in _notice_player. The perception component's
        # sense delegates return a null error from Python and abort the rest of possess.
        state = _runtime(self)
        state["contact_bound"] = False
        state["touching"] = False
        for box in pawn.get_components_by_class(unreal.BoxComponent):
            if "Contact" not in str(box.get_name()):
                continue
            try:
                box.on_component_begin_overlap.add_function(self, "handle_contact_overlap")
                state["contact_bound"] = True
            except Exception:
                state["contact_bound"] = False
            break

    def _poll_contact(self, pawn):
        if not self.b_has_target:
            _runtime(self)["touching"] = False
            return
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player:
            return
        touching = _length(player.get_actor_location() - pawn.get_actor_location()) <= 130.0
        for box in pawn.get_components_by_class(unreal.BoxComponent):
            if "Contact" not in str(box.get_name()):
                continue
            try:
                touching = bool(box.is_overlapping_actor(player))
            except Exception:
                pass
            break
        state = _runtime(self)
        if touching and not state.get("touching"):
            self.notify_contact()
            try:
                from . import hooks
                hooks.on_contact_player(pawn, player)
            except Exception as exc:
                unreal.log_warning(f"OnContactPlayer: {exc}")
        state["touching"] = touching

    @unreal.ufunction(params=[unreal.Actor, unreal.AIStimulus])
    def handle_perception(self, actor, stimulus):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not actor or actor != player:
            return
        sensed = True
        try:
            sensed = bool(stimulus.successfully_sensed)
        except Exception:
            pass
        if sensed:
            self.notify_player_seen(player)

    @unreal.ufunction(
        params=[
            unreal.PrimitiveComponent,
            unreal.Actor,
            unreal.PrimitiveComponent,
            int,
            bool,
            unreal.HitResult,
        ]
    )
    def handle_contact_overlap(self, overlapped_component, other_actor, other_comp, other_body_index, from_sweep, sweep_result):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not other_actor or other_actor != player or not self.b_has_target:
            return
        self.notify_contact()
        try:
            from . import hooks
            hooks.on_contact_player(self.get_controlled_pawn(), player)
        except Exception as exc:
            unreal.log_warning(f"OnContactPlayer: {exc}")

    def _ensure_player_stimulus(self):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player:
            return
        source = player.get_component_by_class(unreal.AIPerceptionStimuliSourceComponent)
        if not source:
            source = player.add_component_by_class(
                unreal.AIPerceptionStimuliSourceComponent,
                False,
                unreal.Transform(),
                False,
            )
        if not source:
            return
        source.register_for_sense(unreal.AISense_Sight.static_class())
        source.register_for_sense(unreal.AISense_Hearing.static_class())
        try:
            source.register_with_perception_system()
        except Exception:
            pass

    def _report_footsteps(self, pawn):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player:
            return
        if _length(player.get_velocity()) < config.HEARING_SPEED_THRESHOLD:
            return
        if _length(player.get_actor_location() - pawn.get_actor_location()) > config.HEARING_RADIUS:
            return
        try:
            unreal.AISense_Hearing.report_noise_event(
                self,
                player.get_actor_location(),
                1.0,
                player,
                config.HEARING_RADIUS,
                "Footstep",
            )
        except Exception:
            pass

    def _tick_chase(self, pawn, dt):
        target = self.target_actor
        state = _runtime(self)
        if _still_perceived(self, pawn, target):
            self.lost_timer = 0.0
            self.last_known_location = target.get_actor_location()
        else:
            self.lost_timer += dt
            if self.lost_timer >= config.LOST_TIMER_SECONDS:
                self._clear_chase()
                self._move_to_current_patrol()
                return
        state["chase_time"] = float(state.get("chase_time") or 0.0) + dt
        _set_speed(pawn, True, state["chase_time"])
        if target and _move_is_idle(self):
            _steer_toward(pawn, target.get_actor_location())
        state["repath"] += dt
        if target and state["repath"] >= config.REPATH_INTERVAL:
            state["repath"] = 0.0
            self.move_to_actor(target, config.CHASE_ACCEPT_RADIUS)

    def _tick_patrol(self, pawn, dt):
        points = self._collect_patrol_points()
        if not points:
            return
        state = _runtime(self)
        if state["waiting"]:
            state["patrol_wait"] -= dt
            if state["patrol_wait"] <= 0.0:
                state["waiting"] = False
                self.patrol_index = (int(self.patrol_index) + 1) % len(points)
                self._move_to_current_patrol()
            return
        target = points[int(self.patrol_index) % len(points)]
        if _at_patrol_point(pawn.get_actor_location(), target):
            state["waiting"] = True
            state["patrol_wait"] = random.uniform(config.PATROL_WAIT_MIN, config.PATROL_WAIT_MAX)
            self.stop_movement()
            return
        if _move_is_idle(self):
            _steer_toward(pawn, target)
            state["repath"] += dt
            if state["repath"] >= config.REPATH_INTERVAL:
                state["repath"] = 0.0
                self._move_to_current_patrol()

    def _clear_chase(self):
        self.b_has_target = False
        self.b_is_chasing = False
        self.target_actor = None
        self.lost_timer = 0.0
        state = _runtime(self)
        state["waiting"] = False
        state["chase_time"] = 0.0
        pawn = self.get_controlled_pawn()
        if pawn:
            _set_speed(pawn, False)
        self.stop_movement()

    def _collect_patrol_points(self):
        state = _runtime(self)
        cached = state["points"]
        if cached:
            return cached
        base2 = None
        level_class = getattr(unreal, "LevelInstance", None)
        if level_class is not None:
            for actor in unreal.GameplayStatics.get_all_actors_of_class(self, level_class):
                if actor.get_actor_label() == config.BASE2_LABEL:
                    base2 = actor
                    break
        route = []
        for _label, x, y, z in config.PATROL_POINTS:
            local = unreal.Vector(float(x), float(y), float(z))
            if base2:
                world = unreal.MathLibrary.transform_location(base2.get_actor_transform(), local)
            else:
                world = local
            route.append(world)
        state["points"] = route
        return route

    def _move_to_current_patrol(self):
        points = self._collect_patrol_points()
        if not points:
            return
        state = _runtime(self)
        state["repath"] = 0.0
        state["waiting"] = False
        point = points[int(self.patrol_index) % len(points)]
        self.move_to_location(point, config.PATROL_ACCEPT_RADIUS)


def _notice_player(controller, pawn):
    player = unreal.GameplayStatics.get_player_pawn(controller, 0)
    if not player or player == pawn:
        return
    delta = player.get_actor_location() - pawn.get_actor_location()
    distance = _length(delta)
    if distance <= config.HEARING_RADIUS and _length(player.get_velocity()) >= config.HEARING_SPEED_THRESHOLD:
        controller.notify_player_seen(player)
        return
    if distance > config.SIGHT_RADIUS:
        return
    forward = pawn.get_actor_forward_vector()
    horizontal = (delta.x * forward.x) + (delta.y * forward.y)
    span = _length_2d(delta) * _length_2d(forward)
    if span <= 1.0:
        return
    if horizontal / span < math.cos(math.radians(config.SIGHT_HALF_ANGLE_DEGREES)):
        return
    if controller.line_of_sight_to(player):
        controller.notify_player_seen(player)


def _at_patrol_point(pawn_location, point):
    delta = pawn_location - point
    return (
        _length_2d(delta) <= config.PATROL_ACCEPT_RADIUS
        and abs(delta.z) <= config.PATROL_HEIGHT_TOLERANCE
    )


def _length(vector):
    return (vector.x * vector.x + vector.y * vector.y + vector.z * vector.z) ** 0.5


def _length_2d(vector):
    return (vector.x * vector.x + vector.y * vector.y) ** 0.5


def _steer_toward(pawn, target_location):
    delta = target_location - pawn.get_actor_location()
    delta.z = 0.0
    if _length_2d(delta) < 1.0:
        return
    pawn.add_movement_input(delta, 1.0, False)


def _move_is_idle(controller):
    try:
        status = str(controller.get_move_status()).lower()
    except Exception:
        return True
    return "idle" in status


def _set_speed(pawn, chasing, chase_time=0.0):
    movement = pawn.get_component_by_class(unreal.CharacterMovementComponent)
    if not movement:
        return
    if not chasing:
        movement.max_walk_speed = config.PATROL_WALK_SPEED
    elif chase_time < config.CHASE_CREEP_SECONDS:
        movement.max_walk_speed = config.CHASE_CREEP_SPEED
    elif chase_time < config.CHASE_MID_SECONDS:
        movement.max_walk_speed = config.CHASE_MID_SPEED
    else:
        movement.max_walk_speed = config.CHASE_FAST_SPEED
    try:
        movement.gravity_scale = 1.0
    except Exception:
        pass
    try:
        movement.set_walkable_floor_angle(55.0)
    except Exception:
        pass
    try:
        movement.set_editor_property("max_step_height", 55.0)
    except Exception:
        pass
    try:
        mode = str(movement.movement_mode)
    except Exception:
        mode = ""
    if "WALK" not in mode.upper():
        try:
            movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
        except Exception:
            pass


def _load_anim(path):
    try:
        asset = unreal.load_asset(path)
    except Exception:
        asset = None
    if asset:
        return asset
    try:
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        return None


def _play_loop(mesh, asset):
    mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    try:
        mesh.play_animation(asset, True)
        return
    except Exception:
        pass
    mesh.override_animation_data(asset, True, True, 0.0, 1.0)


def _update_locomotion(pawn, state):
    mesh = pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    if not mesh:
        return
    anims = state.get("anims")
    if not anims:
        anims = {"walk": _load_anim(_WALK_ANIM), "idle": _load_anim(_IDLE_ANIM)}
        state["anims"] = anims
    speed = _length_2d(pawn.get_velocity())
    moving = speed > 12.0
    clip = "walk" if moving else "idle"
    asset = anims.get(clip) or anims.get("idle")
    if not asset:
        return
    single = False
    try:
        single = mesh.get_animation_mode() == unreal.AnimationMode.ANIMATION_SINGLE_NODE
    except Exception:
        single = False
    if state.get("locomotion") != clip or not single:
        _play_loop(mesh, asset)
        state["locomotion"] = clip
    if clip != "walk":
        return
    rate = speed / _WALK_REF_SPEED
    if rate < 0.75:
        rate = 0.75
    elif rate > 1.8:
        rate = 1.8
    try:
        mesh.set_play_rate(rate)
    except Exception:
        pass


def _still_perceived(controller, pawn, target):
    if not target:
        return False
    if controller.line_of_sight_to(target):
        return True
    distance = _length(target.get_actor_location() - pawn.get_actor_location())
    if distance > config.HEARING_RADIUS:
        return False
    return _length(target.get_velocity()) >= config.HEARING_SPEED_THRESHOLD
