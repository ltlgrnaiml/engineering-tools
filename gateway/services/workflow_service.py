"""Workflow artifact scanning and graph building service.

Per PLAN-001 M1: Backend API Foundation.
Provides functions for discovering and relating workflow artifacts.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from shared.contracts.devtools.workflow import (
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    FileFormat,
    GenerationResponse,
    GenerationStatus,
    GraphEdge,
    GraphNode,
    GraphResponse,
    PromptResponse,
    RelationshipType,
    WorkflowMode,
    WorkflowScenario,
    WorkflowStage,
    WorkflowState,
)

__version__ = "2025.12.01"

# Get project root (parent of gateway/services/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# =============================================================================
# Constants
# =============================================================================

ARTIFACT_DIRECTORIES: dict[ArtifactType, str] = {
    ArtifactType.DISCUSSION: ".discussions",
    ArtifactType.ADR: ".adrs",
    ArtifactType.SPEC: "docs/specs",
    ArtifactType.PLAN: ".plans",
    ArtifactType.CONTRACT: "shared/contracts",
}

# In-memory workflow storage (POC - would be file-based in production)
_active_workflows: dict[str, WorkflowState] = {}
_generated_content: dict[str, dict] = {}
_workflow_counter = 0

# Scenario to starting stage mapping per ADR-0045
SCENARIO_START_STAGE: dict[WorkflowScenario, WorkflowStage] = {
    WorkflowScenario.NEW_FEATURE: WorkflowStage.DISCUSSION,
    WorkflowScenario.BUG_FIX: WorkflowStage.PLAN,
    WorkflowScenario.ARCHITECTURE_CHANGE: WorkflowStage.DISCUSSION,
    WorkflowScenario.ENHANCEMENT: WorkflowStage.SPEC,
    WorkflowScenario.DATA_STRUCTURE: WorkflowStage.CONTRACT,
}

# Stage progression order
STAGE_ORDER = [
    WorkflowStage.DISCUSSION,
    WorkflowStage.ADR,
    WorkflowStage.SPEC,
    WorkflowStage.CONTRACT,
    WorkflowStage.PLAN,
]

# =============================================================================
# Prompt Templates for AI-Lite Mode (DISC-002)
# =============================================================================

# Prompt structure:
# 1. Role: "You are helping create a {TARGET_TYPE} from a {SOURCE_TYPE}"
# 2. Source Context: Extracted content from source artifact
# 3. Task Description: What the AI should produce
# 4. Target Schema: Minimal schema definition with required fields
# 5. Output Instruction: "Output valid JSON/Python matching this schema"


def _build_discussion_to_adr_prompt(
    artifact_id: str,
    title: str,
    content: dict,
) -> str:
    """Build prompt for Discussion -> ADR transition."""
    summary = content.get("summary", "")
    requirements = content.get("requirements", {})
    func_reqs = requirements.get("functional", [])
    nfunc_reqs = requirements.get("non_functional", [])
    open_questions = content.get("open_questions", [])
    options = content.get("options_considered", [])
    recommendation = content.get("recommendation", "")

    func_req_str = "\n".join(
        f"- {r.get('id', 'FR-?')}: {r.get('description', '')}" for r in func_reqs
    ) if func_reqs else "None captured"

    nfunc_req_str = "\n".join(
        f"- {r.get('id', 'NFR-?')}: {r.get('description', '')}" for r in nfunc_reqs
    ) if nfunc_reqs else "None captured"

    questions_str = "\n".join(
        f"- {q.get('id', 'Q-?')}: {q.get('question', '')} ({q.get('status', 'open')})"
        for q in open_questions
    ) if open_questions else "None"

    options_str = ""
    for opt in options:
        pros = ", ".join(opt.get("pros", []))
        cons = ", ".join(opt.get("cons", []))
        options_str += f"\n### {opt.get('name', 'Option')}\n- Pros: {pros}\n- Cons: {cons}\n"

    return f'''You are helping create an ADR (Architecture Decision Record) from a design discussion.

## Source Discussion
**ID**: {artifact_id}
**Title**: {title}
**Summary**: {summary}

### Functional Requirements Captured
{func_req_str}

### Non-Functional Requirements
{nfunc_req_str}

### Open Questions (these need decisions)
{questions_str}

### Options Considered
{options_str if options_str else "None documented"}

### Recommendation
{recommendation if recommendation else "None stated"}

## Your Task
Create an ADR JSON document that:
1. Captures the architectural DECISION (not just the discussion)
2. Documents the CONTEXT that led to this decision
3. Lists ALTERNATIVES that were considered and why they were rejected
4. Defines GUARDRAILS that must be enforced
5. Lists CONSEQUENCES of this decision

## Required ADR Schema
```json
{{
  "schema_type": "adr",
  "id": "ADR-XXXX_Short-Title",  // REQUIRED: Format ADR-NNNN_Title
  "title": "...",                 // REQUIRED: Min 10 chars
  "status": "proposed",           // proposed | accepted | deprecated | superseded
  "date": "YYYY-MM-DD",           // REQUIRED: Today's date
  "deciders": "...",              // REQUIRED: Who made/approved decision
  "scope": "subsystem:...",       // REQUIRED: e.g., core, subsystem:DAT
  "context": "...",               // REQUIRED: Min 50 chars - problem statement
  "decision_primary": "...",      // REQUIRED: Min 50 chars - what we decided
  "decision_details": {{
    "approach": "...",
    "constraints": ["..."],
    "implementation_specs": []
  }},
  "consequences": ["..."],        // REQUIRED: At least one consequence
  "alternatives_considered": [
    {{
      "name": "...",
      "pros": "...",
      "cons": "...",
      "rejected_reason": "..."
    }}
  ],
  "guardrails": [
    {{
      "id": "G-XXXX-01",
      "rule": "...",
      "enforcement": "...",
      "scope": "..."
    }}
  ],
  "references": [],
  "tags": []
}}
```

Output valid JSON matching this schema.'''


def _build_adr_to_spec_prompt(
    artifact_id: str,
    title: str,
    content: dict,
) -> str:
    """Build prompt for ADR -> SPEC transition."""
    context = content.get("context", "")
    decision = content.get("decision_primary", "")
    details = content.get("decision_details", {})
    approach = details.get("approach", "")
    constraints = details.get("constraints", [])
    guardrails = content.get("guardrails", [])
    consequences = content.get("consequences", [])

    constraints_str = "\n".join(f"- {c}" for c in constraints) if constraints else "None"
    guardrails_str = "\n".join(
        f"- {g.get('id', 'G-?')}: {g.get('rule', '')}" for g in guardrails
    ) if guardrails else "None"
    consequences_str = "\n".join(f"- {c}" for c in consequences) if consequences else "None"

    return f'''You are helping create a SPEC (Specification) that implements an ADR.

## Source ADR
**ID**: {artifact_id}
**Title**: {title}
**Status**: {content.get('status', 'proposed')}

### Context
{context}

### Decision
{decision}

### Approach
{approach}

### Constraints
{constraints_str}

### Guardrails to Enforce
{guardrails_str}

### Consequences
{consequences_str}

## Your Task
Create a SPEC JSON document that:
1. Defines FUNCTIONAL REQUIREMENTS with testable acceptance criteria
2. Defines NON-FUNCTIONAL REQUIREMENTS (performance, security, etc.)
3. Specifies API CONTRACTS if applicable (endpoints, models)
4. Specifies UI COMPONENTS if applicable (hierarchy, state)
5. Defines TEST REQUIREMENTS
6. Breaks work into IMPLEMENTATION MILESTONES

## Required SPEC Schema
```json
{{
  "schema_type": "spec",
  "id": "SPEC-XXXX",              // REQUIRED: Format SPEC-NNNN
  "title": "...",                  // REQUIRED: Descriptive title
  "status": "draft",               // draft | review | accepted
  "created_date": "YYYY-MM-DD",
  "updated_date": "YYYY-MM-DD",
  "implements_adr": ["{artifact_id}"],  // Reference to source ADR
  "overview": {{
    "purpose": "...",              // REQUIRED
    "scope": "...",                // REQUIRED
    "out_of_scope": ["..."]
  }},
  "requirements": {{
    "functional": [
      {{
        "id": "SPEC-XXXX-F01",
        "category": "...",
        "description": "...",       // REQUIRED
        "acceptance_criteria": ["..."]  // REQUIRED: At least one
      }}
    ],
    "non_functional": [
      {{
        "id": "SPEC-XXXX-NF01",
        "category": "Performance|Security|Accessibility",
        "description": "...",
        "acceptance_criteria": ["..."]
      }}
    ]
  }},
  "api_contracts": {{
    "endpoints": [
      {{
        "method": "GET|POST|PUT|DELETE",
        "path": "/api/...",
        "description": "...",
        "request": "ModelName",
        "response": "ModelName"
      }}
    ],
    "models": [
      {{
        "name": "ModelName",
        "type": "model|enum",
        "fields": [
          {{"name": "field", "type": "str", "required": true}}
        ]
      }}
    ]
  }},
  "implementation_milestones": [
    {{
      "id": "M1",
      "name": "...",
      "tasks": ["..."],
      "acceptance_criteria": ["..."]
    }}
  ]
}}
```

Output valid JSON matching this schema.'''


def _build_spec_to_plan_prompt(
    artifact_id: str,
    title: str,
    content: dict,
    adr_content: dict | None = None,
) -> str:
    """Build prompt for SPEC -> Plan transition."""
    overview = content.get("overview", {})
    if isinstance(overview, dict):
        purpose = overview.get("purpose", "")
        scope = overview.get("scope", "")
    else:
        purpose = ""
        scope = ""
    requirements = content.get("requirements", {})
    # Handle both dict and list formats for requirements
    if isinstance(requirements, dict):
        func_reqs = requirements.get("functional", [])
    elif isinstance(requirements, list):
        func_reqs = requirements
    else:
        func_reqs = []
    api_contracts = content.get("api_contracts", {})
    if not isinstance(api_contracts, dict):
        api_contracts = {}
    milestones = content.get("implementation_milestones", [])
    implements_adr = content.get("implements_adr", [])

    func_req_str = "\n".join(
        f"- {r.get('id', 'F?')}: {r.get('description', '') if isinstance(r, dict) else str(r)}"
        for r in func_reqs
    ) if func_reqs else "None specified"

    endpoints = api_contracts.get("endpoints", [])
    endpoints_str = "\n".join(
        f"- {e.get('method', '?')} {e.get('path', '?')}: {e.get('description', '')}"
        for e in endpoints
    ) if endpoints else "None specified"

    milestone_str = "\n".join(
        f"- {m.get('id', 'M?')}: {m.get('name', '')}" for m in milestones
    ) if milestones else "None specified"

    adr_section = ""
    if adr_content:
        adr_section = f'''
### Referenced ADR
**ID**: {adr_content.get('id', 'Unknown')}
**Decision**: {adr_content.get('decision_primary', 'Unknown')}
**Guardrails**:
''' + "\n".join(
            f"- {g.get('rule', '')}" for g in adr_content.get('guardrails', [])
        )

    return f'''You are helping create an implementation Plan from a SPEC.

## Source SPEC
**ID**: {artifact_id}
**Title**: {title}
**Implements ADR**: {", ".join(implements_adr) if implements_adr else "None"}

### Purpose
{purpose}

### Scope
{scope}
{adr_section}

### Functional Requirements
{func_req_str}

### API Endpoints
{endpoints_str}

### Suggested Milestones
{milestone_str}

## Your Task
Create a Plan JSON document that:
1. References all source artifacts (SPEC, ADR)
2. Breaks work into MILESTONES
3. Each milestone has TASKS with verification commands
4. Each task has CONTEXT (files, patterns to follow)
5. Includes GLOBAL ACCEPTANCE CRITERIA
6. Enforces all ADR GUARDRAILS as constraints

## Required Plan Schema
```json
{{
  "schema_type": "plan",
  "id": "PLAN-XXX",                // REQUIRED: Format PLAN-NNN
  "title": "...",                   // REQUIRED: Descriptive title
  "status": "draft",                // draft | active | in_progress | completed
  "granularity": "L1",              // L1 (standard) | L2 (enhanced) | L3 (procedural)
  "created_date": "YYYY-MM-DD",
  "updated_date": "YYYY-MM-DD",
  "author": "...",
  "summary": "...",                 // REQUIRED
  "objective": "...",               // REQUIRED: What success looks like
  "source_references": [
    {{"type": "spec", "id": "{artifact_id}", "title": "{title}"}}
  ],
  "prerequisites": ["..."],
  "milestones": [
    {{
      "id": "M1",                   // REQUIRED: Format MN
      "name": "...",                // REQUIRED
      "objective": "...",           // REQUIRED
      "tasks": [
        {{
          "id": "T-M1-01",          // REQUIRED: Format T-MN-NN
          "description": "...",     // REQUIRED
          "verification_command": "grep '...' path/to/file",  // REQUIRED
          "context": [
            "FILE: path/to/modify.py",
            "ARCHITECTURE: Follow existing patterns in X"
          ]
        }}
      ],
      "acceptance_criteria": [
        {{
          "id": "AC-M1-01",
          "description": "...",
          "verification_command": "pytest tests/..."
        }}
      ]
    }}
  ],
  "global_acceptance_criteria": [
    {{
      "id": "AC-GLOBAL-01",
      "description": "All tests pass",
      "verification_command": "pytest tests/ -v"
    }}
  ]
}}
```

Output valid JSON matching this schema.'''


def _build_spec_to_contract_prompt(
    artifact_id: str,
    title: str,
    content: dict,
) -> str:
    """Build prompt for SPEC -> Contract transition."""
    api_contracts = content.get("api_contracts", {})
    models = api_contracts.get("models", [])

    models_str = ""
    for m in models:
        if isinstance(m, dict):
            name = m.get("name", "Unknown")
            mtype = m.get("type", "model")
            fields = m.get("fields", [])
            fields_str = "\n".join(
                f"    - {f.get('name', '?')}: {f.get('type', '?')}"
                for f in fields
            ) if fields else "    (no fields defined)"
            models_str += f"\n### {name} ({mtype})\n{fields_str}\n"
        else:
            models_str += f"\n### {m}\n"

    return f'''You are helping create Pydantic contracts from a SPEC.

## Source SPEC
**ID**: {artifact_id}
**Title**: {title}

### API Models Defined
{models_str if models_str else "No models defined in SPEC"}

## Your Task
Create Pydantic model definitions that:
1. Follow the existing contract patterns in this project
2. Use proper type hints (Python 3.9+ style: list[], dict[], X | None)
3. Include Field descriptions
4. Add validators where appropriate
5. Include __version__ = "YYYY.MM.01" at top

## Contract Template
```python
"""Contract for {{domain}}.

