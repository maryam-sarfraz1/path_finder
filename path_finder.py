import tkinter as tk
from tkinter import messagebox
import heapq
import random
import time
import math

# Colors
C_EMPTY    = "#ffffff"
C_WALL     = "#2d2d2d"
C_START    = "#27ae60"
C_GOAL     = "#e74c3c"
C_VISITED  = "#aed6f1"
C_FRONTIER = "#f9e79f"
C_PATH     = "#f39c12"
C_AGENT    = "#8e44ad"

CELL = 25

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def euclidean(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def get_neighbors(node, rows, cols, grid):
    r, c = node
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
            yield (nr, nc)

def reconstruct(came_from, goal):
    path, node = [], goal
    while node:
        path.append(node)
        node = came_from[node]
    return path[::-1]

def astar(grid, start, goal, h):
    rows, cols = len(grid), len(grid[0])
    heap = [(0, start)]
    came_from = {start: None}
    g = {start: 0}
    visited = []
    while heap:
        _, cur = heapq.heappop(heap)
        visited.append(cur)
        if cur == goal:
            return reconstruct(came_from, goal), visited
        for nb in get_neighbors(cur, rows, cols, grid):
            ng = g[cur] + 1
            if nb not in g or ng < g[nb]:
                g[nb] = ng
                came_from[nb] = cur
                heapq.heappush(heap, (ng + h(nb, goal), nb))
    return None, visited

def gbfs(grid, start, goal, h):
    rows, cols = len(grid), len(grid[0])
    heap = [(h(start, goal), start)]
    came_from = {start: None}
    visited = []
    while heap:
        _, cur = heapq.heappop(heap)
        visited.append(cur)
        if cur == goal:
            return reconstruct(came_from, goal), visited
        for nb in get_neighbors(cur, rows, cols, grid):
            if nb not in came_from:
                came_from[nb] = cur
                heapq.heappush(heap, (h(nb, goal), nb))
    return None, visited

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Pathfinding Agent")
        self.root.resizable(False, False)

        self.ROWS = 20
        self.COLS = 25
        self.grid = [[0]*self.COLS for _ in range(self.ROWS)]
        self.start = (0, 0)
        self.goal  = (self.ROWS-1, self.COLS-1)

        self.algo      = tk.StringVar(value="A*")
        self.heuristic = tk.StringVar(value="Manhattan")
        self.draw_mode = tk.StringVar(value="Wall")
        self.dynamic   = tk.BooleanVar(value=False)

        self.path       = []
        self.agent_step = 0
        self.agent_pos  = None
        self.running    = False
        self.after_id   = None

        self.nv_var = tk.StringVar(value="0")
        self.pc_var = tk.StringVar(value="0")
        self.et_var = tk.StringVar(value="0 ms")
        self.rp_var = tk.StringVar(value="0")

        self._build_ui()
        self._redraw()

    def _build_ui(self):
        # Row 1: Algorithm + Heuristic + Draw mode
        top = tk.Frame(self.root, bg="#f0f0f0", pady=6, padx=8)
        top.pack(fill="x")

        tk.Label(top, text="Algorithm:", bg="#f0f0f0").pack(side="left")
        for a in ["A*", "GBFS"]:
            tk.Radiobutton(top, text=a, variable=self.algo, value=a, bg="#f0f0f0").pack(side="left")

        tk.Label(top, text="   Heuristic:", bg="#f0f0f0").pack(side="left")
        for h in ["Manhattan", "Euclidean"]:
            tk.Radiobutton(top, text=h, variable=self.heuristic, value=h, bg="#f0f0f0").pack(side="left")

        tk.Label(top, text="   Draw:", bg="#f0f0f0").pack(side="left")
        for m in ["Wall", "Erase", "Start", "Goal"]:
            tk.Radiobutton(top, text=m, variable=self.draw_mode, value=m, bg="#f0f0f0").pack(side="left")

        tk.Checkbutton(top, text="   Dynamic Mode", variable=self.dynamic, bg="#f0f0f0").pack(side="left")

        # Row 2: Buttons + density
        btn_frame = tk.Frame(self.root, bg="#e8e8e8", pady=4, padx=8)
        btn_frame.pack(fill="x")

        for text, cmd in [
            ("Generate Maze", self.generate_maze),
            ("Clear", self.clear_grid),
            ("Run", self.run_search),
            ("Stop", self.stop),
            ("Reset View", self.reset_view),
        ]:
            tk.Button(btn_frame, text=text, command=cmd, width=11,
                      relief="groove", bg="#dcdcdc").pack(side="left", padx=3)

        tk.Label(btn_frame, text="  Density:", bg="#e8e8e8").pack(side="left")
        self.density = tk.Scale(btn_frame, from_=10, to=60, orient="horizontal",
                                length=100, bg="#e8e8e8", showvalue=True, highlightthickness=0)
        self.density.set(30)
        self.density.pack(side="left")

        # Canvas
        self.canvas = tk.Canvas(self.root,
                                width=self.COLS*CELL,
                                height=self.ROWS*CELL,
                                bg="white", cursor="crosshair")
        self.canvas.pack(padx=8, pady=4)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<B1-Motion>", self._click)

        # Metrics
        bar = tk.Frame(self.root, bg="#f0f0f0", pady=4, padx=8)
        bar.pack(fill="x")
        for label, var in [("Nodes Visited:", self.nv_var), ("Path Cost:", self.pc_var),
                            ("Time:", self.et_var), ("Re-plans:", self.rp_var)]:
            tk.Label(bar, text=label, bg="#f0f0f0", font=("Arial",9)).pack(side="left", padx=(8,2))
            tk.Label(bar, textvariable=var, bg="#f0f0f0", font=("Arial",9,"bold"), fg="#1a5276").pack(side="left")

        # Legend
        leg = tk.Frame(self.root, bg="#f0f0f0", pady=3, padx=8)
        leg.pack(fill="x")
        for color, name in [(C_START,"Start"),(C_GOAL,"Goal"),(C_WALL,"Wall"),
                            (C_VISITED,"Visited"),(C_PATH,"Path"),(C_AGENT,"Agent")]:
            tk.Label(leg, bg=color, width=2, relief="solid").pack(side="left", padx=(8,2))
            tk.Label(leg, text=name, bg="#f0f0f0", font=("Arial",8)).pack(side="left")

    def _redraw(self):
        self.canvas.delete("all")
        for r in range(self.ROWS):
            for c in range(self.COLS):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c, color=None):
        if color is None:
            if (r,c) == self.start:    color = C_START
            elif (r,c) == self.goal:   color = C_GOAL
            elif self.grid[r][c] == 1: color = C_WALL
            else:                       color = C_EMPTY
        x0, y0 = c*CELL, r*CELL
        self.canvas.create_rectangle(x0, y0, x0+CELL, y0+CELL,
                                     fill=color, outline="#cccccc", tags=f"c{r}_{c}")

    def _color(self, r, c, color):
        self.canvas.delete(f"c{r}_{c}")
        x0, y0 = c*CELL, r*CELL
        self.canvas.create_rectangle(x0, y0, x0+CELL, y0+CELL,
                                     fill=color, outline="#cccccc", tags=f"c{r}_{c}")

    def _click(self, e):
        r, c = e.y // CELL, e.x // CELL
        if not (0 <= r < self.ROWS and 0 <= c < self.COLS):
            return
        m = self.draw_mode.get()
        if m == "Wall" and (r,c) not in (self.start, self.goal):
            self.grid[r][c] = 1
            self._color(r, c, C_WALL)
        elif m == "Erase":
            self.grid[r][c] = 0
            self._color(r, c, C_EMPTY)
        elif m == "Start":
            self.grid[self.start[0]][self.start[1]] = 0
            self._color(self.start[0], self.start[1], C_EMPTY)
            self.start = (r, c)
            self.grid[r][c] = 0
            self._color(r, c, C_START)
        elif m == "Goal":
            self.grid[self.goal[0]][self.goal[1]] = 0
            self._color(self.goal[0], self.goal[1], C_EMPTY)
            self.goal = (r, c)
            self.grid[r][c] = 0
            self._color(r, c, C_GOAL)

    def generate_maze(self):
        self.stop()
        d = self.density.get() / 100

        # Protect a 2-cell radius around start and goal so path can always begin/end
        protected = set()
        for (sr, sc) in (self.start, self.goal):
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    protected.add((sr + dr, sc + dc))

        h = manhattan if self.heuristic.get() == "Manhattan" else euclidean

        # Keep regenerating until a valid path exists
        while True:
            self.grid = [[0] * self.COLS for _ in range(self.ROWS)]
            for r in range(self.ROWS):
                for c in range(self.COLS):
                    if (r, c) not in protected and random.random() < d:
                        self.grid[r][c] = 1

            path, _ = astar(self.grid, self.start, self.goal, h)
            if path is not None:
                break  # Valid maze found

        self._reset_metrics()
        self._redraw()

    def clear_grid(self):
        self.stop()
        self.grid = [[0]*self.COLS for _ in range(self.ROWS)]
        self._reset_metrics()
        self._redraw()

    def reset_view(self):
        self.stop()
        self._reset_metrics()
        self._redraw()

    def _reset_metrics(self):
        self.nv_var.set("0"); self.pc_var.set("0")
        self.et_var.set("0 ms"); self.rp_var.set("0")
        self.path = []; self.agent_step = 0; self.agent_pos = None

    def run_search(self):
        self.stop()
        self._reset_metrics()
        self._redraw()

        h = manhattan if self.heuristic.get() == "Manhattan" else euclidean
        t0 = time.perf_counter()
        if self.algo.get() == "A*":
            path, visited = astar(self.grid, self.start, self.goal, h)
        else:
            path, visited = gbfs(self.grid, self.start, self.goal, h)
        elapsed = (time.perf_counter() - t0) * 1000

        self.et_var.set(f"{elapsed:.2f} ms")
        self.nv_var.set(str(len(visited)))

        if path is None:
            messagebox.showwarning("No Path", "No path found!")
            return

        self.pc_var.set(str(len(path)-1))
        self.path = path

        for r, c in visited:
            if (r,c) not in (self.start, self.goal):
                self._color(r, c, C_VISITED)
        for r, c in path:
            if (r,c) not in (self.start, self.goal):
                self._color(r, c, C_PATH)

        self.running = True
        self.agent_step = 0
        self.agent_pos = self.start
        self._step_agent()

    def _step_agent(self):
        if not self.running:
            return
        if self.agent_step < len(self.path):
            if self.agent_pos and self.agent_pos not in (self.start, self.goal):
                self._color(self.agent_pos[0], self.agent_pos[1], C_PATH)
            self.agent_pos = self.path[self.agent_step]
            r, c = self.agent_pos
            self._color(r, c, C_AGENT)
            self.agent_step += 1

            if self.dynamic.get() and random.random() < 0.10:
                self._spawn_obstacle()

            self.after_id = self.root.after(100, self._step_agent)
        else:
            self.running = False

    def _spawn_obstacle(self):
        future = set(self.path[self.agent_step:])
        for _ in range(30):
            r = random.randint(0, self.ROWS-1)
            c = random.randint(0, self.COLS-1)
            if (self.grid[r][c] == 0 and (r,c) not in (self.start, self.goal, self.agent_pos)):
                self.grid[r][c] = 1
                self._color(r, c, C_WALL)
                if (r, c) in future:
                    self._replan()
                break

    def _replan(self):
        h = manhattan if self.heuristic.get() == "Manhattan" else euclidean
        t0 = time.perf_counter()
        if self.algo.get() == "A*":
            new_path, new_visited = astar(self.grid, self.agent_pos, self.goal, h)
        else:
            new_path, new_visited = gbfs(self.grid, self.agent_pos, self.goal, h)
        elapsed = (time.perf_counter() - t0) * 1000

        self.et_var.set(f"{elapsed:.2f} ms")
        self.nv_var.set(str(int(self.nv_var.get()) + len(new_visited)))
        self.rp_var.set(str(int(self.rp_var.get()) + 1))

        if new_path is None:
            messagebox.showwarning("Blocked", "Agent is completely blocked!")
            self.running = False
            return

        self.pc_var.set(str(int(self.pc_var.get()) + len(new_path)-1))
        self.path = new_path
        self.agent_step = 0
        for r, c in new_path:
            if (r,c) not in (self.start, self.goal):
                self._color(r, c, C_PATH)

    def stop(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()