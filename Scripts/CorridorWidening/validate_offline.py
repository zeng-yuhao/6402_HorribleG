"""Validate exported corridor changes without accessing Unreal.

Inputs beside this script: before.json, after.json, applied.json, rooms.json.
Only the resulting validation.json is written when this script is executed.
Navigation uses a conservative mesh AABB proxy, not cooked Unreal collision.
"""
import collections
import itertools
import json
import math
import re
from pathlib import Path

D = Path(__file__).resolve().parent
EPS = 0.001
REBUILT = {
    'TF_Architecture/Walls', 'TF_Architecture/WallFinishes',
    'TF_Architecture/Mouldings', 'TF_Architecture/Ceilings',
}


def load(name):
    return json.loads((D / name).read_text())


def floor_room(actor):
    match = re.search(r'_R(\d+)_', actor['label'])
    return int(match[1]) if match else None


def retained(actor):
    return not (actor['folder'] in REBUILT or (
        actor['folder'] == 'TF_Architecture/Floors'
        and floor_room(actor) in (0, 2, 9)))


def vector_equal(a, b, angular=False):
    if len(a) != len(b):
        return False
    return all(abs((x-y+180) % 360-180 if angular else x-y) <= EPS
               for x, y in zip(a, b))


def shifted(p, delta):
    return [x+y for x, y in zip(p, delta)]


def rect(actor):
    lo, hi = actor['bounds']
    return [lo[0], lo[1], hi[0], hi[1]]


def within(point, rectangle):
    x, y = point
    return (rectangle[0]-EPS <= x <= rectangle[2]+EPS
            and rectangle[1]-EPS <= y <= rectangle[3]+EPS)


def intersection_lengths(a, b):
    return [min(a['bounds'][1][i], b['bounds'][1][i])
            - max(a['bounds'][0][i], b['bounds'][0][i]) for i in range(3)]


def retention_check(before, after, applied):
    current = {a['name']: a for a in after}
    deltas = {a['name']: a['delta'] for a in applied['moved']}
    errors = []
    checked = 0
    components_checked = 0
    for old in before:
        if not retained(old):
            continue
        checked += 1
        new = current.get(old['name'])
        if new is None:
            errors.append({'actor': old['label'], 'field': 'missing_actor'})
            continue
        delta = deltas.get(old['name'], [0, 0, 0])
        for field in ('label', 'folder', 'class'):
            if new[field] != old[field]:
                errors.append({'actor': old['label'], 'field': field})
        for field in ('p', 'r', 's'):
            expected = shifted(old[field], delta) if field == 'p' else old[field]
            if not vector_equal(new[field], expected, angular=field == 'r'):
                errors.append({'actor': old['label'], 'field': field,
                               'expected': expected, 'actual': new[field]})
        if len(new['components']) != len(old['components']):
            errors.append({'actor': old['label'], 'field': 'component_count'})
        for index, (c0, c1) in enumerate(zip(old['components'], new['components'])):
            components_checked += 1
            for field in ('mesh', 'mats', 'collision'):
                if c0.get(field) != c1.get(field):
                    errors.append({'actor': old['label'], 'component': index,
                                   'field': field})
            for field in ('p', 'r', 's'):
                expected = shifted(c0[field], delta) if field == 'p' else c0[field]
                if not vector_equal(c1[field], expected, angular=field == 'r'):
                    errors.append({'actor': old['label'], 'component': index,
                                   'field': field, 'expected': expected,
                                   'actual': c1[field]})
        if old['components']:
            expected = [shifted(p, delta) for p in old['bounds']]
            if not all(vector_equal(x, y) for x, y in zip(new['bounds'], expected)):
                errors.append({'actor': old['label'], 'field': 'mesh_bounds'})
    for moved in applied['moved']:
        if moved['name'] not in current:
            errors.append({'actor': moved['label'], 'field': 'missing_moved_actor'})
    return {'passed': not errors, 'actors_checked': checked,
            'components_checked': components_checked, 'errors': errors}


def room_checks(before, after, rooms):
    checks = []
    for number in (3, 7, 4, 8):
        footprints = []
        for scene in (before, after):
            floors = [a for a in scene if a['folder'] == 'TF_Architecture/Floors'
                      and floor_room(a) == number]
            if not floors:
                footprints.append(None)
                continue
            footprints.append([min(rect(a)[0] for a in floors),
                               min(rect(a)[1] for a in floors),
                               max(rect(a)[2] for a in floors),
                               max(rect(a)[3] for a in floors)])
        old, new = footprints
        expected = rooms[str(number)]
        sizes = [[r[2]-r[0], r[3]-r[1]] if r else None for r in footprints]
        passed = bool(old and new and vector_equal(new, expected)
                      and vector_equal(sizes[0], sizes[1]))
        checks.append({'room': number, 'passed': passed,
                       'before_floor_inner_bounds': old,
                       'after_floor_inner_bounds': new,
                       'before_size_cm': sizes[0], 'after_size_cm': sizes[1],
                       'declared_inner_bounds': expected})
    return {'passed': all(c['passed'] for c in checks), 'rooms': checks}