Per SPEC-{artifact_id}: {title}.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator

__version__ = "2025.12.01"


class ModelName(BaseModel):
    """Description of this model."""
    
    field_name: str = Field(..., description="Required field")
    optional_field: str | None = Field(None, description="Optional field")
    enum_field: Literal["value1", "value2"] = Field(..., description="Enum field")
    list_field: list[str] = Field(default_factory=list, description="List field")
    
    @field_validator("field_name")
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field_name."""
        if not v:
            raise ValueError("field_name cannot be empty")
        return v
    
    model_config = {{"extra": "forbid", "str_strip_whitespace": True}}
```

Output valid Python code matching this pattern.'''


# Legacy simple templates (kept for fallback)
SIMPLE_PROMPT_TEMPLATES: dict[tuple[ArtifactType, ArtifactType], str] = {
    (ArtifactType.DISCUSSION, ArtifactType.ADR): (
        "Please review {artifact_id} ('{title}') and create an ADR capturing "
        "the key decisions. Focus on the context, decision, and consequences."
    ),
    (ArtifactType.ADR, ArtifactType.SPEC): (
        "ADR {artifact_id} ('{title}') is approved. Please create a detailed "
        "SPEC with functional requirements, API contracts, and acceptance criteria."
    ),
    (ArtifactType.SPEC, ArtifactType.PLAN): (
        "SPEC {artifact_id} ('{title}') is ready. Please create an implementation "
        "Plan with milestones, tasks, and verification commands."
    ),
    (ArtifactType.SPEC, ArtifactType.CONTRACT): (
        "Based on SPEC {artifact_id} ('{title}'), please create the Pydantic "
        "contract models in shared/contracts/."
    ),
    (ArtifactType.PLAN, ArtifactType.ADR): (
        "Plan {artifact_id} revealed architectural decisions. Please create "
        "an ADR to document them."
    ),
}


# =============================================================================
# Artifact Scanning
# =============================================================================


def scan_artifacts(
    artifact_type: ArtifactType | None = None,
    search: str | None = None,
) -> list[ArtifactSummary]:
    """Scan filesystem for workflow artifacts.

    Args:
        artifact_type: Filter by artifact type (optional).
        search: Filter by title/ID containing this string (optional).

    Returns:
        List of artifact summaries found.
    """
    results: list[ArtifactSummary] = []
    types_to_scan = [artifact_type] if artifact_type else list(ArtifactType)

    for atype in types_to_scan:
        directory = Path(ARTIFACT_DIRECTORIES[atype])
        if not directory.exists():
            continue

        # Determine file patterns based on artifact type
        # Plans can be both .json and .md, so scan both
        if atype == ArtifactType.ADR or atype == ArtifactType.SPEC:
            patterns = ["*.json"]
        elif atype == ArtifactType.CONTRACT:
            patterns = ["*.py"]
        elif atype == ArtifactType.PLAN:
            patterns = ["*.json", "*.md"]  # Plans can be JSON or Markdown
        else:
            patterns = ["*.md"]

        for pattern in patterns:
          for file_path in directory.rglob(pattern):
            # Skip templates, __init__.py, __pycache__, L3 chunks, etc.
            if (
                file_path.name.startswith(".")
                or file_path.name.startswith("_")
                or "template" in file_path.name.lower()
                or "__pycache__" in str(file_path)
                or file_path.name == "AGENTS.md"
                or file_path.name == "INDEX.md"
                or file_path.name == "INDEX.json"
                or file_path.name == "EXECUTION.md"
                or "/L3/" in str(file_path).replace("\\", "/")  # Skip L3 chunk files
            ):
                continue

            artifact = _parse_artifact(file_path, atype)
            if artifact:
                # Apply search filter
                if search:
                    search_lower = search.lower()
                    if (
                        search_lower not in artifact.title.lower()
                        and search_lower not in artifact.id.lower()
                    ):
                        continue
                results.append(artifact)

    # Deduplicate by ID, preferring JSON over markdown
    seen_ids: dict[str, ArtifactSummary] = {}
    for artifact in results:
        if artifact.id not in seen_ids:
            seen_ids[artifact.id] = artifact
        elif artifact.file_format == FileFormat.JSON:
            # JSON takes precedence over markdown for same ID
            seen_ids[artifact.id] = artifact

    return sorted(seen_ids.values(), key=lambda a: a.id)


def _get_file_format(file_path: Path) -> FileFormat:
    """Determine file format from extension.

    Args:
        file_path: Path to the file.

    Returns:
        FileFormat enum value.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return FileFormat.JSON
    elif suffix == ".md":
        return FileFormat.MARKDOWN
    elif suffix == ".py":
        return FileFormat.PYTHON
    else:
        return FileFormat.UNKNOWN


