#!/usr/bin/env sh
# step-gate launcher for Unix (linux/macOS) and Git Bash: auto-select bin/<platform>/step-gate
# Agent-facing commands are status/next/complete/help only. Any other command
# (reset/init/fail/...) is admin-only; the operator provisions access out-of-band.
SKILL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
START_DIR=$(pwd)
CMD="$1"
SUB="$2"
case "$CMD" in
  status|next|complete|--help|-h|help|"")
    ;;
  chain)
    # chain status is read-only; chain init/advance are admin-only.
    case "$SUB" in
      status) ;;
      *)
        if [ -z "$STEP_GATE_ADMIN_TOKEN" ]; then
          echo "[step-gate] command '$CMD $SUB' is admin-only; contact the operator (docs/ADMIN.md)" >&2
          exit 2
        fi
        ADMIN_ONLY=--admin-only
        ;;
    esac
    ;;
  *)
    if [ -z "$STEP_GATE_ADMIN_TOKEN" ]; then
      echo "[step-gate] command '$CMD' is admin-only; contact the operator (docs/ADMIN.md)" >&2
      exit 2
    fi
    ADMIN_ONLY=--admin-only
    ;;
esac
OS=$(uname -s)
ARCH=$(uname -m)
case "$OS" in
  Darwin) PLAT=macos ;;
  Linux) PLAT=linux ;;
  MINGW*|MSYS*|CYGWIN*) PLAT=windows ;;
  *) echo "[step-gate] unsupported OS: $OS" >&2; exit 1 ;;
esac
case "$ARCH" in
  x86_64|amd64) A=x64 ;;
  aarch64|arm64) A=arm64 ;;
  *) echo "[step-gate] unsupported arch: $ARCH" >&2; exit 1 ;;
esac
BIN="$SKILL_DIR/bin/$PLAT-$A/step-gate"
[ "$PLAT" = windows ] && BIN="$BIN.exe"
if [ ! -f "$BIN" ]; then
  echo "[step-gate] no binary for $PLAT-$A: $BIN (run build-cross.sh or install the platform package)" >&2
  exit 1
fi
cd "$SKILL_DIR" || exit 1
# Append --admin-only for admin commands (double layer with the whitelist above).
exec "$BIN" "$@" --workdir "$START_DIR" ${ADMIN_ONLY:-}
