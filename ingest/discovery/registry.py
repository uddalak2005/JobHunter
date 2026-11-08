from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ingest.schemas import ATSBoard

DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "company_registry.yaml"
)


class RegistryEntry(ATSBoard):
    enabled: bool = True

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegistryDocument(BaseModel):
    companies: list[RegistryEntry] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


def load_company_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> list[ATSBoard]:
    registry_path = Path(path)

    try:
        raw_data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid company registry YAML at {registry_path}") from exc

    document = RegistryDocument.model_validate(raw_data)
    seen_boards: set[tuple[str, str]] = set()
    boards: list[ATSBoard] = []

    for entry in document.companies:
        board_key = (entry.provider, entry.board_id)
        if board_key in seen_boards:
            raise ValueError(
                f"Duplicate ATS board in {registry_path}: "
                f"{entry.provider}/{entry.board_id}"
            )
        seen_boards.add(board_key)

        if entry.enabled:
            boards.append(ATSBoard.model_validate(entry.model_dump(exclude={"enabled"})))

    return boards