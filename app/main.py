from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Optional
from collections import deque
import uvicorn, random, os

app = FastAPI()
_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(_dir, "templates"))

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Tunable robot parameters
BATTERY_CAPACITY = 150      # max battery, in "moves"
LOW_BATTERY_THRESHOLD = 30  # trigger a trip to the charging station at/under this level
CHARGE_TICKS_TOTAL = 10     # number of animation ticks a full recharge takes
MAX_SIM_TICKS = 9000        # safety cap so a run can never loop forever

# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------

def in_bounds(r, c, rows, cols):
    return 0 <= r < rows and 0 <= c < cols


def walkable(cell):
    return cell in ('D', 'C')


def bfs_path(grid, start, goal):
    """Shortest path (list of (r,c), inclusive) between two walkable cells, or None."""
    if start == goal:
        return [start]
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        r, c = cur
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, rows, cols) and (nr, nc) not in prev and walkable(grid[nr][nc]):
                prev[(nr, nc)] = cur
                q.append((nr, nc))
    if goal not in prev:
        return None
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def bfs_nearest_in_set(grid, start, targets):
    """BFS outward from start, returns path (inclusive) to the closest cell in `targets`
    (start itself excluded), or None if nothing reachable."""
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    prev = {start: None}
    found = None
    while q:
        cur = q.popleft()
        if cur in targets and cur != start:
            found = cur
            break
        r, c = cur
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, rows, cols) and (nr, nc) not in prev and walkable(grid[nr][nc]):
                prev[(nr, nc)] = cur
                q.append((nr, nc))
    if found is None:
        return None
    path = []
    cur = found
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def build_zigzag_order(grid):
    """Fixed boustrophedon (row-by-row, alternating direction) visiting order."""
    rows, cols = len(grid), len(grid[0])
    order = []
    for r in range(1, rows - 1):
        cols_range = range(1, cols - 1) if r % 2 == 1 else range(cols - 2, 0, -1)
        for c in cols_range:
            if walkable(grid[r][c]):
                order.append((r, c))
    return order


# ---------------------------------------------------------------------------
# Room generation: walls + furniture obstacles + per-cell dirt level + charger
# ---------------------------------------------------------------------------

