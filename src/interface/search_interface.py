from __future__ import annotations

import argparse
import sys
from datetime import datetime

from ..graph.graph import GTFSGraph
from ..routing.types import (
    PathResult,
    PointToPointAlgorithm,
    SearchCriterion,
    SearchMode,
    SearchParameters,
    TourOptimizationStrategy,
    TourResult,
)


class SearchInterface:
    @staticmethod
    def print_available_options() -> None:
        print("\n=== DOSTĘPNE OPCJE I ALGORYTMY WYSZUKIWANIA ===")

        print("\n--- Algorytmy A -> B ---")
        for alg in PointToPointAlgorithm:
            print(f"  • {alg.value:<18} - {alg.description}")

        print("\n--- Strategie optymalizacji A -> L -> A ---")
        for strat in TourOptimizationStrategy:
            print(f"  • {strat.value:<18} - {strat.description}")

        print("\n--- Kryteria optymalizacji ---")
        for crit in SearchCriterion:
            print(f"  • {crit.value:<18} - {crit.description}")
        print()

    @staticmethod
    def create_cli_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="main.py",
            description="Wyszukiwanie najszybszej lub najdogodniejszej trasy GTFS.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Przykłady użycia:
  1. Tryb A -> B (AStar / Dijkstra):
     python main.py ab 1413001 1413002 t "2026-10-24 08:00:00" --variant astar

  2. Tryb A -> L -> A (Optymalizacja trasy):
     python main.py cycle 1413001 "1413002;1413003" p "2026-10-24 08:00:00" --variant basic --iterations 100

  3. Interaktywny (bez argumentów):
     python main.py
            """,
        )

        subparsers = parser.add_subparsers(
            dest="command",
            help="Wybierz tryb wyszukiwania",
            metavar="{ab, cycle}",
        )

        parser_ab = subparsers.add_parser(
            "ab",
            help="Szukanie trasy z punktu A do punktu B (AStar / Dijkstra)",
        )
        parser_ab.add_argument("start", help="ID przystanku początkowego A")
        parser_ab.add_argument("target", help="ID przystanku końcowego B")
        parser_ab.add_argument(
            "criterion",
            choices=[c.value for c in SearchCriterion],
            help="Kryterium: t = czas, p = liczba przesiadek",
        )
        parser_ab.add_argument(
            "start_time",
            help="Czas rozpoczęcia podróży (YYYY-MM-DD HH:MM:SS)",
        )
        parser_ab.add_argument(
            "--variant",
            choices=[a.value for a in PointToPointAlgorithm],
            default=PointToPointAlgorithm.DIJKSTRA.value,
            help="Algorytm wyszukiwania (domyślnie: dijkstra)",
        )
        parser_ab.add_argument(
            "--max-waiting",
            type=int,
            default=3600,
            help="Maksymalny czas oczekiwania na przesiadkę w sekundach (domyślnie: 3600)",
        )

        parser_cycle = subparsers.add_parser(
            "cycle",
            help="Szukanie trasy typu komiwojażer A -> L -> A",
        )
        parser_cycle.add_argument("start", help="ID przystanku początkowego A")
        parser_cycle.add_argument(
            "target",
            help="Lista przystanków L rozdzielona średnikami (np. '1413001;1413002')",
        )
        parser_cycle.add_argument(
            "criterion",
            choices=[c.value for c in SearchCriterion],
            help="Kryterium: t = czas, p = liczba przesiadek",
        )
        parser_cycle.add_argument(
            "start_time",
            help="Czas rozpoczęcia podróży (YYYY-MM-DD HH:MM:SS)",
        )
        parser_cycle.add_argument(
            "--variant",
            choices=[s.value for s in TourOptimizationStrategy],
            default=TourOptimizationStrategy.BASIC.value,
            help="Strategia optymalizacji (domyślnie: basic)",
        )
        parser_cycle.add_argument(
            "--iterations",
            type=int,
            default=80,
            help="Liczba iteracji (domyślnie: 80)",
        )
        parser_cycle.add_argument(
            "--max-waiting",
            type=int,
            default=3600,
            help="Maksymalny czas oczekiwania na przesiadkę w sekundach (domyślnie: 3600)",
        )

        return parser

    @staticmethod
    def _prompt_interactive() -> SearchParameters:
        SearchInterface.print_available_options()
        print("=== Tryb interaktywny wyszukiwania trasy ===")
        mode_choice = input("Wybierz tryb [1 = A->B, 2 = A->L->A] (domyślnie 1): ").strip()
        mode = "cycle" if mode_choice == "2" else "ab"

        start = input("ID przystanku początkowego A: ").strip()
        if not start:
            raise ValueError("Przystanek początkowy nie może być pusty.")

        if mode == "ab":
            target = input("ID przystanku końcowego B: ").strip()
            default_variant = PointToPointAlgorithm.DIJKSTRA.value
            variant_prompt = f"Wariant {[a.value for a in PointToPointAlgorithm]} (domyślnie {default_variant}): "
        else:
            target = input("Lista przystanków L (rozdzielona średnikami ';'): ").strip()
            default_variant = TourOptimizationStrategy.BASIC.value
            variant_prompt = f"Strategia optymalizacji {[s.value for s in TourOptimizationStrategy]} (domyślnie {default_variant}): "

        criterion = input("Kryterium [t = czas, p = przesiadki] (domyślnie t): ").strip() or "t"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_time = input(f"Czas startu (YYYY-MM-DD HH:MM:SS) [domyślnie {now_str}]: ").strip() or now_str

        variant = input(variant_prompt).strip() or default_variant

        iterations = 80
        if mode == "cycle":
            iters_raw = input("Liczba iteracji [domyślnie 80]: ").strip()
            iterations = int(iters_raw) if iters_raw else 80

        return SearchInterface.parse_input_values(
            start_stop_id=start,
            target=target,
            criterion=criterion,
            start_time=start_time,
            mode=mode,
            variant=variant,
            iterations=iterations,
            max_waiting=3600,
        )

    @staticmethod
    def parse_input_values(
        start_stop_id: str,
        target: str,
        criterion: str,
        start_time: str,
        mode: str = "auto",
        variant: str = "basic",
        iterations: int = 80,
        max_waiting: int = 3600,
    ) -> SearchParameters:
        if criterion not in {c.value for c in SearchCriterion}:
            raise ValueError("Nieznane kryterium. Użyj 't' albo 'p'.")

        if mode not in {"auto", "ab", "cycle"}:
            raise ValueError("Nieznany tryb. Użyj: auto, ab lub cycle.")

        normalized_start = str(start_stop_id).strip()
        normalized_target = str(target).strip()
        if not normalized_start:
            raise ValueError("Przystanek początkowy A nie może być pusty.")
        if not normalized_target:
            raise ValueError("Drugi argument (B albo lista L) nie może być pusty.")

        inferred_mode = mode
        if inferred_mode == "auto":
            inferred_mode = "cycle" if ";" in normalized_target else "ab"

        parsed_mode = SearchMode(inferred_mode)
        parsed_criterion = SearchCriterion(criterion)

        if parsed_mode == SearchMode.AB:
            end_stop_id = normalized_target
            visit_stops: list[str] = []
            try:
                point_algo = PointToPointAlgorithm(variant.strip().lower())
            except ValueError:
                point_algo = PointToPointAlgorithm.DIJKSTRA
            tour_strat = None
        else:
            end_stop_id = None
            visit_stops = [x.strip() for x in normalized_target.split(";") if x.strip()]
            if not visit_stops:
                raise ValueError("Lista przystanków L nie może być pusta.")
            try:
                tour_strat = TourOptimizationStrategy(variant.strip().lower())
            except ValueError as exc:
                raise ValueError(
                    "Nieznana strategia optymalizacji. Użyj: "
                    f"{[s.value for s in TourOptimizationStrategy]}"
                ) from exc
            point_algo = None

        try:
            departure_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError("Niepoprawny format daty. Użyj: YYYY-MM-DD HH:MM:SS") from exc

        return SearchParameters(
            mode=parsed_mode,
            start_stop_id=normalized_start,
            end_stop_id=end_stop_id,
            visit_stops=visit_stops,
            criterion=parsed_criterion,
            departure_datetime=departure_datetime,
            point_algorithm=point_algo,
            tour_strategy=tour_strat,
            iterations=iterations,
            max_waiting=max_waiting,
        )

    @classmethod
    def parse_cli_input(cls, argv: list[str] | None = None) -> SearchParameters:
        args_list = argv if argv is not None else sys.argv[1:]

        if not args_list:
            return cls._prompt_interactive()

        parser = cls.create_cli_parser()
        args = parser.parse_args(args_list)

        command = getattr(args, "command", None) or "auto"
        iterations = getattr(args, "iterations", 80)

        return cls.parse_input_values(
            start_stop_id=args.start,
            target=args.target,
            criterion=args.criterion,
            start_time=args.start_time,
            mode=command,
            variant=args.variant,
            iterations=iterations,
            max_waiting=args.max_waiting,
        )

    @staticmethod
    def print_result(result: PathResult | TourResult, graph: GTFSGraph | None = None) -> None:
        if isinstance(result, TourResult):
            print(f"\nOPTYMALNY OBIEG: {' -> '.join(result.order)}")
            print(
                f"Całkowity czas: {result.total_time // 60} min "
                f"({result.total_time // 3600} h {(result.total_time % 3600) // 60} min) | "
                f"Całkowite przesiadki: {result.total_transfers} | "
                f"Wartość zoptymalizowana: {result.minimized_value}"
            )
            print("=" * 160)
            for leg_num, leg in enumerate(result.legs, 1):
                print(f"\nNOGA {leg_num}: {leg.start_stop_id} -> {leg.end_stop_id}")
                SearchInterface.print_result(leg, graph)
        else:
            if not result.path_edges:
                print("Brak trasy do wyswietlenia (lista odcinkow jest pusta).")
                return

            print(f"\nTRASA ZNALEZIONA: {result.start_stop_id} -> {result.end_stop_id}")
            print(
                f"Czas: {result.total_time // 60} min "
                f"({result.total_time // 3600} h {(result.total_time % 3600) // 60} min) | "
                f"Dystans: {result.total_distance / 1000:.2f} km | "
                f"Przesiadki: {result.transfers}"
            )
            print("=" * 155)

            start_node = graph.nodes.get(result.start_stop_id) if graph else None

            print(
                f"{'Lp':<4} {'Linia':<12} {'Od':<30} {'Do':<30} "
                f"{'Odjazd':<8} {'Przyjazd':<8} {'Czas':<8} {'Uwagi':<45}"
            )
            print("-" * 155)

            for i, edge in enumerate(result.path_edges):
                has_transfer = (
                    i < len(result.path_edges) - 1
                    and edge.route_name != result.path_edges[i + 1].route_name
                )

                # Определяем название станции отправления:
                # - Для первого ребра берём имя из start_node (если есть) или его ID
                # - Для последующих рёбер берём имя target из предыдущего ребра
                if i == 0:
                    from_name = start_node.name[:28] if start_node else result.start_stop_id
                else:
                    prev_edge = result.path_edges[i - 1]
                    from_name = prev_edge.target.name[:28]

                to_name = edge.target.name[:28]

                dep_h, dep_m = edge.departure_time // 3600, (edge.departure_time % 3600) // 60
                arr_h, arr_m = edge.arrival_time // 3600, (edge.arrival_time % 3600) // 60
                dep_time = f"{dep_h:02d}:{dep_m:02d}"
                arr_time = f"{arr_h:02d}:{arr_m:02d}"
                travel_str = f"{edge.travel_time // 60} min"

                print(
                    f"{i+1:<4} {edge.route_name:<12} {from_name:<30} {to_name:<30} "
                    f"{dep_time:<8} {arr_time:<8} {travel_str:<8} {'-':<45}"
                )

                if has_transfer:
                    next_edge = result.path_edges[i + 1]
                    next_dep_h, next_dep_m = (
                        next_edge.departure_time // 3600,
                        (next_edge.departure_time % 3600) // 60,
                    )
                    next_dep_time = f"{next_dep_h:02d}:{next_dep_m:02d}"
                    transfer_wait = next_edge.departure_time - edge.arrival_time
                    wait_minutes = transfer_wait // 60
                    wait_seconds = transfer_wait % 60
                    wait_str = (
                        f"{wait_minutes} min {wait_seconds} s"
                        if wait_seconds > 0
                        else f"{wait_minutes} min"
                    )
                    print(
                        f"{'':<4} {'':<12} {to_name:<30} {to_name:<30} "
                        f"{arr_time:<8} {next_dep_time:<8} {wait_str:<8} "
                        f"Przesiadka: {edge.route_name} -> {next_edge.route_name:<22}"
                    )

            print("=" * 155)