def _parse_artifact(file_path: Path, atype: ArtifactType) -> ArtifactSummary | None:
    """Parse artifact metadata from file.

    Args:
        file_path: Path to artifact file.
        atype: Type of artifact.

    Returns:
        ArtifactSummary or None if parsing fails.
    """
    try:
        # Route by file extension first, then artifact type
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            return _parse_json_artifact(file_path, atype)
        elif suffix == ".py":
            return _parse_python_artifact(file_path)
        elif suffix == ".md":
            return _parse_markdown_artifact(file_path, atype)
        else:
            return None
    except Exception:
        return None


def _parse_json_artifact(file_path: Path, atype: ArtifactType) -> ArtifactSummary | None:
    """Parse JSON-based artifact (ADR, SPEC)."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    artifact_id = data.get("id", file_path.stem)
    title = data.get("title", artifact_id)
    status_str = data.get("status", "draft")
    updated_date = data.get("updated_date")

    # Map status string to enum
    try:
        status = ArtifactStatus(status_str)
    except ValueError:
        status = ArtifactStatus.DRAFT

    return ArtifactSummary(
        id=artifact_id,
        type=atype,
        title=title,
        status=status,
        file_path=str(file_path),
        file_format=_get_file_format(file_path),
        updated_date=updated_date,
    )


def _parse_markdown_artifact(
    file_path: Path, atype: ArtifactType
) -> ArtifactSummary | None:
    """Parse markdown-based artifact (Discussion, Plan)."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read(2000)  # Read first 2KB for metadata

    # Extract ID from filename (e.g., DISC-001_title.md -> DISC-001)
    match = re.match(r"^(DISC-\d+|PLAN-\d+)", file_path.stem)
    artifact_id = match.group(1) if match else file_path.stem

    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else artifact_id

    # Try to detect status from content
    if "status: active" in content.lower() or "## active" in content.lower():
        status = ArtifactStatus.ACTIVE
    elif "status: completed" in content.lower():
        status = ArtifactStatus.COMPLETED
    else:
        status = ArtifactStatus.DRAFT

    return ArtifactSummary(
        id=artifact_id,
        type=atype,
        title=title,
        status=status,
        file_path=str(file_path),
        file_format=_get_file_format(file_path),
        updated_date=None,
    )


