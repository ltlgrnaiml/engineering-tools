"""Workflow Service - artifact discovery for DevTools Workflow Manager."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from shared.contracts.core.path_safety import PathValidationError, RelativePath, make_relative
from shared.contracts.devtools.workflow import (
    ArtifactGraphResponse,
    ArtifactDeleteRequest,
    ArtifactDeleteResponse,
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    ArtifactWriteRequest,
    ArtifactWriteResponse,
    GraphEdge,
    GraphNode,
    GraphRelationship,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent


def scan_artifacts(
    artifact_type: ArtifactType | None = None,
    search: str | None = None,
) -> list[ArtifactSummary]:
    """Scan workflow artifacts in the repository.

    Args:
        artifact_type: Optional artifact type filter.
        search: Optional case-insensitive substring filter applied to `id`, `title`,
            and `file_path`.

    Returns:
        List of discovered artifacts.
    """

    artifacts: list[ArtifactSummary] = []

    for candidate in _iter_artifact_files(artifact_type=artifact_type):
        summary = _read_artifact_summary(candidate)
        if summary is None:
            continue
        if not _matches_search(summary, search=search):
            continue
        artifacts.append(summary)

    artifacts.sort(key=lambda a: (a.type.value, a.id))
    return artifacts


def build_artifact_graph(
    artifact_type: ArtifactType | None = None,
    search: str | None = None,
) -> ArtifactGraphResponse:
    """Build the artifact relationship graph.

    Args:
        artifact_type: Optional artifact type filter.
        search: Optional search filter applied to artifact scanning.

    Returns:
        Graph response containing nodes and edges.
    """

    summaries = scan_artifacts(artifact_type=artifact_type, search=search)

    nodes_by_id: dict[str, GraphNode] = {
        s.id: GraphNode(
            id=s.id,
            type=s.type,
            label=s.title,
            status=s.status,
            file_path=s.file_path,
        )
        for s in summaries
    }

    edges: list[GraphEdge] = []
    seen_edges: set[tuple[str, str, GraphRelationship]] = set()

    for summary in summaries:
        abs_path = PROJECT_ROOT / Path(summary.file_path)
        for relationship, target_id in _extract_artifact_references(
            artifact_type=summary.type,
            path=abs_path,
        ):
            if target_id == summary.id:
                continue

            if target_id not in nodes_by_id:
                guessed_type = _infer_type_from_id(target_id)
                if guessed_type is None:
                    continue
                nodes_by_id[target_id] = GraphNode(
                    id=target_id,
                    type=guessed_type,
                    label=target_id,
                    status=ArtifactStatus.UNKNOWN,
                    file_path="",
                )

            key = (summary.id, target_id, relationship)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            edges.append(
                GraphEdge(
                    source=summary.id,
                    target=target_id,
                    relationship=relationship,
                )
            )

    nodes = list(nodes_by_id.values())
    nodes.sort(key=lambda n: (n.type.value, n.id))
    edges.sort(key=lambda e: (e.relationship.value, e.source, e.target))
    return ArtifactGraphResponse(nodes=nodes, edges=edges)


def create_artifact(request: ArtifactWriteRequest) -> ArtifactWriteResponse:
    """Create a new artifact.

    Args:
        request: Write request.

    Returns:
        Write response.
    """

    return _write_artifact(request=request, must_exist=False)


def update_artifact(request: ArtifactWriteRequest) -> ArtifactWriteResponse:
    """Update an existing artifact.

    Args:
        request: Write request.

    Returns:
        Write response.
    """

    return _write_artifact(request=request, must_exist=True)


def delete_artifact(request: ArtifactDeleteRequest) -> ArtifactDeleteResponse:
    """Delete an artifact by moving it to a backup location.

    Args:
        request: Delete request.

    Returns:
        Delete response.
    """

    try:
        rel = RelativePath(path=request.file_path)
    except (PathValidationError, ValueError) as e:
        return ArtifactDeleteResponse(
            success=False,
            file_path=request.file_path,
            backup_path=None,
            message=f"Path unsafe: {e}",
        )

    abs_path = (PROJECT_ROOT / rel.to_native()).resolve()
    allowed_root = _artifact_root_for_relpath(rel.path)
    if allowed_root is None:
        return ArtifactDeleteResponse(
            success=False,
            file_path=rel.path,
            backup_path=None,
            message="Path not within allowed artifact roots",
        )

    try:
        abs_path.relative_to(allowed_root.resolve())
    except ValueError:
        return ArtifactDeleteResponse(
            success=False,
            file_path=rel.path,
            backup_path=None,
            message="Path not within allowed artifact roots",
        )

    if not abs_path.exists():
        return ArtifactDeleteResponse(
            success=False,
            file_path=rel.path,
            backup_path=None,
            message="Artifact not found",
        )

    if request.permanent:
        abs_path.unlink(missing_ok=True)
        return ArtifactDeleteResponse(
            success=True,
            file_path=rel.path,
            backup_path=None,
            message="Artifact permanently deleted",
        )

    backup_path = _backup_file(abs_path)
    return ArtifactDeleteResponse(
        success=True,
        file_path=rel.path,
        backup_path=backup_path,
        message="Artifact moved to backup",
    )


def _matches_search(summary: ArtifactSummary, search: str | None) -> bool:
    if not search:
        return True

    term = search.casefold()
    return (
        term in summary.id.casefold()
        or term in summary.title.casefold()
        or term in summary.file_path.casefold()
    )


def _iter_artifact_files(artifact_type: ArtifactType | None) -> list[tuple[ArtifactType, Path]]:
    specs = {
        ArtifactType.DISCUSSION: (PROJECT_ROOT / ".discussions", ["*.md"]),
        ArtifactType.ADR: (PROJECT_ROOT / ".adrs", ["**/*.json"]),
        ArtifactType.SPEC: (PROJECT_ROOT / "docs" / "specs", ["**/*.json"]),
        ArtifactType.PLAN: (PROJECT_ROOT / ".plans", ["*.json", "*.md"]),
        ArtifactType.CONTRACT: (PROJECT_ROOT / "shared" / "contracts", ["**/*.py"]),
    }

    pairs: list[tuple[ArtifactType, Path]] = []

    types_to_scan = [artifact_type] if artifact_type is not None else list(specs.keys())
    for t in types_to_scan:
        root, globs = specs[t]
        if not root.exists():
            continue
        for glob in globs:
            pairs.extend((t, p) for p in root.glob(glob) if p.is_file())

    return pairs


def _read_artifact_summary(candidate: tuple[ArtifactType, Path]) -> ArtifactSummary | None:
    artifact_type, path = candidate

    try:
        relative_path = make_relative(path=path, base=PROJECT_ROOT).path
    except Exception:
        return None

    stat = path.stat()
    updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    size_bytes = int(stat.st_size)

    if artifact_type in {ArtifactType.ADR, ArtifactType.SPEC, ArtifactType.PLAN} and path.suffix == ".json":
        return _read_json_artifact(
            artifact_type=artifact_type,
            path=path,
            relative_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )

    if path.suffix.lower() == ".md":
        return _read_markdown_artifact(
            artifact_type=artifact_type,
            path=path,
            relative_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )

    if artifact_type == ArtifactType.CONTRACT and path.suffix.lower() == ".py":
        return ArtifactSummary(
            id=relative_path,
            type=artifact_type,
            title=path.name,
            status=ArtifactStatus.UNKNOWN,
            file_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )

    return ArtifactSummary(
        id=path.stem,
        type=artifact_type,
        title=path.name,
        status=ArtifactStatus.UNKNOWN,
        file_path=relative_path,
        updated_at=updated_at,
        size_bytes=size_bytes,
    )


def _read_json_artifact(
    artifact_type: ArtifactType,
    path: Path,
    relative_path: str,
    updated_at: datetime,
    size_bytes: int,
) -> ArtifactSummary:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        artifact_id = str(data.get("id") or path.stem)
        title = str(data.get("title") or artifact_id)
        status = _normalize_status(data.get("status"))
        return ArtifactSummary(
            id=artifact_id,
            type=artifact_type,
            title=title,
            status=status,
            file_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )
    except Exception as e:
        return ArtifactSummary(
            id=path.stem,
            type=artifact_type,
            title=f"[Error loading: {e}]",
            status=ArtifactStatus.UNKNOWN,
            file_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )


def _read_markdown_artifact(
    artifact_type: ArtifactType,
    path: Path,
    relative_path: str,
    updated_at: datetime,
    size_bytes: int,
) -> ArtifactSummary:
    try:
        content = path.read_text(encoding="utf-8")
        title = _extract_markdown_title(content) or path.stem
        return ArtifactSummary(
            id=path.stem,
            type=artifact_type,
            title=title,
            status=ArtifactStatus.UNKNOWN,
            file_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )
    except Exception as e:
        return ArtifactSummary(
            id=path.stem,
            type=artifact_type,
            title=f"[Error loading: {e}]",
            status=ArtifactStatus.UNKNOWN,
            file_path=relative_path,
            updated_at=updated_at,
            size_bytes=size_bytes,
        )


def _extract_markdown_title(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _normalize_status(raw: object) -> ArtifactStatus:
    if raw is None:
        return ArtifactStatus.UNKNOWN

    value = str(raw).strip().casefold()
    if value in {"draft", "proposed"}:
        return ArtifactStatus.DRAFT
    if value in {"accepted", "active"}:
        return ArtifactStatus.ACTIVE
    if value == "deprecated":
        return ArtifactStatus.DEPRECATED
    if value in {"superseded", "superceded"}:
        return ArtifactStatus.SUPERSEDED
    return ArtifactStatus.UNKNOWN


def _extract_artifact_references(
    artifact_type: ArtifactType,
    path: Path,
) -> list[tuple[GraphRelationship, str]]:
    if not path.exists():
        return []

    if path.suffix.lower() == ".json" and artifact_type in {
        ArtifactType.ADR,
        ArtifactType.SPEC,
        ArtifactType.PLAN,
    }:
        return _extract_json_references(path)

    if path.suffix.lower() == ".md":
        return _extract_text_references(path)

    return []


def _extract_json_references(path: Path) -> list[tuple[GraphRelationship, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    refs: list[tuple[GraphRelationship, str]] = []

    implements = data.get("implements_adr")
    if isinstance(implements, list):
        for item in implements:
            if isinstance(item, str):
                refs.append((GraphRelationship.IMPLEMENTS, item))

    source_discussion = data.get("source_discussion")
    if isinstance(source_discussion, str) and source_discussion:
        refs.append((GraphRelationship.REFERENCES, source_discussion))

    tier_0_contracts = data.get("tier_0_contracts")
    if isinstance(tier_0_contracts, list):
        for item in tier_0_contracts:
            if isinstance(item, str) and item:
                refs.append((GraphRelationship.REFERENCES, item))

    source_references = data.get("source_references")
    if isinstance(source_references, list):
        for item in source_references:
            if not isinstance(item, dict):
                continue
            ref_id = item.get("id")
            if isinstance(ref_id, str) and ref_id:
                refs.append((GraphRelationship.REFERENCES, ref_id))

    references = data.get("references")
    if isinstance(references, list):
        for item in references:
            if not isinstance(item, str):
                continue
            for token in _extract_reference_tokens(item):
                refs.append((GraphRelationship.REFERENCES, token))

    return refs


def _extract_text_references(path: Path) -> list[tuple[GraphRelationship, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return []

    return [(GraphRelationship.REFERENCES, token) for token in _extract_reference_tokens(content)]


def _extract_reference_tokens(text: str) -> list[str]:
    tokens: list[str] = []

    patterns = [
        r"\bADR-\d{4}\b",
        r"\bSPEC-\d{4}\b",
        r"\bPLAN-\d{3}\b",
        r"\bDISC-\d{3}(?:_[A-Za-z0-9-]+)?\b",
        r"\bshared/contracts/[A-Za-z0-9_\-/]+\.py\b",
    ]

    for pattern in patterns:
        tokens.extend(re.findall(pattern, text))

    return sorted(set(tokens))


def _infer_type_from_id(artifact_id: str) -> ArtifactType | None:
    if artifact_id.startswith("ADR-"):
        return ArtifactType.ADR
    if artifact_id.startswith("SPEC-"):
        return ArtifactType.SPEC
    if artifact_id.startswith("PLAN-"):
        return ArtifactType.PLAN
    if artifact_id.startswith("DISC-"):
        return ArtifactType.DISCUSSION
    if artifact_id.startswith("shared/contracts/") and artifact_id.endswith(".py"):
        return ArtifactType.CONTRACT
    return None


def _write_artifact(request: ArtifactWriteRequest, must_exist: bool) -> ArtifactWriteResponse:
    try:
        rel = RelativePath(path=request.file_path)
    except (PathValidationError, ValueError) as e:
        return ArtifactWriteResponse(
            success=False,
            artifact=None,
            file_path=request.file_path,
            backup_path=None,
            validation_errors=[f"path unsafe: {e}"],
            message="Path unsafe",
        )

    abs_path = (PROJECT_ROOT / rel.to_native()).resolve()
    allowed_root = _artifact_root_for_type(request.type)
    if allowed_root is None:
        return ArtifactWriteResponse(
            success=False,
            artifact=None,
            file_path=rel.path,
            backup_path=None,
            validation_errors=["unsupported artifact type"],
            message="Unsupported artifact type",
        )

    try:
        abs_path.relative_to(allowed_root.resolve())
    except ValueError:
        return ArtifactWriteResponse(
            success=False,
            artifact=None,
            file_path=rel.path,
            backup_path=None,
            validation_errors=["file_path must be within the artifact type root"],
            message="Path not within allowed artifact root",
        )

    if must_exist and not abs_path.exists():
        return ArtifactWriteResponse(
            success=False,
            artifact=None,
            file_path=rel.path,
            backup_path=None,
            validation_errors=["artifact does not exist"],
            message="Artifact not found",
        )

    if not must_exist and abs_path.exists():
        return ArtifactWriteResponse(
            success=False,
            artifact=None,
            file_path=rel.path,
            backup_path=None,
            validation_errors=["artifact already exists"],
            message="Artifact already exists",
        )

    validation_errors: list[str] = []
    if request.format.value == "json":
        try:
            json.loads(request.content)
        except Exception as e:
            validation_errors.append(f"invalid json: {e}")

    if validation_errors:
        return ArtifactWriteResponse(
            success=False,
            artifact=None,
            file_path=rel.path,
            backup_path=None,
            validation_errors=validation_errors,
            message="Validation failed",
        )

    backup_path: str | None = None
    if abs_path.exists() and request.create_backup:
        backup_path = _backup_file(abs_path)

    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(request.content, encoding="utf-8")

    summary = _read_artifact_summary((request.type, abs_path))
    return ArtifactWriteResponse(
        success=True,
        artifact=summary,
        file_path=rel.path,
        backup_path=backup_path,
        validation_errors=[],
        message="Artifact saved",
    )


def _backup_file(abs_path: Path) -> str:
    backup_dir = abs_path.parent / ".backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    backup_name = f"{abs_path.name}.{timestamp}.bak"
    backup_abs_path = backup_dir / backup_name
    abs_path.rename(backup_abs_path)

    return make_relative(path=backup_abs_path, base=PROJECT_ROOT).path


def _artifact_root_for_type(artifact_type: ArtifactType) -> Path | None:
    roots: dict[ArtifactType, Path] = {
        ArtifactType.DISCUSSION: PROJECT_ROOT / ".discussions",
        ArtifactType.ADR: PROJECT_ROOT / ".adrs",
        ArtifactType.SPEC: PROJECT_ROOT / "docs" / "specs",
        ArtifactType.PLAN: PROJECT_ROOT / ".plans",
        ArtifactType.CONTRACT: PROJECT_ROOT / "shared" / "contracts",
    }
    return roots.get(artifact_type)


def _artifact_root_for_relpath(file_path: str) -> Path | None:
    for t, root in {
        ArtifactType.DISCUSSION: PROJECT_ROOT / ".discussions",
        ArtifactType.ADR: PROJECT_ROOT / ".adrs",
        ArtifactType.SPEC: PROJECT_ROOT / "docs" / "specs",
        ArtifactType.PLAN: PROJECT_ROOT / ".plans",
        ArtifactType.CONTRACT: PROJECT_ROOT / "shared" / "contracts",
    }.items():
        if file_path.startswith(make_relative(path=root, base=PROJECT_ROOT).path + "/"):
            return root
    return None
