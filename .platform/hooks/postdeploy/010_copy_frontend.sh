#!/bin/bash
set -euo pipefail

# Kør på EC2 efter EB har lagt din kode i /var/app/current
SRC="/var/app/current/frontend/dist"
DST="/var/app/current/frontend"

if [ -d "$SRC" ]; then
  rm -rf "$DST"
  mkdir -p "$DST"
  cp -rp "$SRC/"* "$DST/"
  echo "[postdeploy] Copied frontend dist to $DST"
else
  echo "[postdeploy] WARNING: $SRC not found. Did you build and commit frontend/dist?"
fi
