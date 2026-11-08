import pytest
from pydantic import ValidationError

from ingest.discovery.registry import load_company_registry


def test_loads_default_company_registry():
    boards = load_company_registry()

    assert {(board.provider, board.board_id) for board in boards} == {
        ("greenhouse", "stripe"),
        ("lever", "spotify"),
        ("ashby", "linear"),
    }


def test_disabled_companies_are_not_loaded(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
companies:
  - company_name: Disabled Co
    provider: greenhouse
    board_id: disabled
    enabled: false
  - company_name: Enabled Co
    provider: ashby
    board_id: enabled
""",
        encoding="utf-8",
    )

    boards = load_company_registry(registry_path)

    assert [(board.company_name, board.board_id) for board in boards] == [
        ("Enabled Co", "enabled")
    ]


def test_duplicate_boards_are_rejected(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
companies:
  - company_name: First Name
    provider: greenhouse
    board_id: shared
  - company_name: Another Name
    provider: greenhouse
    board_id: shared
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate ATS board"):
        load_company_registry(registry_path)


def test_invalid_provider_is_rejected(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
companies:
  - company_name: Unsupported Co
    provider: workday
    board_id: unsupported
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_company_registry(registry_path)


def test_missing_board_id_is_rejected(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
companies:
  - company_name: Missing Board
    provider: greenhouse
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_company_registry(registry_path)


def test_invalid_yaml_is_reported(tmp_path):
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("companies: [", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid company registry YAML"):
        load_company_registry(registry_path)