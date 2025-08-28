"""
Package init for the local `src` package.

We perform a safe runtime check for the sqlite3 library version here. Chroma/Chromadb
requires sqlite3 >= 3.35.0, but the Python runtime's bundled `sqlite3` module may be
linked against an older SQLite version (for example when Python was built against an
older system lib). When that happens, try to replace the stdlib `sqlite3` module with
`pysqlite3.dbapi2` (provided by the `pysqlite3-binary` package) so the rest of the
application (and chromadb) sees a newer SQLite.

This is a low-risk, local workaround for development environments. A permanent fix
is to rebuild Python or use a Python build linked to a newer libsqlite3, or install
the package as an editable install in the virtualenv.
"""

from __future__ import annotations

import sys
import warnings


def _ensure_sqlite_min_version(min_version: tuple[int, int, int] = (3, 35, 0)) -> None:
	"""Ensure the `sqlite3` module exposes at least `min_version`.

	If the stdlib `sqlite3` is linked to an older SQLite, attempt to import
	`pysqlite3.dbapi2` and register it as the `sqlite3` module in sys.modules.
	"""
	try:
		import sqlite3 as _sqlite  # type: ignore

		try:
			parts = tuple(int(p) for p in _sqlite.sqlite_version.split("."))
		except Exception:
			parts = (0, 0, 0)

		if parts >= min_version:
			return

		# stdlib sqlite3 is too old; try to swap in pysqlite3
		try:
			from pysqlite3 import dbapi2 as _pysqlite_dbapi2  # type: ignore

			sys.modules["sqlite3"] = _pysqlite_dbapi2
			warnings.warn(
				"Replaced stdlib sqlite3 with pysqlite3.dbapi2 to satisfy chromadb's"
				" SQLite version requirement."
			)
		except Exception as exc:  # pragma: no cover - runtime environment dependent
			warnings.warn(
				"Your Python's sqlite3 is older than required by chromadb and pysqlite3"
				" is not available. Install `pysqlite3-binary` or use a Python build"
				" linked against SQLite >= 3.35.0. Error: %s" % (exc,)
			)
	except Exception:
		# If importing sqlite3 itself fails for some reason, don't crash at import time.
		# Chromadb will raise a clearer error later when it imports.
		return


# Run the check early so any subsequent imports (like chromadb) see the patched module.
_ensure_sqlite_min_version()