def generate_room(rows=18, cols=24, seed=42):
    random.seed(seed)
    grid = [['D' for _ in range(cols)] for _ in range(rows)]

    # outer walls
    for r in range(rows):
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                grid[r][c] = 'W'

    # scattered single-cell walls
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if random.random() < 0.07:
                grid[r][c] = 'W'

    # furniture blobs (sofas/tables) - visually and functionally distinct from walls
    furniture_attempts = int(rows * cols * 0.06)
    for _ in range(furniture_attempts):
        r = random.randint(1, rows - 2)
        c = random.randint(1, cols - 2)
        if grid[r][c] == 'D':
            grid[r][c] = 'F'
            if random.random() < 0.5:
                dr, dc = random.choice([(0, 1), (1, 0)])
                nr, nc = r + dr, c + dc
                if 1 <= nr <= rows - 2 and 1 <= nc <= cols - 2 and grid[nr][nc] == 'D':
                    grid[nr][nc] = 'F'

    # keep only the largest connected floor component reachable -> guarantees every
    # dirty cell and the charging station are always reachable by BFS
    visited = set()
    components = []
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 'D' and (r, c) not in visited:
                comp = []
                dq = deque([(r, c)])
                visited.add((r, c))
                while dq:
                    cr, cc = dq.popleft()
                    comp.append((cr, cc))
                    for dr, dc in DIRS:
                        nr, nc = cr + dr, cc + dc
                        if in_bounds(nr, nc, rows, cols) and grid[nr][nc] == 'D' and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            dq.append((nr, nc))
                components.append(comp)

    if not components:
        grid[rows // 2][cols // 2] = 'D'
        components = [[(rows // 2, cols // 2)]]

    main_comp = max(components, key=len)
    main_set = set(main_comp)
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 'D' and (r, c) not in main_set:
                grid[r][c] = 'F'  # unreachable pocket -> treat as extra furniture

    # charging station: floor cell closest to the room center
    cy, cx = rows // 2, cols // 2
    station = min(main_comp, key=lambda p: abs(p[0] - cy) + abs(p[1] - cx))
    grid[station[0]][station[1]] = 'C'

    # per-cell dirt level (0 = clean, 1-3 = needs that many passes to fully clean)
    dirt = {}
    dirt_choices = [1, 1, 2, 2, 3]
    for (r, c) in main_comp:
        dirt[(r, c)] = 0 if (r, c) == station else random.choice(dirt_choices)

    return grid, dirt, [station]


# ---------------------------------------------------------------------------
# Simulation: shared engine for both algorithms (battery + charging logic
# is identical for both, only target-selection differs)
# ---------------------------------------------------------------------------

def run_simulation(grid, dirt_init, stations, start, algo,
                    battery_capacity=BATTERY_CAPACITY,
                    low_threshold=LOW_BATTERY_THRESHOLD,
                    charge_ticks_total=CHARGE_TICKS_TOTAL,
                    max_ticks=MAX_SIM_TICKS):
    dirt = dict(dirt_init)
    stations_set = set(stations)
    r, c = start
    battery = battery_capacity

    path = [{"r": r, "c": c, "battery": battery, "action": "start", "dirt": dirt.get((r, c), 0)}]
    charge_count = 0
    moves = 0

    dirty_initial = {p for p, v in dirt.items() if v > 0}
    total_dirt_units = sum(dirt.values())

    zz_order = build_zigzag_order(grid) if algo == "zigzag" else None
    zz_n = len(zz_order) if zz_order else 0
    zz_idx = 0

    route = []             # queued cells still to walk through for the current target
    current_target = None  # target survives battery interruptions - never silently abandoned
    mode = "normal"         # normal | to_station | charging
    charge_ticks_left = 0

    def all_clean():
        return all(v <= 0 for v in dirt.values())

    ticks_guard = 0
    while not all_clean() and ticks_guard < max_ticks:
        ticks_guard += 1

        if mode == "charging":
            gain = max(1, battery_capacity // charge_ticks_total)
            battery = min(battery_capacity, battery + gain)
            path.append({"r": r, "c": c, "battery": battery, "action": "charging", "dirt": 0})
            charge_ticks_left -= 1
            if battery >= battery_capacity or charge_ticks_left <= 0:
                battery = battery_capacity
                mode = "normal"
            continue

        # low battery -> (re)route to nearest charging station, unless already heading there.
        # `current_target` is left untouched so the interrupted cleaning goal is resumed after charging.
        if mode != "to_station" and battery <= low_threshold and (r, c) not in stations_set:
            station_route = bfs_nearest_in_set(grid, (r, c), stations_set)
            if station_route:
                route = station_route[1:]
                mode = "to_station"

        if mode == "to_station":
            if not route:
                mode = "charging"
                charge_count += 1
                charge_ticks_left = charge_ticks_total
                continue
            nr, nc = route.pop(0)
            r, c = nr, nc
            battery = max(0, battery - 1)
            moves += 1
            if dirt.get((r, c), 0) > 0:
                dirt[(r, c)] -= 1
            path.append({"r": r, "c": c, "battery": battery, "action": "move", "dirt": dirt.get((r, c), 0)})
            continue

        # ---- normal mode ----
        if current_target is None:
            if algo == "smart":
                if dirt.get((r, c), 0) > 0:
                    current_target = (r, c)
                else:
                    targets = {p for p, v in dirt.items() if v > 0}
                    if not targets:
                        break
                    found = bfs_nearest_in_set(grid, (r, c), targets)
                    if not found:
                        break
                    current_target = found[-1]
            else:  # naive fixed zigzag sweep - blindly re-cycles the whole room in the
                    # same order, ignoring dirt state, until everything is clean
                if zz_n == 0:
                    break
                current_target = zz_order[zz_idx % zz_n]
                zz_idx += 1
            route = []

        if current_target == (r, c):
            # standing on the target -> clean in place, no travel cost
            battery = max(0, battery - 1)
            moves += 1
            if dirt.get((r, c), 0) > 0:
                dirt[(r, c)] -= 1
            path.append({"r": r, "c": c, "battery": battery, "action": "clean", "dirt": dirt.get((r, c), 0)})
            current_target = None
            continue

        if not route:
            full = bfs_path(grid, (r, c), current_target)
            if not full or len(full) < 2:
                # unreachable/degenerate - drop it and pick a fresh target next tick
                current_target = None
                continue
            route = full[1:]

        nr, nc = route.pop(0)
        r, c = nr, nc
        battery = max(0, battery - 1)
        moves += 1
        if dirt.get((r, c), 0) > 0:
            dirt[(r, c)] -= 1
        path.append({"r": r, "c": c, "battery": battery, "action": "move", "dirt": dirt.get((r, c), 0)})
        if (r, c) == current_target:
            current_target = None  # reached - a fresh target will be picked next tick

    cleaned_cells = sum(1 for p in dirty_initial if dirt.get(p, 0) <= 0)
    remaining_units = sum(max(0, v) for v in dirt.values())
    cell_efficiency = round(cleaned_cells / max(1, len(dirty_initial)) * 100, 1)
    dirt_efficiency = round((total_dirt_units - remaining_units) / max(1, total_dirt_units) * 100, 1)
    duration_seconds = round(moves * 0.3 + charge_count * charge_ticks_total * 1.0, 1)

    return {
        "algo": algo,
        "path": path,
        "steps": len(path),
        "moves": moves,
        "charge_count": charge_count,
        "cleaned_cells": cleaned_cells,
        "total_dirty_cells": len(dirty_initial),
        "cell_efficiency": cell_efficiency,
        "dirt_efficiency": dirt_efficiency,
        "duration_seconds": duration_seconds,
        "battery_capacity": battery_capacity,
        "low_threshold": low_threshold,
        "finished": all_clean(),
    }


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def dirt_to_map(grid, dirt):
    rows, cols = len(grid), len(grid[0])
    return [[dirt.get((r, c), 0) for c in range(cols)] for r in range(rows)]


def run_and_package(seed, algo, rows=18, cols=24):
    if algo not in ("zigzag", "smart"):
        algo = "smart"
    grid, dirt, stations = generate_room(rows=rows, cols=cols, seed=seed)
    result = run_simulation(grid, dirt, stations, stations[0], algo)
    result["grid"] = grid
    result["dirt_map"] = dirt_to_map(grid, dirt)
    result["stations"] = [[s[0], s[1]] for s in stations]
    result["seed"] = seed
    result["rows"] = rows
    result["cols"] = cols
    # legacy-compatible fields
    result["cleaned"] = result["cleaned_cells"]
    result["total"] = result["total_dirty_cells"]
    result["efficiency"] = result["cell_efficiency"]
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_seed": 42})


@app.get("/simulate")
async def simulate_endpoint(algo: str = "smart", seed: int = 42):
    return run_and_package(seed, algo)


@app.get("/new")
async def new_room(seed: Optional[int] = None, algo: str = "smart"):
    if seed is None:
        seed = random.randint(1, 1_000_000)
    return run_and_package(seed, algo)


@app.get("/compare")
async def compare(seed: int = 42):
    grid, dirt, stations = generate_room(seed=seed)
    zigzag_result = run_simulation(grid, dirt, stations, stations[0], "zigzag")
    smart_result = run_simulation(grid, dirt, stations, stations[0], "smart")

    dmap = dirt_to_map(grid, dirt)
    stations_out = [[s[0], s[1]] for s in stations]
    for res in (zigzag_result, smart_result):
        res["grid"] = grid
        res["dirt_map"] = dmap
        res["stations"] = stations_out

    summary = {
        "seed": seed,
        "steps_diff": zigzag_result["steps"] - smart_result["steps"],
        "moves_diff": zigzag_result["moves"] - smart_result["moves"],
        "charge_diff": zigzag_result["charge_count"] - smart_result["charge_count"],
        "faster_algo": "smart" if smart_result["steps"] <= zigzag_result["steps"] else "zigzag",
        "time_saved_seconds": round(zigzag_result["duration_seconds"] - smart_result["duration_seconds"], 1),
    }
    return {"seed": seed, "zigzag": zigzag_result, "smart": smart_result, "summary": summary}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5010)
