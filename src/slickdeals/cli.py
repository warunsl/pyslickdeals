"""Command-line interface: `slickdeals`."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from urllib.error import URLError

from . import __version__
from .feed import Deal, fetch_deals


def _color() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _style(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _color() else text


def _ago(dt: datetime | None) -> str:
    if not dt:
        return ""
    secs = (datetime.now(timezone.utc) - dt).total_seconds()
    if secs < 3600:
        return f"{max(int(secs // 60), 0)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


def print_deals(deals: list[Deal], verbose: bool = False, hot: bool = False) -> None:
    width = min(shutil.get_terminal_size().columns, 100)
    prefix = "🔥 " if hot else ""
    for d in deals:
        title = _style(d.title, "1;31" if hot else "1")
        print(f"{prefix}{title}  {_style(_ago(d.published), '2')}")
        if verbose and d.description:
            print(textwrap.indent(textwrap.fill(d.description, width - 4), "    "))
        print(_style(f"    {d.link}", "36"))
        print()


def _matches(deal: Deal, keywords: list[str]) -> bool:
    text = f"{deal.title} {deal.description}".lower()
    return any(k.lower() in text for k in keywords)


def _notify(deal: Deal) -> None:
    if sys.platform != "darwin" or not shutil.which("osascript"):
        return
    title = deal.title.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(
        ["osascript", "-e", f'display notification "{title}" with title "Slickdeals"'],
        check=False,
        capture_output=True,
    )


def _load(args) -> list[Deal]:
    deals = fetch_deals(args.search, args.popular)
    if args.match:
        deals = [d for d in deals if _matches(d, args.match)]
    return deals


def watch(args) -> int:
    seen: set[str] = set()
    first = True
    print(
        _style(f"Watching every {args.interval}m. Ctrl-C to stop.", "2"),
        file=sys.stderr,
    )
    while True:
        try:
            deals = _load(args)
        except (URLError, OSError) as e:
            print(_style(f"fetch failed: {e}", "33"), file=sys.stderr)
            deals = []
        new = [d for d in deals if d.id not in seen]
        seen.update(d.id for d in deals)
        if new:
            # Show what's there on the first poll, but only notify for later arrivals.
            print_deals(new, args.verbose, args.popular)
            if not first and args.notify:
                for d in new:
                    _notify(d)
        first = False
        time.sleep(args.interval * 60)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="slickdeals",
        description="Browse Slickdeals from the command line. "
        "Shows frontpage deals by default.",
    )
    source = p.add_mutually_exclusive_group()
    source.add_argument("-s", "--search", metavar="QUERY", help="search all deals")
    source.add_argument(
        "-p", "--popular", action="store_true", help="show popular deals 🔥"
    )
    p.add_argument(
        "-m",
        "--match",
        metavar="WORD",
        action="append",
        help="only show deals whose title/description contains WORD "
        "(repeatable; any match counts)",
    )
    p.add_argument("-n", "--limit", type=int, default=None, help="max deals to show")
    p.add_argument("-v", "--verbose", action="store_true", help="show descriptions")
    p.add_argument("--json", action="store_true", help="output JSON")
    p.add_argument(
        "-w", "--watch", action="store_true", help="poll for new deals until stopped"
    )
    p.add_argument(
        "-i", "--interval", type=int, default=10, help="watch interval in minutes"
    )
    p.add_argument(
        "--notify",
        action="store_true",
        help="with --watch, send a macOS notification for each new deal",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.interval < 1:
        print("--interval must be at least 1 minute", file=sys.stderr)
        return 2
    try:
        if args.watch:
            return watch(args)
        deals = _load(args)
    except KeyboardInterrupt:
        return 130
    except (URLError, OSError) as e:
        print(f"Can't reach slickdeals: {e}", file=sys.stderr)
        return 1

    if args.limit is not None:
        deals = deals[: args.limit]
    if args.json:
        json.dump([d.to_dict() for d in deals], sys.stdout, indent=2)
        print()
    elif not deals:
        print("No deals found.", file=sys.stderr)
    else:
        print_deals(deals, args.verbose, args.popular)
    return 0


if __name__ == "__main__":
    sys.exit(main())
