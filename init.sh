#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="${PROJECT_ROOT}/env"

# Keep conda from hijacking this shell session if available.
if command -v conda >/dev/null 2>&1; then
  conda deactivate >/dev/null 2>&1 || true
fi

# Create env if missing.
if [ ! -d "${ENV_DIR}" ]; then
  echo "Creating virtualenv at ${ENV_DIR}"
  python3 -m venv "${ENV_DIR}"
fi

# Activate env.
# shellcheck disable=SC1091
source "${ENV_DIR}/bin/activate"

# Make sure we use this env's python/pip.
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1

# Install deps if needed.
if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
  python -m pip install --upgrade pip
  python -m pip install -r "${PROJECT_ROOT}/requirements.txt"
fi

# Create .env from template if missing.
if [ ! -f "${PROJECT_ROOT}/.env" ] && [ -f "${PROJECT_ROOT}/.env.example" ]; then
  cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
  echo "Created .env from .env.example"
fi

# Handy helper aliases for this shell only.
alias lorewell-run='python -m uvicorn app.main:app --reload'
alias lorewell-pip='python -m pip'
alias lorewell-python='python'

echo
echo "Lorewell ready."
echo "Project: ${PROJECT_ROOT}"
echo "Python:  $(which python)"
echo "Pip:     $(python -m pip --version)"
echo
echo "Next:"
echo "  source ./init.sh"
echo "  lorewell-run"
