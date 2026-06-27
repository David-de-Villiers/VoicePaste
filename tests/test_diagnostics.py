from voicepaste.diagnostics import _active_conda_warning, _ld_library_path_warning


def test_diagnostics_warns_for_conda_base():
    check = _active_conda_warning({"CONDA_DEFAULT_ENV": "base", "CONDA_PREFIX": "/home/me/miniconda3"})
    assert check.ok is False
    assert "base active" in check.value


def test_diagnostics_warns_for_miniconda_ld_library_path():
    check = _ld_library_path_warning({"LD_LIBRARY_PATH": "/home/me/miniconda3/lib:/usr/lib"})
    assert check.ok is False
    assert "Conda path" in check.value


def test_diagnostics_accepts_clean_conda_environment():
    assert _active_conda_warning({}).ok is True
    assert _ld_library_path_warning({}).ok is True
