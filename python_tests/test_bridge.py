from __future__ import annotations

from pathlib import Path

import pytest
from tca_sil.bridge import locate_sil_library


def test_explicit_missing_library_reports_checked_path(tmp_path: Path) -> None:
    missing = tmp_path / "tca_sil.dll"
    with pytest.raises(FileNotFoundError, match="Compiled SIL library") as error:
        locate_sil_library(missing)
    assert str(missing) in str(error.value)


def test_explicit_existing_library_is_resolved(tmp_path: Path) -> None:
    library = tmp_path / "placeholder.dll"
    library.write_bytes(b"not loaded by this resolution test")
    assert locate_sil_library(library) == library.resolve()
