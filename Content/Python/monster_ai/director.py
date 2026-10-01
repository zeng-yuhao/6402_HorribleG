import math
import random

import unreal

from . import config


def _is_player_actor(actor):
    if not actor:
        return False
    player = unreal.GameplayStatics.get_player_pawn(actor, 0)
    return bool(player) and actor == player


def _ensure_player_stimulus(player):
    if not player:
        return
    existing = player.get_component_by_class(unreal.AIPerceptionStimuliSourceComponent)
    if existing:
        return
    source = player.add_component_by_class(
        unreal.AIPerceptionStimuliSourceComponent,
        True,
        unreal.Transform(),
        False,
    )
    if not source:
        return
    source.register_for_sense(unreal.AISense_Sight)
    source.register_for_sense(unreal.AISense_Hearing)
    source.register_as_source_for_senses = True


@unreal.uclass()
class Monster_Controller(unreal.AIController):
    """Runs movement + the 1s lose-player timer from the spec."""

    b_has_target = unreal.uproperty(bool)
    target_actor = unreal.uproperty(unreal.Actor)
    last_known_location = unreal.uproperty(unreal.Vector)
    b_is_chasing = unreal.uproperty(bool)
    lost_timer = unreal.uproperty(float)

    @unreal.ufunction(override=True)
    def receive_possess(self, possessed_pawn):
        super(Monster_Controller, self).receive_possess(possessed_pawn)
        self.set_actor_tick_enabled(True)
        self.lost_timer = 0.0

    @unreal.ufunction(override=True)
    def receive_tick(self, delta_seconds):
        super(Monster_Controller, self).receive_tick(delta_seconds)
        if not self.b_has_target:
            self.lost_timer = 0.0
            return
        target = self.target_actor
        if target and self.line_of_sight_to(target):
            self.lost_timer = 0.0
            return
        self.lost_timer += float(delta_seconds)
        if self.lost_timer >= config.LOST_TIMER_SECONDS:
            self.clear_target()

    def set_target(self, player):
        self.b_has_target = True
        self.target_actor = player
        self.last_known_location = player.get_actor_location()
        self.b_is_chasing = True
        self.lost_timer = 0.0

    def clear_target(self):
        self.b_has_target = False
        self.target_actor = None
        self.b_is_chasing = False
        self.lost_timer = 0.0
        self.stop_movement()


