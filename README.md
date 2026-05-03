# Pacman-with-A-and-A-inverse-Ghosts
A classic Pac-Man arcade game built with Python and Pygame, featuring intelligent ghost enemies powered by the **A\* (A-Star) pathfinding algorithm**. Each ghost has its own unique hunting strategy, just like the original 1980 arcade game.
---

## 📸 Preview

> Classic 28×31 maze · 4 intelligent ghosts · Power pellets · Score tracking

---

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Pygame

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pacman-astar.git
cd pacman-astar

# Install dependencies
pip install pygame

# Run the game
python pacman.py
```

---

## 🕹️ Controls

| Key | Action |
|-----|--------|
| `Arrow Keys` / `WASD` | Move Pac-Man |
| `R` | Restart game |
| `Escape` | Quit |

---

## 🧠 How the A\* Algorithm Works

Each ghost calculates the **shortest path** to its target cell every step using A\* search:

- **Open list** — candidate cells sorted by `f = g + h`
- **g cost** — actual steps taken from the ghost's current position
- **h (heuristic)** — Manhattan distance to the target
- **Path reconstruction** — the ghost moves one cell at a time along the optimal path

This means ghosts don't wander randomly — they actively navigate around walls and find the most efficient route to reach you.

### Frightened Mode (Power Pellet)

When Pac-Man eats a power pellet, the A\* target is **inverted** — ghosts maximize distance from Pac-Man instead of minimizing it, making them actively flee.

---

## 👻 Ghost Personalities

Each of the 4 ghosts uses A\* pathfinding but with different **target selection strategies**, replicating the original arcade behavior:

| Ghost | Color | Name | Chase Strategy |
|-------|-------|------|----------------|
| 🔴 | Red | **Blinky** | Targets Pac-Man's exact current cell — relentless direct chaser |
| 🩷 | Pink | **Pinky** | Targets 4 cells *ahead* of Pac-Man — tries to ambush |
| 🩵 | Cyan | **Inky** | Uses a flanking intercept position |
| 🟠 | Orange | **Clyde** | Chases when far away, retreats to corner when close |

All ghosts also switch between **Chase** and **Scatter** modes on a timer — during scatter mode they retreat to their assigned corner of the maze.

---

## ✨ Features

- ✅ Classic 28×31 Pac-Man maze layout
- ✅ A\* pathfinding for all 4 ghosts
- ✅ Unique ghost personalities (Blinky, Pinky, Inky, Clyde)
- ✅ Chase / Scatter / Frightened / Dead ghost states
- ✅ Power pellets that trigger frightened mode
- ✅ Tunnel wrapping on left/right edges
- ✅ Ghost house — dead ghosts return and revive
- ✅ Animated Pac-Man mouth and ghost wiggle
- ✅ HUD showing score, level, lives, and each ghost's current AI mode
- ✅ Win/Game Over screens

---

## 🗂️ Project Structure

```
pacman-astar/
│
├── pacman.py       # Main game file (all-in-one)
└── README.md       # This file
```

### Key Classes

| Class | Responsibility |
|-------|---------------|
| `Game` | Main game loop, collision detection, state management |
| `Pacman` | Player movement, input handling, animation |
| `Ghost` | A\* pathfinding, mode switching, personality logic |

### Key Functions

| Function | Description |
|----------|-------------|
| `astar(grid, start, goal)` | Core A\* pathfinding — returns the next step toward the goal |
| `heuristic(a, b)` | Manhattan distance used as the A\* heuristic |
| `Ghost.get_target()` | Selects the target cell based on ghost personality and current mode |
| `Ghost.frighten()` | Activates frightened mode with a countdown timer |

---

## 🛠️ Tech Stack

- **Python 3** — core language
- **Pygame** — rendering, input, game loop
- **heapq** — priority queue for A\* open list
- **math / collections** — animation and pathfinding utilities

---

## 📖 Algorithm Reference

If you want to learn more about the A\* algorithm used in this project:

- [A* Search Algorithm — Wikipedia](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [Pac-Man Ghost AI explained — GameInternals](https://www.gamedeveloper.com/design/the-pac-man-dossier)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
