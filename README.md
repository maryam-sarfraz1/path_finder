# Dynamic Pathfinding Agent

A GUI-based pathfinding simulator built with **Tkinter** implementing:
- **Greedy Best-First Search (GBFS)** — `f(n) = h(n)`
- **A\* Search** — `f(n) = g(n) + h(n)`
- **Dynamic Obstacles** with real-time re-planning

---

## Requirements

- Python 3.8+
- Tkinter (included with standard Python on Windows/macOS)

On Ubuntu/Debian:
```bash
sudo apt-get install python3-tk
```

---

## How to Run

```bash
python dynamic_pathfinding.py
```

---

## Features

| Feature | Description |
|---|---|
| Grid Sizing | Set custom rows & columns (5–50 rows, 5–80 cols) |
| Random Map | Generate maze with user-defined obstacle density |
| Interactive Editor | Left-click to toggle walls; right-click to remove |
| Start/Goal Placement | Select "Start" or "Goal" mode and click to place |
| Algorithm Toggle | Switch between A* and GBFS |
| Heuristic Toggle | Choose Manhattan, Euclidean, or Diagonal |
| Animation Speed | Adjustable via slider (10–300 ms per step) |
| Dynamic Mode | New obstacles spawn mid-navigation |
| Re-planning | Agent instantly replans if path is blocked |
| Metrics | Nodes visited, path cost, exec time, re-plans |

---

## Color Legend

| Color | Meaning |
|---|---|
| 🔵 Cyan | Start node |
| 🔴 Pink | Goal node |
| 🟡 Yellow | Frontier (open list) |
| 🔵 Blue | Visited (closed list) |
| 🟢 Green | Final path |
| ⬛ Dark | Empty cell |
| 🔘 Gray | Wall/obstacle |

---

## Algorithm Notes

### A* Search
- Uses `f(n) = g(n) + h(n)`
- Optimal and complete (with admissible heuristic)
- Generally explores fewer nodes than GBFS

### Greedy Best-First Search
- Uses `f(n) = h(n)` only
- Faster but not guaranteed optimal
- Can get stuck in local minima

### Heuristics
- **Manhattan**: Best for 4-directional movement (default)
- **Euclidean**: Good when diagonal movement is conceptually valid
- **Diagonal (Chebyshev)**: Min of dx/dy — useful for 8-directional grids

---

## Dynamic Mode
Enable the checkbox to spawn random obstacles during navigation.  
If a new wall blocks the agent's current path, the agent immediately calls the selected algorithm from its current position to find a new route.
