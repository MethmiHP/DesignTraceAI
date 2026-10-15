import pytest

from shared.utils import output_store


def pytest_configure(config):
    # The router constructs its service while test modules are imported.
    # Set the default before collection, rather than in a fixture (too late).
    # LLM tests explicitly pass enable_llm=True with a stub provider.
    environment = pytest.MonkeyPatch()
    environment.setenv("API_COMPONENT_ENABLE_LLM", "false")
    config.add_cleanup(environment.undo)


@pytest.fixture(autouse=True)
def isolated_outputs(tmp_path, monkeypatch):
    """Keep test runs from accumulating in the user's process outputs."""
    output_dir = tmp_path / "outputs"
    monkeypatch.setattr(output_store, "DEFAULT_OUTPUT_DIR", output_dir)
    return output_dir