def _parse_python_artifact(file_path: Path) -> ArtifactSummary | None:
    """Parse Python contract file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read(1000)  # Read first 1KB

    # Use module name as ID
    artifact_id = file_path.stem

    # Extract docstring for title
    docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
    if docstring_match:
        # First line of docstring
        title = docstring_match.group(1).strip().split("\n")[0]
    else:
        title = artifact_id

    return ArtifactSummary(
        id=artifact_id,
        type=ArtifactType.CONTRACT,
        title=title,
        status=ArtifactStatus.ACTIVE,
        file_path=str(file_path),
        file_format=FileFormat.PYTHON,
        updated_date=None,
    )


# =============================================================================
# Graph Building
# =============================================================================


def _extract_short_id(full_id: str) -> str:
    """Extract short ID prefix from full artifact ID.
    
    Examples:
        ADR-0001_guided-workflow -> ADR-0001
        DISC-001_DevTools-AI -> DISC-001
        SPEC-0043_knowledge-archive -> SPEC-0043
    """
    patterns = [
        r'^(ADR-\d{4})',
        r'^(SPEC-\d{4})',
        r'^(DISC-\d{3})',
        r'^(PLAN-\d{3})',
    ]
    for pattern in patterns:
        match = re.match(pattern, full_id)
        if match:
            return match.group(1)
    return full_id  # Return as-is if no pattern matches


def build_artifact_graph(use_rag_db: bool = True) -> GraphResponse:
    """Build the artifact relationship graph.

    Args:
        use_rag_db: If True, use RAG DB relationships table (preferred).
                    If False, fall back to file parsing.

    Returns:
        GraphResponse with nodes and edges representing artifact relationships.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    artifacts = scan_artifacts()

    # Create nodes and build ID mappings
    artifact_ids = set()
    short_to_full: dict[str, str] = {}  # Map short IDs to full IDs

    for artifact in artifacts:
        artifact_ids.add(artifact.id)
        # Build short ID mapping (ADR-0001 -> ADR-0001_full-title)
        short_id = _extract_short_id(artifact.id)
        short_to_full[short_id] = artifact.id
        short_to_full[artifact.id] = artifact.id  # Also map full to full

        nodes.append(
            GraphNode(
                id=artifact.id,
                type=artifact.type,
                label=artifact.title,
                status=artifact.status,
                file_path=artifact.file_path,
            )
        )

    # Build edges from RAG DB relationships table (preferred - already relational)
    if use_rag_db:
        try:
            from gateway.services.knowledge.database import get_connection
            conn = get_connection()
            rows = conn.execute("""
                SELECT DISTINCT source_id, target_id, relationship_type
                FROM relationships
            """).fetchall()

            for row in rows:
                source_id = row['source_id']
                target_id = row['target_id']
                rel_type = row['relationship_type']

                # Resolve short IDs to full IDs
                resolved_source = short_to_full.get(source_id)
                resolved_target = short_to_full.get(target_id)

                # Only include edges where both nodes can be resolved
                if resolved_source and resolved_target:
                    # Map relationship types
                    if rel_type == 'implements':
                        relationship = RelationshipType.IMPLEMENTS
                    elif rel_type == 'creates':
                        relationship = RelationshipType.CREATES
                    else:
                        relationship = RelationshipType.REFERENCES

                    edges.append(
                        GraphEdge(
                            source=resolved_source,
                            target=resolved_target,
                            relationship=relationship,
                        )
                    )
            conn.close()

            # If we got edges from RAG DB, return early
            if edges:
                return GraphResponse(nodes=nodes, edges=edges)
        except Exception:
            pass  # Fall back to file parsing

    # Fallback: Build edges by scanning files for references
    for artifact in artifacts:
        if artifact.type in (ArtifactType.ADR, ArtifactType.SPEC):
            try:
                with open(artifact.file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Check implements_adr field (SPEC -> ADR)
                implements = data.get("implements_adr", [])
                for adr_id in implements:
                    if adr_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=adr_id,
                                relationship=RelationshipType.IMPLEMENTS,
                            )
                        )

                # Check resulting_specs field (ADR -> SPEC)
                specs = data.get("resulting_specs", [])
                for spec in specs:
                    spec_id = spec.get("id") if isinstance(spec, dict) else spec
                    if spec_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=spec_id,
                                relationship=RelationshipType.CREATES,
                            )
                        )

                # Check source_references in plans
                refs = data.get("source_references", [])
                for ref in refs:
                    ref_id = ref.get("id") if isinstance(ref, dict) else ref
                    if ref_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=ref_id,
                                relationship=RelationshipType.REFERENCES,
                            )
                        )

                # Check references array
                refs = data.get("references", [])
                for ref in refs:
                    ref_id = ref.get("id") if isinstance(ref, dict) else ref
                    if ref_id and ref_id in artifact_ids:
                        edges.append(
                            GraphEdge(
                                source=artifact.id,
                                target=ref_id,
                                relationship=RelationshipType.REFERENCES,
                            )
                        )

            except Exception:
                pass

    return GraphResponse(nodes=nodes, edges=edges)


