# Corridor widening, 2026-09-20

Target: `/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex`.

The two user-marked passages now have 200.6608 cm of finished clearance between the original wood mouldings. The wall-core gap is 224 cm. Previously the room 1/5 horizontal passage was 128.6608 cm and the passage between rooms 3/7 and 4/8 was 28.6608 cm.

Room 1 was translated 72 cm north; rooms 4 and 8 were translated 172 cm east. Rooms 3 and 7 remain in place. All enclosed room dimensions and all 855 mesh props retain their mesh, materials, scale, rotation and relative placement. The corresponding room floors, broken modules, decals, lighting and doorframes moved together. The north exterior extends 72 cm and east exterior extends 172 cm. Adjacent walls, wall finishes, mouldings, corridor floors and ceilings were reconstructed as non-overlapping geometry. Existing archive and bathroom wall tiles were preserved.

`before.json` and `after.json` are live actor snapshots before and after saving and reloading. `applied.json` records each retained actor translation and the new wall geometry. `rooms.json` contains the current room bounds. Earlier `ThirdFloorTransfer` plans describe the state before widening and are retained as historical/source data; do not reapply them over the widened map.

`validation.json` passes retained-actor invariants, four-room dimensions, measured clearances, disjoint wall volumes, coplanar floor overlap, full floor-footprint coverage, local navigation and unique actor labels. `collision_checks.json` records four successful Unreal Pawn-profile capsule sweeps (radius 35 cm, half-height 90 cm). `collision_control.json` confirms the same query blocks against a wall. This validates the requested passages; it is not a full gameplay playthrough.

`Review/Overview.png` is a real editor render with the existing `MI_PostProcessDistort_Inst` effect temporarily disabled for geometry inspection. The effect was restored before the final save. `backup.json` records the backup directory. `session_closed.json` records the final save and local editor job dispatcher cleanup.
