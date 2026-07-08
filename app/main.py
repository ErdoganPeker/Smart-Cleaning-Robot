from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn, json, random, os

app = FastAPI()
_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(_dir, "templates"))

def generate_room(rows=18, cols=24, seed=42):
    random.seed(seed)
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if r == 0 or r == rows-1 or c == 0 or c == cols-1:
                row.append('W')
            elif random.random() < 0.12:
                row.append('W')
            else:
                row.append('D')
        grid.append(row)
    return grid

def simulate(grid):
    rows, cols = len(grid), len(grid[0])
    path = []
    cleaned = set()
    for r in range(1, rows-1):
        cols_range = range(1, cols-1) if r % 2 == 1 else range(cols-2, 0, -1)
        for c in cols_range:
            if grid[r][c] != 'W':
                path.append([r, c])
                cleaned.add((r, c))
    total = sum(1 for row in grid for cell in row if cell == 'D')
    return path, len(cleaned), total

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    grid = generate_room()
    path, cleaned, total = simulate(grid)
    eff = round(cleaned/max(1,total)*100, 1)
    return templates.TemplateResponse("index.html", {"request": request, "grid": json.dumps(grid), "path": json.dumps(path), "cleaned": cleaned, "total": total, "efficiency": eff})

@app.get("/new")
async def new_room(seed: int = 99):
    grid = generate_room(seed=seed)
    path, cleaned, total = simulate(grid)
    return {"grid": grid, "path": path, "cleaned": cleaned, "total": total, "efficiency": round(cleaned/max(1,total)*100,1)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5010)