# =============================================================================
# Workflow Orchestration (M10)
# =============================================================================


def create_workflow(
    mode: WorkflowMode,
    scenario: WorkflowScenario,
    title: str,
) -> WorkflowState:
    """Create a new workflow session.

    Args:
        mode: Automation mode (manual, ai_lite, ai_full).
        scenario: Entry point scenario.
        title: Workflow title.

    Returns:
        WorkflowState for the new workflow.
    """
    global _workflow_counter
    _workflow_counter += 1
    workflow_id = f"WF-{_workflow_counter:03d}"

    start_stage = SCENARIO_START_STAGE.get(scenario, WorkflowStage.DISCUSSION)

    workflow = WorkflowState(
        id=workflow_id,
        mode=mode,
        scenario=scenario,
        title=title,
        current_stage=start_stage,
        artifacts_created=[],
        created_at=datetime.now().isoformat(),
    )
    _active_workflows[workflow_id] = workflow
    return workflow


def get_workflow_status(workflow_id: str) -> WorkflowState | None:
    """Get current status of a workflow.

    Args:
        workflow_id: The workflow ID (e.g., WF-001).

    Returns:
        WorkflowState if found, None otherwise.
    """
    return _active_workflows.get(workflow_id)


def advance_workflow(workflow_id: str) -> WorkflowStage | None:
    """Advance workflow to the next stage.

    Args:
        workflow_id: The workflow ID.

    Returns:
        New WorkflowStage if advanced, None if at end or not found.
    """
    workflow = _active_workflows.get(workflow_id)
    if not workflow:
        return None

    current_idx = STAGE_ORDER.index(workflow.current_stage)
    if current_idx >= len(STAGE_ORDER) - 1:
        return None  # Already at last stage

    next_stage = STAGE_ORDER[current_idx + 1]
    workflow.current_stage = next_stage
    return next_stage


