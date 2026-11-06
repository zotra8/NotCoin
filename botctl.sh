#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")"
pidfile=.bot.pid

running() {
  [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null
}

case "${1:-status}" in
  start)
    if running; then
      echo "Bot already running (PID $(cat "$pidfile"))"
      exit 0
    fi
    setsid python3 -u main.py >> bot.log 2>&1 < /dev/null &
    echo "$!" > "$pidfile"
    sleep 2
    if running; then
      echo "Bot started (PID $(cat "$pidfile"))"
    else
      echo "Bot failed to start; inspect bot.log" >&2
      exit 1
    fi
    ;;
  stop)
    if running; then
      kill -TERM "$(cat "$pidfile")"
      echo "Bot stopped"
    else
      echo "Bot is not running"
    fi
    rm -f "$pidfile"
    ;;
  restart)
    bash ./botctl.sh stop
    bash ./botctl.sh start
    ;;
  status)
    if running; then
      echo "Bot running (PID $(cat "$pidfile"))"
    else
      echo "Bot is not running"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}" >&2
    exit 2
    ;;
esac
