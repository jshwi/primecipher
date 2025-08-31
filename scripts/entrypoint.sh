#!/bin/bash -x
set -Eeuo pipefail

# hand over control
exec "$@"