def generate_prompt(
    artifact_id: str,
    target_type: ArtifactType,
) -> PromptResponse:
    """Generate context-aware prompt for AI-Lite mode.

    Per DISC-002: Generates comprehensive prompts that include:
    1. Source artifact content extraction
    2. Target schema with required fields
    3. Clear instructions for AI

    Args:
        artifact_id: Source artifact ID.
        target_type: Target artifact type to create.

    Returns:
        PromptResponse with generated prompt.
    """
    # Find source artifact
    artifacts = scan_artifacts()
    source = next((a for a in artifacts if a.id == artifact_id), None)

    if not source:
        return PromptResponse(
            prompt=f"Create a new {target_type.value} artifact.",
            target_type=target_type,
            context={"error": f"Source artifact {artifact_id} not found"},
        )

    # Load source artifact content for rich prompts
    content = _load_artifact_content(source.file_path)

    # Generate prompt based on source->target transition
    prompt = _generate_rich_prompt(
        source_type=source.type,
        target_type=target_type,
        artifact_id=artifact_id,
        title=source.title,
        content=content,
    )

    return PromptResponse(
        prompt=prompt,
        target_type=target_type,
        context={
            "source_id": artifact_id,
            "source_type": source.type.value,
            "source_title": source.title,
            "target_type": target_type.value,
            "prompt_version": "2.0",  # Rich prompt version
        },
    )


def _load_artifact_content(file_path: str) -> dict:
    """Load artifact content from file.

    Args:
        file_path: Path to artifact file.

    Returns:
        Dictionary with artifact content (or empty dict on failure).
    """
    try:
        path = Path(file_path)
        if path.suffix == ".json":
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        elif path.suffix == ".md":
            return _parse_markdown_to_dict(path)
        else:
            return {}
    except Exception:
        return {}


