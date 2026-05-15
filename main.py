"""CLI entry point for the energy grid simulator."""

from __future__ import annotations

import argparse
import sys

from energy_grid.output import print_schedule
from energy_grid.parser import load_input
from energy_grid.scheduler import build_schedule


def main() -> int:
    """Run the application."""
    parser = argparse.ArgumentParser(description="Simulate an energy grid schedule.")
    parser.add_argument("input_path", help="Path to the input JSON file")
    args = parser.parse_args()

    try:
        consumers, generators = load_input(args.input_path)
        schedule = build_schedule(consumers, generators)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print_schedule(schedule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
