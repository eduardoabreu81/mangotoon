#!/bin/sh
set -e

python scripts/init_data.py --data-dir "${APP_DATA_DIR:-data}"

exec "$@"