def _parse_markdown_to_dict(file_path: Path) -> dict:
    """Parse markdown discussion file to dictionary.

    Args:
        file_path: Path to markdown file.

    Returns:
        Dictionary with extracted content.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        result: dict = {"raw_content": content}

        # Extract summary (text after ## Summary)
        summary_match = re.search(
            r"##\s*Summary\s*\n+(.+?)(?=\n##|\n---|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if summary_match:
            result["summary"] = summary_match.group(1).strip()

        # Extract requirements
        func_reqs = []
        for match in re.finditer(
            r"-\s*\[.\]\s*\*\*(FR-\d+)\*\*:\s*(.+)", content
        ):
            func_reqs.append({"id": match.group(1), "description": match.group(2).strip()})

        nfunc_reqs = []
        for match in re.finditer(
            r"-\s*\[.\]\s*\*\*(NFR-\d+)\*\*:\s*(.+)", content
        ):
            nfunc_reqs.append({"id": match.group(1), "description": match.group(2).strip()})

        if func_reqs or nfunc_reqs:
            result["requirements"] = {
                "functional": func_reqs,
                "non_functional": nfunc_reqs,
            }

        # Extract open questions
        questions = []
        question_section = re.search(
            r"##\s*Open Questions\s*\n+(.+?)(?=\n##|\n---|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if question_section:
            for match in re.finditer(
                r"\|\s*(Q-\d+)\s*\|\s*(.+?)\s*\|\s*`?(\w+)`?\s*\|",
                question_section.group(1),
            ):
                questions.append({
                    "id": match.group(1),
                    "question": match.group(2).strip(),
                    "status": match.group(3).strip(),
                })
        result["open_questions"] = questions

        # Extract recommendation
        rec_match = re.search(
            r"###\s*Recommendation\s*\n+(.+?)(?=\n##|\n###|\n---|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if rec_match:
            result["recommendation"] = rec_match.group(1).strip()

        return result
    except Exception:
        return {}


def _generate_rich_prompt(
    source_type: ArtifactType,
    target_type: ArtifactType,
    artifact_id: str,
    title: str,
    content: dict,
) -> str:
    """Generate a rich, context-aware prompt.

    Args:
        source_type: Type of source artifact.
        target_type: Type of target artifact to create.
        artifact_id: Source artifact ID.
        title: Source artifact title.
        content: Loaded source artifact content.

    Returns:
        Generated prompt string.
    """
    # Route to appropriate prompt builder
    if source_type == ArtifactType.DISCUSSION and target_type == ArtifactType.ADR:
        return _build_discussion_to_adr_prompt(artifact_id, title, content)

    elif source_type == ArtifactType.ADR and target_type == ArtifactType.SPEC:
        return _build_adr_to_spec_prompt(artifact_id, title, content)

    elif source_type == ArtifactType.SPEC and target_type == ArtifactType.PLAN:
        # Try to load referenced ADR for additional context
        adr_content = None
        implements_adr = content.get("implements_adr", [])
        if implements_adr:
            adr_artifacts = scan_artifacts(ArtifactType.ADR)
            adr = next((a for a in adr_artifacts if a.id == implements_adr[0]), None)
            if adr:
                adr_content = _load_artifact_content(adr.file_path)
        return _build_spec_to_plan_prompt(artifact_id, title, content, adr_content)

    elif source_type == ArtifactType.SPEC and target_type == ArtifactType.CONTRACT:
        return _build_spec_to_contract_prompt(artifact_id, title, content)

    else:
        # Fallback to simple template
        template_key = (source_type, target_type)
        template = SIMPLE_PROMPT_TEMPLATES.get(
            template_key,
            f"Based on {source_type.value} {{artifact_id}} ('{{title}}'), please create a {target_type.value}.",
        )
        return template.format(artifact_id=artifact_id, title=title)


# =============================================================================
# AI-Full Mode Generation (M12)
# =============================================================================

# Content templates for AI-Full generation (placeholder - AI integration later)
GENERATION_TEMPLATES: dict[ArtifactType, dict] = {
    ArtifactType.DISCUSSION: {
        "title": "{title}",
        "status": "draft",
        "content": "# {title}\n\n## Background\n\n{description}\n\n## Questions\n\n1. TBD\n\n## Next Steps\n\n- [ ] Define requirements",
    },
    ArtifactType.ADR: {
        "id": "ADR-XXXX",
        "title": "{title}",
        "status": "draft",
        "context": "Generated from workflow: {description}",
        "decision": "TBD",
        "consequences": ["TBD"],
    },
    ArtifactType.SPEC: {
        "id": "SPEC-XXXX",
        "title": "{title}",
        "status": "draft",
        "summary": "{description}",
        "requirements": [],
    },
    ArtifactType.PLAN: {
        "id": "PLAN-XXX",
        "title": "{title}",
        "status": "draft",
        "milestones": [],
    },
}


def _get_rag_context(
    query: str,
    artifact_type: str | None = None,
    use_reranking: bool = True,
) -> str:
    """Retrieve relevant context from Knowledge Archive via Enhanced RAG.
    
    Uses multi-level retrieval:
    - Level 1: Query Enhancement (always on)
    - Level 2: LLM Re-ranking (configurable via use_reranking)
    - Level 3: Graph-Aware Retrieval (always on)
    
    Args:
        query: Search query for relevant documents.
        artifact_type: Type of artifact being generated (for query expansion).
        use_reranking: Whether to use LLM re-ranking (UI toggle).
        
    Returns:
        Formatted context string with relevant ADRs, SPECs, etc.
    """
    try:
        from gateway.services.knowledge.enhanced_rag import get_enhanced_context
        return get_enhanced_context(query, artifact_type, use_reranking)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Enhanced RAG context retrieval failed: {e}")
        return ""


def generate_artifact_content(
    artifact_type: ArtifactType,
    title: str,
    description: str = "",
    use_llm: bool = True,
    use_rag: bool = True,
    use_reranking: bool = True,
) -> dict:
    """Generate content for an artifact based on type.

    Uses xAI LLM for intelligent generation with structured output.
    Optionally retrieves RAG context from Knowledge Archive.
    Falls back to templates if LLM is unavailable.

    Args:
        artifact_type: Type of artifact to generate.
        title: Title for the artifact.
        description: Optional description/context.
        use_llm: Whether to use LLM generation (default True).
        use_rag: Whether to include RAG context (default True).
        use_reranking: Whether to use LLM re-ranking for RAG (default True, UI toggle).

    Returns:
        Dictionary with generated content.
    """
    from gateway.services.llm_service import (
        ARTIFACT_SCHEMAS,
        generate_structured,
        is_available,
    )

    # Try LLM generation if enabled and available
    if use_llm and is_available():
        schema = ARTIFACT_SCHEMAS.get(artifact_type.value)
        if schema:
            # Get RAG context if enabled
            rag_context = ""
            if use_rag:
                rag_query = f"{title} {description}"
                rag_context = _get_rag_context(
                    query=rag_query,
                    artifact_type=artifact_type.value,
                    use_reranking=use_reranking,
                )

            prompt = _build_generation_prompt(artifact_type, title, description, rag_context)

            system_prompt = f"""You are generating a {artifact_type.value} artifact for the Engineering Tools platform.
