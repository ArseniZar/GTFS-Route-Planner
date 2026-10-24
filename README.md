# GTFS Route Planner

**A GTFS-based public transport route planner using Dijkstra, A\* and Tabu Search.**

**Student project.** A console application that finds public transport routes from timetables in the **GTFS** format. It builds a graph from the timetable data, finds a route according to the chosen criterion and saves the result on an interactive HTML map.

Search parameters are entered **interactively**: after launch, the program asks for them one by one in the console.

> The program's interface and output are in **Polish**.

## Table of contents

- [Features](#features)
- [GTFS data](#gtfs-data)
- [Algorithms](#algorithms)
- [Optimization criteria](#optimization-criteria)
- [Libraries](#libraries)
- [Installation and running](#installation-and-running)
- [Usage](#usage)
- [Output examples](#output-examples)
- [Project structure](#project-structure)

---

## Features

- **Interactive input** in the console: mode, stops, criterion, start time and other parameters are requested one by one, and optional ones have defaults (just press Enter).
- **Mode 1 — route A → B** between two stops.
- **Mode 2 — round trip A → L → A:** start at A, visit the stops from the list L and return to A.
- **Two criteria:** minimum travel time (`t`) or minimum number of transfers (`p`).
- **Choice of the search algorithm** and of the **optimization strategy** for the round trip.
- **Timetable-aware search** starting from a given departure time.
- **Route table** with lines, stops, departure and arrival times, distance and number of transfers.
- **Route map** saved to `found_route_map.html`.

---

## GTFS data

The timetable data in **GTFS** (General Transit Feed Specification) format is provided by the instructor. Place the files in the `data/` directory.

GTFS is a set of related text (CSV) files. The main ones:

| File | Contents |
|---|---|
| `stops.txt` | Stops: `stop_id`, `stop_name`, coordinates |
| `routes.txt` | Lines: `route_id`, line name |
| `trips.txt` | Trips: `trip_id`, `route_id`, `service_id` |
| `stop_times.txt` | Arrival and departure times at the stops of each trip |
| `calendar.txt` | Days of the week and validity period of the timetable |
| `calendar_dates.txt` | Exceptions to the timetable (holidays, etc.) |

Stops are identified in the program by `stop_id` from `stops.txt`.

---

## Algorithms

- **Dijkstra** — route search A → B.
- **A\*** — route search A → B (alternative variant).
- **Tabu Search** — optimization of the round trip A → L → A, with the strategies `basic`, `variable_tenure`, `aspiration` and `adaptive`.

<!-- TODO: check that src/routing.py really implements Tabu Search (the name is inferred from the tenure/aspiration parameters). -->

---

## Optimization criteria

| Code | Criterion | When to choose it |
|---|---|---|
| `t` | Travel time (including waiting at transfers). **Default.** | You want to arrive as fast as possible. |
| `p` | Number of transfers | You want as few transfers as possible, even if the trip takes longer. |

Enter a lowercase Latin letter, `t` or `p`; pressing Enter selects the default (`t`).

---

## Libraries

Exact versions are listed in [`requirements.txt`](requirements.txt).

- **Data and computation:** `pandas`, `numpy`
- **Geodata:** `geopandas`, `shapely`, `pyproj`, `pyogrio`
- **Route map:** `folium`
- **Data structures:** `intervaltree`, `sortedcontainers`
- **Other:** `requests`, `pydeck`, `pypdf`

---

## Installation and running

**Python 3.11 or newer** is required.

```bash
git clone https://github.com/ArseniZar/gtfs-route-planner.git
cd gtfs-route-planner

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

Put the GTFS files into the `data/` directory before running.

After launch, the program loads the data and switches to **interactive mode**: the search parameters are entered in response to prompts in the console (see [Usage](#usage)).

---

## Usage

The program works interactively and asks for the parameters one by one. If a default value is shown, just press **Enter**.

**Mode 1 — A → B**

| Parameter | Prompt | Values | Default |
|---|---|---|---|
| Mode | `Wybierz tryb` | `1` | `1` |
| Stop A | `ID przystanku początkowego A` | `stop_id` | required |
| Stop B | `ID przystanku końcowego B` | `stop_id` | required |
| Criterion | `Kryterium` | `t` / `p` | `t` |
| Start time | `Czas startu` | `YYYY-MM-DD HH:MM:SS` | current time |
| Algorithm | `Wariant` | `dijkstra` / `astar` | `dijkstra` |

**Mode 2 — A → L → A**

| Parameter | Prompt | Values | Default |
|---|---|---|---|
| Mode | `Wybierz tryb` | `2` | `1` |
| Stop A | `ID przystanku początkowego A` | `stop_id` | required |
| List L | `Lista przystanków L` | `stop_id` values separated by `;` (e.g. `ID1;ID2`) | required |
| Criterion | `Kryterium` | `t` / `p` | `t` |
| Start time | `Czas startu` | `YYYY-MM-DD HH:MM:SS` | current time |
| Strategy | `Strategia optymalizacji` | `basic` / `variable_tenure` / `aspiration` / `adaptive` | `basic` |
| Iterations | `Liczba iteracji` | integer | `80` |

**Result:** the route table in the console and the map `found_route_map.html` (open it in a browser). The computation time is printed to `stderr`.

**Exit codes:** `0` — success, `1` — search error, `2` — input error.

---

## Output examples

`1413380` is Wrocław Główny, `1413100` is Bytom Odrzański.

Table legend: `Lp` — row number, `Linia` — line, `Od` / `Do` — from / to, `Odjazd` / `Przyjazd` — departure / arrival, `Czas` — duration, `Uwagi` — notes, `Przesiadka` — transfer, `NOGA` — leg of the round trip.

### Mode 1 (A → B), default values

```text
=== Tryb interaktywny wyszukiwania trasy ===
Wybierz tryb [1 = A->B, 2 = A->L->A] (domyślnie 1):
ID przystanku początkowego A: 1413380
ID przystanku końcowego B: 1413100
Kryterium [t = czas, p = przesiadki] (domyślnie t):
Czas startu (YYYY-MM-DD HH:MM:SS) [domyślnie 2026-10-24 16:20:42]:
Wariant ['dijkstra', 'astar'] (domyślnie dijkstra):

TRASA ZNALEZIONA: 1413380 -> 1413100
Czas: 165 min (2 h 45 min) | Dystans: 194.62 km | Przesiadki: 1
===========================================================================================================================================================
Lp   Linia        Od                             Do                             Odjazd   Przyjazd Czas     Uwagi
-----------------------------------------------------------------------------------------------------------------------------------------------------------
1    D11          Wrocław Główny                 Wrocław Muchobór               16:34    16:39    5 min    -
2    D11          Wrocław Muchobór               Wrocław Nowy Dwór              16:40    16:42    2 min    -
3    D11          Wrocław Nowy Dwór              Środa Śląska                   16:43    16:57    14 min   -
4    D11          Środa Śląska                   Legnica                        16:58    17:14    16 min   -
5    D11          Legnica                        Rzeszotary                     17:19    17:23    4 min    -
6    D11          Rzeszotary                     Raszówka                       17:24    17:28    4 min    -
7    D11          Raszówka                       Gorzelin                       17:28    17:30    2 min    -
8    D11          Gorzelin                       Chróstnik                      17:31    17:33    2 min    -
9    D11          Chróstnik                      Lubin                          17:34    17:38    4 min    -
10   D11          Lubin                          Lubin Stadion                  17:40    17:42    2 min    -
11   D11          Lubin Stadion                  Koźlice                        17:42    17:46    4 min    -
12   D11          Koźlice                        Rynarcice                      17:46    17:48    2 min    -
13   D11          Rynarcice                      Rudna Miasto                   17:49    17:52    3 min    -
14   D11          Rudna Miasto                   Rudna Gwizdanów                17:52    17:55    3 min    -
15   D11          Rudna Gwizdanów                Grębocice                      17:56    18:02    6 min    -
16   D11          Grębocice                      Głogów                         18:03    18:11    8 min    -
                  Głogów                         Głogów                         18:11    18:48    37 min   Przesiadka: D11 -> D20
17   D20          Głogów                         Głogów Huta                    18:48    18:53    5 min    -
18   D20          Głogów Huta                    Głogów Wróblin                 18:54    18:56    2 min    -
19   D20          Głogów Wróblin                 Brzeg Głogowski                18:57    18:59    2 min    -
20   D20          Brzeg Głogowski                Czerna                         18:59    19:02    3 min    -
21   D20          Czerna                         Bytom Odrzański                19:02    19:06    4 min    -
===========================================================================================================================================================
Mapa trasy zapisana do: found_route_map.html
Czas obliczeń: 0.095334 s
```

### Mode 2 (A → L → A), criterion `t`, strategy `basic`, 80 iterations

The leg tables (`NOGA 1` and `NOGA 2`) are printed in the same format as in the example above; they are shortened here.

```text
=== Tryb interaktywny wyszukiwania trasy ===
Wybierz tryb [1 = A->B, 2 = A->L->A] (domyślnie 1): 2
ID przystanku początkowego A: 1413380
Lista przystanków L (rozdzielona średnikami ';'): 1413100
Kryterium [t = czas, p = przesiadki] (domyślnie t): t
Czas startu (YYYY-MM-DD HH:MM:SS) [domyślnie 2026-10-24 16:21:55]:
Strategia optymalizacji ['basic', 'variable_tenure', 'aspiration', 'adaptive'] (domyślnie basic):
Liczba iteracji [domyślnie 80]:

OPTYMALNY OBIEG: 1413380 -> 1413100 -> 1413380
Całkowity czas: 331 min (5 h 31 min) | Całkowite przesiadki: 1 | Wartość zoptymalizowana: 19865
================================================================================================================================================================

NOGA 1: 1413380 -> 1413100

TRASA ZNALEZIONA: 1413380 -> 1413100
Czas: 164 min (2 h 44 min) | Dystans: 194.62 km | Przesiadki: 1
[...]

NOGA 2: 1413100 -> 1413380

TRASA ZNALEZIONA: 1413100 -> 1413380
Czas: 167 min (2 h 47 min) | Dystans: 195.68 km | Przesiadki: 0
[...]
Mapa trasy zapisana do: found_route_map.html
Czas obliczeń: 0.157459 s
```

---

## Project structure

```text
gtfs-route-planner/
├── data/                # GTFS data
├── docs/                # additional materials
├── src/
│   ├── loader.py        # GTFS loading
│   ├── graph.py         # graph construction
│   ├── routing.py       # route search algorithms
│   ├── interface.py     # console input and output
│   └── visualizer.py    # route map (HTML)
├── main.py              # entry point
└── requirements.txt     # dependencies
```

<!-- TODO: check the src/ tree against the real one: file names are reconstructed from the imports in main.py. -->

---

Author: [ArseniZar](https://github.com/ArseniZar)