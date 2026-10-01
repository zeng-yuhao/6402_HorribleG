import unreal

from . import config


@unreal.uclass()
class BTTask_GetNextPatrolPoint(unreal.BTTask_BlueprintBase):
    """Cycles Base2 hallway points into the PatrolPoint blackboard key."""

    @unreal.ufunction(override=True)
    def receive_execute_ai(self, owner_controller, controlled_pawn):
        success = False
        try:
            success = _advance(owner_controller)
        except Exception as exc:
            unreal.log_error(f"BTTask_GetNextPatrolPoint: {exc}")
        self.finish_execute(success)


def _advance(controller):
    if not controller:
        return False
    blackboard = controller.get_blackboard_component()
    if not blackboard:
        return False
    points = []
    for actor in unreal.GameplayStatics.get_all_actors_with_tag(controller, "MonsterPatrol"):
        if actor.get_actor_location().z > -2000.0:
            continue
        points.append(actor)
    order = {label: index for index, (label, *_rest) in enumerate(config.PATROL_POINTS)}
    points.sort(key=lambda actor: order.get(actor.get_actor_label(), 1000))
    if not points:
        return False
    index = int(getattr(controller, "patrol_index", 0)) % len(points)
    blackboard.set_value_as_object("PatrolPoint", points[index])
    controller.patrol_index = (index + 1) % len(points)
    return True
