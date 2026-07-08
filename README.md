# Smart Cleaning Robot

![C++](https://img.shields.io/badge/C++-17-00599C?style=flat&logo=cplusplus&logoColor=white)
![OOP](https://img.shields.io/badge/Paradigm-Object--Oriented-blueviolet?style=flat)
![Algorithm](https://img.shields.io/badge/Algorithm-Pathfinding-22c55e?style=flat)

> A C++ autonomous cleaning robot that reads a text-file map, detects obstacles and passable cells, plans an optimal cleaning path, and navigates the entire area without revisiting cleaned tiles.

---

## Overview

The robot is initialized with a grid-based map loaded from a `.txt` file. Each cell is marked as either an obstacle or a passable tile. The robot then computes a traversal path that covers all reachable cells efficiently, simulating how a real-world autonomous vacuum cleaner would operate.

## Features

- Text-file map parsing — define any grid layout with obstacle and passage markers
- Automatic obstacle detection and avoidance
- Optimal path planning to maximize coverage with minimal backtracking
- Clean-coverage tracking — knows which cells have been visited
- OOP design with separate classes for the robot, map, and pathfinder
- Cleaning report generated after each run (`TemizlikRaporu.txt`)

## Tech Stack

- **Language:** C++17
- **Paradigm:** Object-Oriented Programming
- **Input Format:** TXT grid map files
- **Output:** Console traversal log + cleaning report file

## Project Structure

```
Smart-Cleaning-Robot/
├── main.cpp            # Entry point and simulation loop
├── Harita.txt          # Sample grid map (obstacles + passages)
├── TemizlikRaporu.txt  # Generated cleaning report
└── .gitignore (if present)
```

## Getting Started

### Prerequisites

- GCC/G++ with C++17 support, or MSVC / Clang

### Build & Run

```bash
git clone https://github.com/ErdoganPeker/Smart-Cleaning-Robot.git
cd Smart-Cleaning-Robot
g++ -std=c++17 -o cleaning_robot main.cpp
./cleaning_robot Harita.txt
```

On Windows:

```bash
g++ -std=c++17 -o cleaning_robot.exe main.cpp
cleaning_robot.exe Harita.txt
```

## Map Format

Maps are plain-text grid files where each character represents one cell:

```
# # # # # # #
# . . # . . #
# . # # . . #
# . . . . . #
# # # # # # #
```

- `#` — obstacle (wall/furniture)
- `.` — passable tile (to be cleaned)

## Sample Output

```
Robot starting at (1,1)
Cleaning (1,1) ... done
Moving to (1,2) ... Cleaning ... done
...
Cleaning complete. Tiles cleaned: 18 / 18
Report saved to TemizlikRaporu.txt
```

## Author

**Erdogan Yasin Peker** — Computer Engineer

[GitHub](https://github.com/ErdoganPeker) · [LinkedIn](https://www.linkedin.com/in/erdogan-yasin-peker-b107ba24b/)