This is a solo-dev, AI-assisted project following first-principles development.
Use the PROJECT CONTEXT to reference existing ADRs, patterns, and conventions.
Be specific to this project - avoid generic boilerplate."""

            response = generate_structured(
                prompt=prompt,
                schema=schema,
                system_prompt=system_prompt,
            )

            if response.success and response.data:
                return response.data

    # Fallback to template-based generation
    template = GENERATION_TEMPLATES.get(artifact_type, {})
    content = {}

    for key, value in template.items():
        if isinstance(value, str):
            content[key] = value.format(title=title, description=description or title)
        else:
            content[key] = value

    return content


def _build_generation_prompt(
    artifact_type: ArtifactType,
    title: str,
    description: str,
    rag_context: str = "",
) -> str:
    """Build a prompt for generating an artifact.

    Args:
        artifact_type: Type of artifact to generate.
        title: Title for the artifact.
        description: Description/context for generation.
        rag_context: Optional RAG context from Knowledge Archive.

    Returns:
        Prompt string for the LLM.
    """
    base_context = f"""
Title: {title}
Description: {description or 'No additional description provided.'}

{rag_context}
"""

    prompts = {
        ArtifactType.DISCUSSION: f"""Generate a Discussion artifact for capturing design conversations.

{base_context}

Create a comprehensive discussion document that:
1. Has a clear summary of the topic
2. Provides context for why this discussion is needed
3. Lists functional requirements (FR-1, FR-2, etc.)
4. Lists non-functional requirements (NFR-1, NFR-2, etc.)
5. Includes open questions that need to be resolved
6. Optionally includes a recommendation

Use ID format: DISC-XXX (pick appropriate number)""",

        ArtifactType.ADR: f"""Generate an Architecture Decision Record (ADR) artifact.

{base_context}

Create a comprehensive ADR that:
1. Clearly describes the context and problem
2. States the primary decision
3. Lists decision details/rationale
4. Describes consequences (positive and negative)
5. Lists alternatives that were considered
6. Optionally includes tradeoffs

Use ID format: ADR-XXXX (pick appropriate number)
Status should be: proposed""",

        ArtifactType.SPEC: f"""Generate a Specification (SPEC) artifact.

{base_context}

Create a comprehensive specification that:
1. Clearly states the purpose
2. Defines the scope
3. Lists functional requirements with IDs (FR-1, FR-2, etc.)
4. Lists non-functional requirements with IDs (NFR-1, NFR-2, etc.)
5. Optionally defines API endpoints if applicable
6. Lists acceptance criteria

Use ID format: SPEC-XXXX (pick appropriate number)
Status should be: draft""",

        ArtifactType.PLAN: f"""Generate an Implementation Plan artifact.

{base_context}

Create a comprehensive plan that:
1. Has a clear objective
2. Breaks work into milestones with IDs (M1, M2, etc.)
3. Each milestone should have a name, description, and tasks
4. Lists success criteria for the overall plan

Use ID format: PLAN-XXX (pick appropriate number)
Status should be: draft""",
    }

    return prompts.get(artifact_type, f"Generate a {artifact_type.value} artifact.\n{base_context}")


def generate_full_workflow(
    workflow_id: str,
    title: str,
    description: str = "",
    use_reranking: bool = True,
) -> GenerationResponse:
    """Generate all artifacts for a full workflow.

    Args:
        workflow_id: The workflow ID.
        title: Title for the workflow.
        description: Description/context.
        use_reranking: Whether to use LLM re-ranking for RAG (default True, UI toggle).

    Returns:
        GenerationResponse with all created artifacts.
    """
    workflow = _active_workflows.get(workflow_id)
    if not workflow:
        return GenerationResponse(
            artifacts=[],
            status=GenerationStatus.FAILED,
            errors=[f"Workflow {workflow_id} not found"],
        )

    if workflow.mode != WorkflowMode.AI_FULL:
        return GenerationResponse(
            artifacts=[],
            status=GenerationStatus.FAILED,
            errors=["Full generation only available in AI-Full mode"],
        )

    artifacts: list[ArtifactSummary] = []
    errors: list[str] = []

    # Generate artifacts based on scenario
    types_to_generate = [
        ArtifactType.DISCUSSION,
        ArtifactType.ADR,
        ArtifactType.SPEC,
        ArtifactType.PLAN,
    ]

    # Ensure output directory exists
    output_dir = PROJECT_ROOT / "workspace" / "generated" / workflow_id
    output_dir.mkdir(parents=True, exist_ok=True)

    for atype in types_to_generate:
        try:
            content = generate_artifact_content(
                atype, title, description, use_reranking=use_reranking
            )
            artifact_id = f"{atype.value.upper()}-GEN-{workflow_id}"

            # Write to file for persistence
            file_path = output_dir / f"{atype.value.upper()}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "id": artifact_id,
                    "type": atype.value,
                    "title": title,
                    "description": description,
                    "generated_at": datetime.now().isoformat(),
                    "content": content,
                }, f, indent=2)

            artifact = ArtifactSummary(
                id=artifact_id,
                type=atype,
                title=title,
                status=ArtifactStatus.DRAFT,
                file_path=str(file_path.relative_to(PROJECT_ROOT)),
            )
            artifacts.append(artifact)
            workflow.artifacts_created.append(artifact_id)
            # Store generated content for retrieval (also keep in memory)
            _generated_content[artifact_id] = content
        except Exception as e:
            errors.append(f"Failed to generate {atype.value}: {e}")

    status = GenerationStatus.COMPLETED if not errors else GenerationStatus.FAILED
    return GenerationResponse(artifacts=artifacts, status=status, errors=errors)


def get_generated_content(artifact_id: str) -> dict | None:
    """Retrieve generated content by artifact ID.

    Args:
        artifact_id: The artifact ID (e.g., DISCUSSION-GEN-WF-001).

    Returns:
        The generated content dict, or None if not found.
    """
    return _generated_content.get(artifact_id)