def measure(scene, axis, at, center):
    # axis is the varying coordinate; the perpendicular coordinate is fixed.
    candidates = []
    for actor in scene:
        if actor['folder'] != 'TF_Architecture/Mouldings' or '_base_' not in actor['label']:
            continue
        lo, hi = actor['bounds']
        if lo[1-axis]-EPS <= at <= hi[1-axis]+EPS:
            candidates.append((lo[axis], hi[axis], actor['label']))
    low = [c for c in candidates if c[1] < center]
    high = [c for c in candidates if c[0] > center]
    if not low or not high:
        return {'width_cm': None, 'error': 'No opposing mouldings found'}
    lower = max(low, key=lambda c: c[1])
    upper = min(high, key=lambda c: c[0])
    return {'width_cm': upper[0]-lower[1],
            'lower_finished_edge_cm': lower[1],
            'upper_finished_edge_cm': upper[0],
            'lower_actor': lower[2], 'upper_actor': upper[2]}


def corridor_measurements(before, after):
    checks = []
    for name, axis, at, old_center, new_center in (
        ('room1_room5_horizontal', 1, -1200, -115, -151),
        ('room3_room4_vertical', 0, -194, 945, 1031),
        ('room7_room8_vertical', 0, 245, 945, 1031),
    ):
        old, new = measure(before, axis, at, old_center), measure(after, axis, at, new_center)
        width = new['width_cm']
        checks.append({'name': name, 'cross_section': {'axis': 'X' if axis else 'Y', 'cm': at},
                       'before': old, 'after': new,
                       'passed': width is not None and 198 <= width <= 202})
    return {'passed': all(c['passed'] for c in checks), 'measurements': checks}


def wall_checks(after, applied):
    walls = [a for a in after if a['folder'] == 'TF_Architecture/Walls']
    overlaps = []
    for a, b in itertools.combinations(walls, 2):
        dimensions = intersection_lengths(a, b)
        if all(d > EPS for d in dimensions):
            overlaps.append({'a': a['label'], 'b': b['label'],
                             'intersection_cm': dimensions})
    unmatched = [list(w) for w in applied['walls']]
    unexpected = []
    for actor in walls:
        lo, hi = actor['bounds']
        actual = [lo[0], lo[1], hi[0], hi[1], lo[2], hi[2]]
        match = next((w for w in unmatched if vector_equal(actual, w)), None)
        if match is None:
            unexpected.append({'actor': actor['label'], 'bounds': actual})
        else:
            unmatched.remove(match)
    return {'passed': not overlaps and not unmatched and not unexpected,
            'wall_count': len(walls), 'positive_volume_overlaps': overlaps,
            'missing_applied_boxes': unmatched, 'unexpected_boxes': unexpected}


def floor_checks(after, footprint):
    floors = [a for a in after if a['folder'] == 'TF_Architecture/Floors']
    overlaps = []
    for a, b in itertools.combinations(floors, 2):
        # The -8cm collision base is intentionally beneath the broken finish.
        # Only compare flat cube surfaces at the same elevation. Original
        # damaged meshes have holes and cannot be tested as solid AABB faces.
        if abs(a['bounds'][1][2]-b['bounds'][1][2]) > EPS:
            continue
        dimensions = intersection_lengths(a, b)
        if dimensions[0] > EPS and dimensions[1] > EPS:
            overlaps.append({'a': a['label'], 'b': b['label'],
                             'surface_z_cm': a['bounds'][1][2],
                             'intersection_xy_cm': dimensions[:2]})
    rectangles = [rect(a) for a in floors]
    xs = sorted(set(r[i] for r in rectangles+footprint for i in (0, 2)))
    ys = sorted(set(r[i] for r in rectangles+footprint for i in (1, 3)))
    holes = []
    checked = 0
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            if x1-x0 <= EPS or y1-y0 <= EPS:
                continue
            midpoint = [(x0+x1)/2, (y0+y1)/2]
            if not any(within(midpoint, f) for f in footprint):
                continue
            checked += 1
            if not any(within(midpoint, r) for r in rectangles):
                holes.append([x0, y0, x1, y1])
    return {'passed': not overlaps and not holes, 'flat_floor_count': len(floors),
            'same_height_surface_overlaps': overlaps,
            'collision_floor_coverage_cells': checked, 'uncovered_rectangles': holes,
            'note': 'Coverage includes the intentional -8cm collision subfloors; '
                    'source broken meshes are excluded from flat-surface overlap checks.'}


