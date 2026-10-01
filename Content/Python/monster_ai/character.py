import unreal

from . import config


def _is_player(actor):
    if not actor:
        return False
    player = unreal.GameplayStatics.get_player_pawn(actor, 0)
    return bool(player) and actor == player


@unreal.uclass()
class MonsterCharacter(unreal.Character):
    """
    Patrol/chase judgments live here and are written to the blackboard.
    OnContactPlayer is the collaborator hook; overlap logic stays in this class.
    """

    pending_player = unreal.uproperty(unreal.Actor)

    @unreal.ufunction(
        params=[unreal.Actor],
        meta=dict(BlueprintImplementableEvent=True, DisplayName="OnContactPlayer"),
    )
    def on_contact_player(self, player):
        pass

    @unreal.ufunction(override=True)
    def receive_begin_play(self):
        super(MonsterCharacter, self).receive_begin_play()
        if not _is_in_base2(self):
            unreal.log("MonsterCharacter: Base2 is not loaded around this actor, removing it")
            self.destroy_actor()
            return
        self.set_actor_tick_enabled(True)
        self._stimulus_ready = False
        self._contact_bound = False
        self._perception_bound = False
        self._bind_perception()
        self._bind_contact()
        self._ensure_player_stimulus()

    @unreal.ufunction(override=True)
    def receive_tick(self, delta_seconds):
        super(MonsterCharacter, self).receive_tick(delta_seconds)
        if not self._stimulus_ready:
            self._ensure_player_stimulus()
        self._report_footsteps()
        self._flush_pending_target()

    @unreal.ufunction(params=[unreal.Actor, unreal.AIStimulus])
    def handle_perception(self, actor, stimulus):
        if not _is_player(actor):
            return
        sensed = True
        try:
            sensed = bool(stimulus.get_editor_property("successfully_sensed"))
        except Exception:
            try:
                sensed = bool(stimulus.successfully_sensed)
            except Exception:
                sensed = True
        if sensed:
            self._apply_target(actor)

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
        if not _is_player(other_actor):
            return
        controller = self._monster_controller()
        if not controller or not controller.b_has_target:
            return
        controller.notify_contact()
        self.on_contact_player(other_actor)

    def _bind_perception(self):
        if getattr(self, "_perception_bound", False):
            return
        perception = self.get_component_by_class(unreal.AIPerceptionComponent)
        if not perception:
            return
        perception.on_target_perception_updated.add_function(self, "handle_perception")
        self._perception_bound = True

    def _bind_contact(self):
        if getattr(self, "_contact_bound", False):
            return
        boxes = self.get_components_by_class(unreal.BoxComponent)
        for box in boxes:
            if "Contact" in str(box.get_name()):
                box.on_component_begin_overlap.add_function(self, "handle_contact_overlap")
                self._contact_bound = True
                return

    def _ensure_player_stimulus(self):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player or player == self:
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
            source.set_editor_property("b_auto_register_as_source", True)
        except Exception:
            pass
        try:
            source.register_with_perception_system()
        except Exception:
            pass
        self._stimulus_ready = True

    def _report_footsteps(self):
        player = unreal.GameplayStatics.get_player_pawn(self, 0)
        if not player or player == self:
            return
        if player.get_velocity().size() < config.HEARING_SPEED_THRESHOLD:
            return
        if (player.get_actor_location() - self.get_actor_location()).size() > config.HEARING_RADIUS:
            return
        unreal.AISense_Hearing.report_noise_event(
            self,
            player.get_actor_location(),
            1.0,
            player,
            config.HEARING_RADIUS,
            "Footstep",
        )

    def _monster_controller(self):
        controller = self.get_controller()
        if controller and hasattr(controller, "notify_player_seen"):
            return controller
        return None

    def _apply_target(self, player):
        controller = self._monster_controller()
        if not controller:
            self.pending_player = player
            return
        self.pending_player = None
        controller.notify_player_seen(player)

    def _flush_pending_target(self):
        player = self.pending_player
        if player:
            self._apply_target(player)


def _is_in_base2(actor):
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
