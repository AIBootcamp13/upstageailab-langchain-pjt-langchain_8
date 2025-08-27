What I did (summary)

Set Poetry to create venvs in-project with poetry config virtualenvs.in-project true --local.
Removed the cached Poetry venv and recreated a project .venv using your Python.
Verified .venv exists and Poetry recognizes it as Activated.
Files/paths affected

New directory created: .venv at the project root (.venv)
# should show the project .venv path
poetry env info -p

# shows that .venv is in the project and activated by Poetry
poetry env list --full-path

# confirm VIRTUAL_ENV when you source it
source .venv/bin/activate
echo "$VIRTUAL_ENV"
which python
python -c 'import sys; print(sys.executable, sys.prefix)'


----
wb2x@instance-15724:...b-langchain-pjt-langchain_8 (feature/memory*+)
$ poetry run python - <<'PY'
> import importlib, traceback
> try:
>     importlib.import_module('src.agent')
>     print('import success')
> except Exception as e:
>     print('error during import:', e)
>     traceback.print_exc()
> PY
/home/wb2x/workspace/upstageailab-langchain-pjt-langchain_8/src/__init__.py:49: UserWarning: Your Python's sqlite3 is older than required by chromadb and pysqlite3 is not available. Install `pysqlite3-binary` or use a Python build linked against SQLite >= 3.35.0. Error: No module named 'pysqlite3'
  warnings.warn(
import success

Option A — Local install only (no repo edits, simplest)

Install the package into your current Poetry environment (or any venv) so Streamlit/Chromadb work locally. Nothing changes in the repo or lockfile.
# Install into the current Poetry venv (recommended for current setup)
poetry run pip install "pysqlite3-binary>=0.5.4,<0.6.0"

# Verify
poetry run python -c "import pysqlite3, sqlite3; print('ok', sqlite3.sqlite_version)"