def distance_to_rect(point, r):
    return math.hypot(max(r[0]-point[0], 0, point[0]-r[2]),
                      max(r[1]-point[1], 0, point[1]-r[3]))


def navigation_check(after, footprint):
    step, radius = 10.0, 35.0
    obstacles = []
    for actor in after:
        lo, hi = actor['bounds']
        if lo[2] >= 190 or hi[2] <= 30:
            continue
        folder = actor['folder']
        architecture = folder in ('TF_Architecture/Walls', 'TF_Architecture/WallFinishes',
                                  'TF_Architecture/Mouldings', 'TF_Architecture/WallTiles')
        solid_prop = folder.startswith('TF_Rooms/') and any(
            'NO_COLLISION' not in c.get('collision', 'NO_COLLISION') for c in actor['components'])
        if architecture or solid_prop:
            obstacles.append({'actor': actor['label'], 'rect': rect(actor)})
    checks = []
    for name, window, start, goal in (
        ('horizontal_corridor', [-1690, -250, -720, -50], [-1630, -150], [-780, -150]),
        ('vertical_corridor', [920, -490, 1140, 570], [1030, -460], [1030, 540]),
    ):
        local = [o for o in obstacles if not (
            o['rect'][2] < window[0]-radius or o['rect'][0] > window[2]+radius
            or o['rect'][3] < window[1]-radius or o['rect'][1] > window[3]+radius)]

        def free_point(point):
            return (any(within(point, r) for r in footprint)
                    and all(distance_to_rect(point, o['rect']) >= radius-EPS for o in local))

        free = {(x, y) for x in range(math.ceil(window[0]/step), math.floor(window[2]/step)+1)
                for y in range(math.ceil(window[1]/step), math.floor(window[3]/step)+1)
                if free_point([x*step, y*step])}
        nearest = lambda p: min(free, key=lambda c: math.dist([c[0]*step, c[1]*step], p)) if free else None
        first, last = nearest(start), nearest(goal)
        snaps = [math.dist([c[0]*step, c[1]*step], p) if c else None
                 for c, p in ((first, start), (last, goal))]
        parents = {first: None} if first else {}
        queue = collections.deque([first] if first else [])
        while queue and last not in parents:
            current = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (current[0]+dx, current[1]+dy)
                if nxt in free and nxt not in parents and free_point(
                    [(nxt[0]+current[0])*step/2, (nxt[1]+current[1])*step/2]):
                    parents[nxt] = current
                    queue.append(nxt)
        path = []
        if last in parents:
            cursor = last
            while cursor is not None:
                path.append([cursor[0]*step, cursor[1]*step])
                cursor = parents[cursor]
            path.reverse()
        minimum = min((distance_to_rect(p, o['rect']) for p in path for o in local), default=None)
        checks.append({'name': name, 'passed': bool(path) and all(d <= 15 for d in snaps),
                       'start': start, 'goal': goal, 'endpoint_snap_cm': snaps,
                       'free_grid_cells': len(free), 'obstacle_count': len(local),
                       'path_length_cm': (len(path)-1)*step if path else None,
                       'minimum_center_obstacle_distance_cm': minimum,
                       'path_samples_every_100cm': path[::10]+(path[-1:] if path else [])})
    return {'passed': all(c['passed'] for c in checks), 'grid_cm': step,
            'player_radius_cm': radius, 'checks': checks,
            'limitations': 'Conservative world AABB checks at Z=30..190cm with visual mouldings '
                           'included; this is not Unreal NavMesh or an in-game capsule test.'}


def main():
    before, after, applied, rooms = [load(name) for name in (
        'before.json', 'after.json', 'applied.json', 'rooms.json')]
    counts = collections.Counter(a['label'] for a in after)
    duplicates = {label: count for label, count in counts.items() if count > 1}
    report = {
        'retained_actors': retention_check(before, after, applied),
        'four_rooms': room_checks(before, after, rooms),
        'corridor_clear_widths': corridor_measurements(before, after),
        'wall_solids': wall_checks(after, applied),
        'floors': floor_checks(after, applied['footprint']),
        'corridor_navigation': navigation_check(after, applied['footprint']),
        'unique_actor_labels': {'passed': not duplicates, 'duplicates': duplicates},
    }
    report['all_passed'] = all(check['passed'] for check in report.values())
    (D / 'validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({'all_passed': report['all_passed'],
                      'checks': {key: value['passed'] for key, value in report.items()
                                 if isinstance(value, dict)},
                      'report': str(D / 'validation.json')}, indent=2))
    return report


if __name__ == '__main__':
    main()
