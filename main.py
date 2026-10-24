import sys
from pathlib import Path
from time import perf_counter

from src.graph import GTFSGraph
from src.loader import GTFSDataLoader
from src.routing import GTFSSearchRoute
from src.interface import SearchInterface
from src.visualizer import GTFSVisualizer

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def main() -> int:
    loader = GTFSDataLoader(DATA_DIR)
    data = loader.load()
    graph = GTFSGraph(data)

    try:
        search_params = SearchInterface.parse_cli_input()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    search_route = GTFSSearchRoute(graph)
    visualizer = GTFSVisualizer(graph)

    started = perf_counter()

    try:
        result = search_route.search(search_params)
    except (ValueError, RuntimeError) as exc:
        print(f"Błąd wyszukiwania: {exc}", file=sys.stderr)
        return 1

    elapsed = perf_counter() - started

    SearchInterface.print_result(result, graph)
    visualizer.plot_result(result, output_html="found_route_map.html")

    print(f"Czas obliczeń: {elapsed:.6f} s", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
