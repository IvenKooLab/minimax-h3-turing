#!/usr/bin/env bash
# Launch ComfyUI headless for MiniMax H3 with memory-safe flags.
# VRAM reserve + headroom => keep the shared desktop GPU from TDR (black screen).
# --disable-pinned-memory => kills the read_file_slice failure path that OOM'd.
#
# Usage: edit COMFY_DIR / PY to your install, then run.

COMFY_DIR="${COMFY_DIR:-/path/to/ComfyUI}"
PY="${PY:-/path/to/python}"

cd "$COMFY_DIR" || exit 1
exec "$PY" main.py \
  --listen 127.0.0.1 --port 8188 \
  --reserve-vram 2.5 --vram-headroom 0.5 \
  --disable-pinned-memory \
  > h3_server.log 2>&1