@unreal.uclass()
class Monster_Director(unreal.Actor):
    """
    Placed in Showcase. Owns perception, contact, and patrol/chase switching.
    Behavior-tree equivalent: Selector(Chase if bHasTarget else Patrol).
    """

    b_has_target = unreal.uproperty(bool)
    target_actor = unreal.uproperty(unreal.Actor)
    last_known_location = unreal.uproperty(unreal.Vector)
    b_is_chasing = unreal.uproperty(bool)

    @unreal.ufunction(override=True)
    def receive_begin_play(self):
        super(Monster_Director, self).receive_begin_play()
        self.set_actor_tick_enabled(True)
        self._monster = self._find_or_spawn_monster()
        self._controller = None
        self._patrol_points = self._collect_patrol_points()
        self._patrol_index = 0
        self._patrol_wait = 0.0
        self._repath = 0.0
        self._waiting = False
        self._contact_cooldown = 0.0
        if not self._monster:
            unreal.log_error("Monster_Director: no Monster_Character in world")
            return
        self._bind_contact(self._monster)
        self._possess(self._monster)
        _ensure_player_stimulus(unreal.GameplayStatics.get_player_pawn(self, 0))
        self._move_to_current_patrol(force=True)
        unreal.log("Monster_Director: started on LI_Asylum_Base2")

    @unreal.ufunction(override=True)
    def receive_tick(self, delta_seconds):
        super(Monster_Director, self).receive_tick(delta_seconds)
        monster = getattr(self, "_monster", None)
        if not monster:
            return
        dt = float(delta_seconds)
        self._contact_cooldown = max(0.0, getattr(self, "_contact_cooldown", 0.0) - dt)
        self._update_perception(monster)
        self._update_contact(monster)
        self._sync_public_state()
        if self.b_has_target:
            self._tick_chase(monster, dt)
        else:
            self._tick_patrol(dt)

    @unreal.ufunction(params=[unreal.Actor], meta=dict(BlueprintImplementableEvent=True, DisplayName="OnContactPlayer"))
    def on_contact_player(self, player):
        """Collaborator hook. Do not change overlap/state-machine logic here."""
        pass

    def _find_or_spawn_monster(self):
        world_actors = unreal.GameplayStatics.get_all_actors_of_class(self, unreal.Character)
        for actor in world_actors:
            if actor.get_actor_label() == "Monster_Character":
                return actor
        tagged = unreal.GameplayStatics.get_all_actors_with_tag(self, "Monster_Character")
        if tagged:
            return tagged[0]
        spawn_points = unreal.GameplayStatics.get_all_actors_with_tag(self, "MonsterAI_Spawn")
        if not spawn_points:
            spawn_points = unreal.GameplayStatics.get_all_actors_with_tag(self, "MonsterPatrol")
        location = spawn_points[0].get_actor_location() if spawn_points else self.get_actor_location()
        transform = unreal.Transform(location, unreal.Rotator(), unreal.Vector(1.0, 1.0, 1.0))
        character_class = unreal.EditorAssetLibrary.load_blueprint_class("/Game/AI/Monster/Monster_Character")
        if not character_class:
            character_class = unreal.Character
        spawned = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(
            self, character_class, transform, unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN
        )
        if not spawned:
            unreal.log_error("Monster_Director: failed to spawn monster")
            return None
        actor = unreal.GameplayStatics.finish_spawning_actor(spawned, transform)
        actor.set_actor_label("Monster_Character")
        actor.tags = ["Monster_Character"]
        self._apply_preview_mesh(actor)
        return actor

    def _apply_preview_mesh(self, actor):
        mesh_comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        if not mesh_comp:
            return
        mesh = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
        anim = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
        if mesh:
            try:
                mesh_comp.set_skeletal_mesh_asset(mesh)
            except Exception:
                try:
                    mesh_comp.set_skeletal_mesh(mesh)
                except Exception:
                    pass
        if anim:
            try:
                mesh_comp.set_anim_class(anim)
            except Exception:
                pass

    def _collect_patrol_points(self):
        points = list(unreal.GameplayStatics.get_all_actors_with_tag(self, "MonsterPatrol"))
        points.sort(key=lambda actor: actor.get_actor_label())
        return points

    def _possess(self, monster):
        controller = monster.get_controller()
        if not isinstance(controller, Monster_Controller):
            transform = monster.get_actor_transform()
            spawned = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(
                self, Monster_Controller, transform, unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN
            )
            if spawned:
                controller = unreal.GameplayStatics.finish_spawning_actor(spawned, transform)
            if controller:
                controller.possess(monster)
        self._controller = controller
        movement = monster.get_component_by_class(unreal.CharacterMovementComponent)
        if movement:
            movement.max_walk_speed = config.PATROL_WALK_SPEED

    def _bind_contact(self, monster):
        boxes = monster.get_components_by_class(unreal.BoxComponent)
        for box in boxes:
            name = str(box.get_name())
            if "Contact" in name or "contact" in name:
                box.on_component_begin_overlap.add_function(self, "handle_contact_overlap")
                return
        capsule = monster.get_component_by_class(unreal.CapsuleComponent)
        if capsule:
            capsule.on_component_begin_overlap.add_function(self, "handle_contact_overlap")

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
    def handle_contact_overlap(self, overlapped_component, other_actor, other_comp, body_index, from_sweep, sweep_result):
        if other_actor:
            self._notify_contact(other_actor)

    def _notify_contact(self, player):
        if not _is_player_actor(player):
            return
        if getattr(self, "_contact_cooldown", 0.0) > 0.0:
            return
        self._contact_cooldown = 1.5
        self._clear_target()
        self.on_contact_player(player)
        self._move_to_current_patrol(force=True)

    def _update_contact(self, monster):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player or not self.b_has_target:
            return
        if (monster.get_actor_location() - player.get_actor_location()).size() <= 90.0:
            self._notify_contact(player)

    def _update_perception(self, monster):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player:
            return
        seen = self._can_see_player(monster, player)
        heard = self._can_hear_player(monster, player)
        if seen or heard:
            self._set_target(player)

    def _can_see_player(self, monster, player):
        origin = monster.get_actor_location()
        target = player.get_actor_location()
        delta = target - origin
        distance = delta.size()
        radius = config.SIGHT_LOSE_RADIUS if self.b_has_target else config.SIGHT_RADIUS
        if distance > radius:
            return False
        if distance > 1.0:
            forward = monster.get_actor_forward_vector()
            direction = unreal.Vector(delta.x, delta.y, delta.z)
            direction.normalize()
            dot = forward.dot(direction)
            angle = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
            if angle > (config.SIGHT_ANGLE_DEGREES * 0.5):
                return False
        controller = self._controller
        if controller and controller.line_of_sight_to(player):
            return True
        start = origin + unreal.Vector(0.0, 0.0, 60.0)
        end = target + unreal.Vector(0.0, 0.0, 60.0)
        hit = unreal.SystemLibrary.line_trace_single(
            self,
            start,
            end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,
            [monster, player],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        return not bool(hit)

    def _can_hear_player(self, monster, player):
        distance = (player.get_actor_location() - monster.get_actor_location()).size()
        if distance > config.HEARING_RADIUS:
            return False
        speed = player.get_velocity().size()
        return speed >= config.HEARING_SPEED_THRESHOLD

    def _set_target(self, player):
        self.b_has_target = True
        self.target_actor = player
        self.last_known_location = player.get_actor_location()
        self.b_is_chasing = True
        self._waiting = False
        if self._controller:
            self._controller.set_target(player)
        movement = self._monster.get_component_by_class(unreal.CharacterMovementComponent) if self._monster else None
        if movement:
            movement.max_walk_speed = config.CHASE_WALK_SPEED

    def _clear_target(self):
        self.b_has_target = False
        self.target_actor = None
        self.b_is_chasing = False
        self._waiting = False
        if self._controller:
            self._controller.clear_target()
        if self._monster:
            movement = self._monster.get_component_by_class(unreal.CharacterMovementComponent)
            if movement:
                movement.max_walk_speed = config.PATROL_WALK_SPEED

    def _sync_public_state(self):
        controller = self._controller
        if not controller:
            return
        if self.b_has_target and not controller.b_has_target:
            self._clear_target()
            self._move_to_current_patrol(force=True)
            return
        if controller.b_has_target and controller.target_actor:
            self.last_known_location = controller.last_known_location
            self.b_is_chasing = controller.b_is_chasing

    def _tick_chase(self, monster, dt):
        player = self.target_actor or unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player:
            self._clear_target()
            return
        self.last_known_location = player.get_actor_location()
        if self._controller:
            self._controller.last_known_location = self.last_known_location
        self._repath += dt
        if self._repath >= config.REPATH_INTERVAL:
            self._repath = 0.0
            self._move_to_actor(player, config.CHASE_ACCEPT_RADIUS)

    def _tick_patrol(self, dt):
        if not self._patrol_points:
            return
        if self._waiting:
            self._patrol_wait -= dt
            if self._patrol_wait <= 0.0:
                self._waiting = False
                self._patrol_index = (self._patrol_index + 1) % len(self._patrol_points)
                self._move_to_current_patrol(force=True)
            return
        target = self._patrol_points[self._patrol_index]
        if (self._monster.get_actor_location() - target.get_actor_location()).size_2d() <= config.PATROL_ACCEPT_RADIUS:
            self._waiting = True
            self._patrol_wait = random.uniform(config.PATROL_WAIT_MIN, config.PATROL_WAIT_MAX)
            if self._controller:
                self._controller.stop_movement()

    def _move_to_current_patrol(self, force=False):
        if not self._patrol_points:
            return
        self._repath = 0.0
        self._waiting = False
        self._move_to_actor(self._patrol_points[self._patrol_index], config.PATROL_ACCEPT_RADIUS)

    def _move_to_actor(self, actor, accept_radius):
        if not actor:
            return
        controller = self._controller
        if controller:
            controller.move_to_actor(actor, accept_radius)
            return
        unreal.AIBlueprintHelperLibrary.simple_move_to_actor(self, actor)
