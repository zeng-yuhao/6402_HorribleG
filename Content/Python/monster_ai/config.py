# Tunable values from 怪物AI完整方案.json (v1.1)

LOST_TIMER_SECONDS = 1.0
PATROL_WAIT_MIN = 2.0
PATROL_WAIT_MAX = 4.0

# Total vision cone is 90 degrees. UE sight uses the half-angle.
SIGHT_RADIUS = 1800.0
SIGHT_LOSE_RADIUS = 2200.0
SIGHT_HALF_ANGLE_DEGREES = 45.0

HEARING_RADIUS = 900.0
HEARING_SPEED_THRESHOLD = 20.0

CHASE_ACCEPT_RADIUS = 70.0
PATROL_ACCEPT_RADIUS = 80.0
# Must be this close in height as well, or a first-floor position counts as the floor above.
PATROL_HEIGHT_TOLERANCE = 140.0
REPATH_INTERVAL = 0.35

# BP_FirstPersonCharacter MaxWalkSpeed.
PLAYER_MOVE_SPEED = 300.0
PATROL_WALK_SPEED = 250.0
# Chase starts immediately. Speed steps with time since the chase began.
CHASE_CREEP_SECONDS = 0.5
CHASE_CREEP_SPEED = 20.0
CHASE_MID_SECONDS = 3.5
CHASE_MID_SPEED = 210.0
CHASE_FAST_SPEED = 360.0
CHASE_WALK_SPEED = CHASE_FAST_SPEED

# Local-space points inside the asylum house. Placed only on the Base2 instance.
# Capsule center. First-floor surface is about 647, second-floor surface about 1044.
F1_WALK_Z = 745.7
F2_WALK_Z = 1136.0
# Stair flight beside the first-floor hall, actor near (729, 426). Capsule centers step up the flight.
_STAIR_UP = (
    ("MonsterAI_Stair_F1", 520.0, 426.0, F1_WALK_Z),
    ("MonsterAI_Stair_Low", 635.0, 426.0, 843.0),
    ("MonsterAI_Stair_Mid", 750.0, 426.0, 941.0),
    ("MonsterAI_Stair_High", 865.0, 426.0, 1038.0),
    ("MonsterAI_Stair_F2", 980.0, 426.0, F2_WALK_Z),
)
PATROL_POINTS = (
    ("MonsterAI_Patrol_F1_Entrance", 0.0, 412.4, F1_WALK_Z),
    ("MonsterAI_Patrol_F1_Main01", -442.9, 412.4, F1_WALK_Z),
    ("MonsterAI_Patrol_F1_Main03", 1070.6, -1364.8, F1_WALK_Z),
    ("MonsterAI_Patrol_F1_Main02", 964.8, 2281.9, F1_WALK_Z),
    *_STAIR_UP,
    ("MonsterAI_Patrol_F2_Main02", 662.6, 439.1, F2_WALK_Z),
    ("MonsterAI_Patrol_F2_Main03", 806.3, 2318.5, F2_WALK_Z),
    ("MonsterAI_Patrol_F2_Hall", 94.9, 270.4, F2_WALK_Z),
    *_STAIR_UP[::-1],
)

# Door actors in this local Z band sit on the floors the monster patrols.
DOOR_Z_MIN = 600.0
DOOR_Z_MAX = 1200.0

ASSET_DIR = "/Game/AI/Monster"
BLACKBOARD_PATH = ASSET_DIR + "/Monster_Blackboard"
BEHAVIOR_TREE_PATH = ASSET_DIR + "/Monster_BT"
CHARACTER_PATH = ASSET_DIR + "/Monster_Character"
CONTROLLER_PATH = ASSET_DIR + "/Monster_Controller"
BASE2_LABEL = "LI_Asylum_Base2"
BASE_LABEL = "LI_Asylum_Base"
