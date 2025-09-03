Memory triage tools

1) mem_report.sh
- A zero-dependency shell script that summarizes top processes by RSS and aggregates by command.
- Usage: ./mem_report.sh [TOP_N]

2) mem_tui.py
- Minimal TUI using `rich` and `psutil` to refresh a table of top processes.
- Install dependencies as a normal user: pip install --user rich psutil
- Run: python tools/mem_tui.py

Notes and next steps
- Both tools are deliberately small and user-run (no sudo).
- For longer-term: consider packaging `mem_tui.py` with proper CLI args, filters, and a pager or fuzzy selector.
- If you want a more advanced TUI (interactive selection, killing PIDs, viewing pmap), I can build a textual-based app using `textual` or `urwid` but it will add extra deps.
