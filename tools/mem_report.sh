#!/usr/bin/env bash
set -euo pipefail

# Simple memory investigation helper
# Usage:
#   ./mem_report.sh [TOP_N]
# Examples:
#   ./mem_report.sh         # show top 30 by RSS and aggregated suspects
#   ./mem_report.sh 50      # top 50

N=${1:-30}

printf "\n== Top %s processes by RSS (KB) ==\n\n" "$N"
# Print header then top N
ps -eo pid,ppid,user,%mem,%cpu,rss,vsz,cmd --sort=-rss | awk 'NR==1{printf "%5s %5s %8s %5s %5s %10s %10s %s\n", "PID","PPID","USER","%MEM","%CPU","RSS","VSZ","CMD"; next} {printf "%5s %5s %8s %5s %5s %10s %10s %s\n", $1,$2,$3,$4,$5,$6,$7,$8}' | head -n $((N+1))

printf "\n== Aggregated by command (top 20) ==\n\n"
# Aggregate rss by command (first 120 chars) and show counts
ps -eo rss,cmd --no-headers | awk '{rss=$1; $1=""; cmd=substr($0,2); key=substr(cmd,1,120); agg[key]+=rss; cnt[key]++} END{for(k in agg) printf "%10d %5d %s\n", agg[k], cnt[k], k}' | sort -rn | head -n 20

printf "\n== Quick checks ==\n\n"
# Show memory usage summary
awk '/MemTotal/ {mt=$2} /MemAvailable/ {ma=$2} END{printf "MemTotal: %d KB\nMemAvailable: %d KB\n", mt, ma}' /proc/meminfo || true

# Show top per-user memory consumption
printf "\nTop users by RSS (sum of RSS KB):\n"
ps -eo user,rss --no-headers | awk '{u=$1; r=$2; usr[u]+=r} END{for(u in usr) printf "%10d %s\n", usr[u], u}' | sort -rn

cat <<'EOF'

Notes:
- RSS values are in KB.
- Aggregated view groups by the first ~120 chars of the command line; it helps spot many-worker processes (e.g., multiple node instances, python workers, containers with same cmd).
- No sudo needed.

Suggested next steps:
- Run `./tools/mem_report.sh 50` to get a broader view.
- Use `ps aux | grep <pid>` and `pmap -x <pid>` for deeper inspection (pmap may exist in your environment).
EOF
