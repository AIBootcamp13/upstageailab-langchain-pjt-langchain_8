#!/usr/bin/env python3
"""
A small TUI to inspect processes and memory using textual/rich.
Install: pip install rich textual psutil
Run: python tools/mem_tui.py

Features:
- Lists top processes by RSS
- Press Enter to show detailed info for a selected PID
- Refresh with 'r'

This is intentionally minimal to avoid heavy deps. If you want a full-screen fuzzy finder, we can extend it.
"""
import sys
from typing import List

try:
    from rich.table import Table
    from rich.console import Console
    from rich.live import Live
    import psutil
except Exception as e:
    print("Missing dependencies. Install with: pip install rich psutil")
    raise

console = Console()


def get_top(n=30):
    procs = []
    for p in psutil.process_iter(["pid", "ppid", "name", "username", "memory_info", "cpu_percent", "cmdline"]):
        try:
            info = p.info
n            rss = info.get("memory_info").rss // 1024
        except Exception:
            continue
        procs.append((rss, info))
    procs.sort(reverse=True, key=lambda x: x[0])
    return procs[:n]


def make_table(procs: List, n=30):
    table = Table(title=f"Top {n} processes by RSS (KB)")
    table.add_column("PID", justify="right")
    table.add_column("USER")
    table.add_column("RSS (KB)", justify="right")
    table.add_column("%CPU", justify="right")
    table.add_column("CMD")
    for rss, info in procs:
        pid = info.get("pid")
        cpu = info.get("cpu_percent") or 0
        user = info.get("username") or ""
        cmd = " ".join(info.get("cmdline") or [info.get("name") or ""])[:120]
        table.add_row(str(pid), user, str(rss), f"{cpu:.1f}", cmd)
    return table


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            procs = get_top(n)
            live.update(make_table(procs, n))
            try:
                # simple refresh loop
                import time
                time.sleep(2)
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    main()
