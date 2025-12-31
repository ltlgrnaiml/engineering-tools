"""Tests for DevTools Workflow Manager endpoints.

Per PLAN-001 M1: Backend API Foundation.
"""

import pytest

from gateway.services.workflow_service import build_artifact_graph, scan_artifacts
from shared.contracts.devtools.workflow import (
    ArtifactSummary,
    ArtifactType,
    GraphResponse,
)


class TestScanArtifacts:
    """Tests for scan_artifacts function."""

    def test_scan_all_artifacts(self) -> None:
        """Scan should return artifacts from all directories."""
        results = scan_artifacts()
        assert isinstance(results, list)
        # Should find at least some artifacts in the repo
        assert len(results) > 0

    def test_scan_by_type_adr(self) -> None:
        """Scan should filter by ADR type."""
        results = scan_artifacts(artifact_type=ArtifactType.ADR)
        assert isinstance(results, list)
        for artifact in results:
            assert artifact.type == ArtifactType.ADR

    def test_scan_by_type_spec(self) -> None:
        """Scan should filter by SPEC type."""
        results = scan_artifacts(artifact_type=ArtifactType.SPEC)
        assert isinstance(results, list)
        for artifact in results:
            assert artifact.type == ArtifactType.SPEC

    def test_scan_by_type_plan(self) -> None:
        """Scan should filter by PLAN type."""
        results = scan_artifacts(artifact_type=ArtifactType.PLAN)
        assert isinstance(results, list)
        for artifact in results:
            assert artifact.type == ArtifactType.PLAN

    def test_scan_with_search(self) -> None:
        """Scan should filter by search term."""
        # Search for "workflow" which should match ADR-0043, SPEC-0040, etc.
        results = scan_artifacts(search="workflow")
        assert isinstance(results, list)
        # All results should contain the search term in title or id
        for artifact in results:
            assert (
                "workflow" in artifact.title.lower()
                or "workflow" in artifact.id.lower()
            )

    def test_artifact_summary_structure(self) -> None:
        """Each artifact should have required fields."""
        results = scan_artifacts()
        if results:
            artifact = results[0]
            assert isinstance(artifact, ArtifactSummary)
            assert artifact.id is not None
            assert artifact.type is not None
            assert artifact.title is not None
            assert artifact.status is not None
            assert artifact.file_path is not None


class TestBuildArtifactGraph:
    """Tests for build_artifact_graph function."""

    def test_graph_structure(self) -> None:
        """Graph should have nodes and edges lists."""
        graph = build_artifact_graph()
        assert isinstance(graph, GraphResponse)
        assert isinstance(graph.nodes, list)
        assert isinstance(graph.edges, list)

    def test_graph_has_nodes(self) -> None:
        """Graph should have at least one node."""
        graph = build_artifact_graph()
        assert len(graph.nodes) > 0

    def test_node_structure(self) -> None:
        """Each node should have required fields."""
        graph = build_artifact_graph()
        for node in graph.nodes:
            assert node.id is not None
            assert node.type is not None
            assert node.label is not None
            assert node.status is not None
            assert node.file_path is not None

    def test_edge_structure(self) -> None:
        """Each edge should have required fields."""
        graph = build_artifact_graph()
        for edge in graph.edges:
            assert edge.source is not None
            assert edge.target is not None
            assert edge.relationship is not None

    def test_graph_relationships_exist(self) -> None:
        """Graph should have some relationships (edges)."""
        graph = build_artifact_graph()
        # We have ADR-0043 -> SPEC-0040, so should have at least 1 edge
        assert len(graph.edges) > 0


# =============================================================================
# Workflow Mode Tests (M10)
# =============================================================================


class TestWorkflowModes:
    """Tests for workflow mode functions."""

    def test_create_workflow_manual(self) -> None:
        """Test creating a manual workflow."""
        from gateway.services.workflow_service import create_workflow
        from shared.contracts.devtools.workflow import (
            WorkflowMode,
            WorkflowScenario,
            WorkflowStage,
        )

        workflow = create_workflow(
            mode=WorkflowMode.MANUAL,
            scenario=WorkflowScenario.NEW_FEATURE,
            title="Test Feature",
        )

        assert workflow.mode == WorkflowMode.MANUAL
        assert workflow.scenario == WorkflowScenario.NEW_FEATURE
        assert workflow.current_stage == WorkflowStage.DISCUSSION
        assert workflow.title == "Test Feature"
        assert workflow.id.startswith("WF-")

    def test_create_workflow_ai_lite(self) -> None:
        """Test creating an AI-Lite workflow."""
        from gateway.services.workflow_service import create_workflow
        from shared.contracts.devtools.workflow import (
            WorkflowMode,
            WorkflowScenario,
            WorkflowStage,
        )

        workflow = create_workflow(
            mode=WorkflowMode.AI_LITE,
            scenario=WorkflowScenario.BUG_FIX,
            title="Bug Fix Test",
        )

        assert workflow.mode == WorkflowMode.AI_LITE
        assert workflow.current_stage == WorkflowStage.PLAN  # Bug fix starts at plan

    def test_create_workflow_enhancement_starts_at_spec(self) -> None:
        """Test that enhancement scenario starts at SPEC stage."""
        from gateway.services.workflow_service import create_workflow
        from shared.contracts.devtools.workflow import (
            WorkflowMode,
            WorkflowScenario,
            WorkflowStage,
        )

        workflow = create_workflow(
            mode=WorkflowMode.MANUAL,
            scenario=WorkflowScenario.ENHANCEMENT,
            title="Enhancement Test",
        )

        assert workflow.current_stage == WorkflowStage.SPEC

    def test_get_workflow_status(self) -> None:
        """Test getting workflow status."""
        from gateway.services.workflow_service import (
            create_workflow,
            get_workflow_status,
        )
        from shared.contracts.devtools.workflow import (
            WorkflowMode,
            WorkflowScenario,
        )

        workflow = create_workflow(
            mode=WorkflowMode.MANUAL,
            scenario=WorkflowScenario.NEW_FEATURE,
            title="Status Test",
        )

        status = get_workflow_status(workflow.id)
        assert status is not None
        assert status.id == workflow.id

    def test_get_workflow_status_not_found(self) -> None:
        """Test getting non-existent workflow returns None."""
        from gateway.services.workflow_service import get_workflow_status

        status = get_workflow_status("WF-999999")
        assert status is None

    def test_advance_workflow(self) -> None:
        """Test advancing workflow to next stage."""
        from gateway.services.workflow_service import (
            advance_workflow,
            create_workflow,
            get_workflow_status,
        )
        from shared.contracts.devtools.workflow import (
            WorkflowMode,
            WorkflowScenario,
            WorkflowStage,
        )

        workflow = create_workflow(
            mode=WorkflowMode.MANUAL,
            scenario=WorkflowScenario.NEW_FEATURE,
            title="Advance Test",
        )

        # Should start at DISCUSSION
        assert workflow.current_stage == WorkflowStage.DISCUSSION

        # Advance to ADR
        new_stage = advance_workflow(workflow.id)
        assert new_stage == WorkflowStage.ADR

        # Verify state persisted
        status = get_workflow_status(workflow.id)
        assert status.current_stage == WorkflowStage.ADR

    def test_generate_prompt(self) -> None:
        """Test generating AI-Lite prompt."""
        from gateway.services.workflow_service import generate_prompt
        from shared.contracts.devtools.workflow import ArtifactType

        # Use existing artifact DISC-001
        response = generate_prompt(
            artifact_id="DISC-001",
            target_type=ArtifactType.ADR,
        )

        assert response.target_type == ArtifactType.ADR
        assert "DISC-001" in response.prompt
        assert response.context.get("source_id") == "DISC-001"

    def test_generate_prompt_artifact_not_found(self) -> None:
        """Test prompt generation with non-existent artifact."""
        from gateway.services.workflow_service import generate_prompt
        from shared.contracts.devtools.workflow import ArtifactType

        response = generate_prompt(
            artifact_id="NONEXISTENT-999",
            target_type=ArtifactType.ADR,
        )

        # Should return fallback prompt
        assert "error" in response.context


# =============================================================================
# AI-Full Mode Tests (M12)
# =============================================================================


class TestAIFullMode:
    """Tests for AI-Full mode generation functions."""

    def test_generate_artifact_content(self) -> None:
        """Test generating artifact content."""
        from gateway.services.workflow_service import generate_artifact_content
        from shared.contracts.devtools.workflow import ArtifactType

        content = generate_artifact_content(
            artifact_type=ArtifactType.DISCUSSION,
            title="Test Feature",
            description="A test feature description",
            use_llm=False,  # Test template fallback
        )

        assert content["title"] == "Test Feature"
        assert content["status"] == "draft"
        assert "Test Feature" in content["content"]

    def test_generate_artifact_content_adr(self) -> None:
        """Test generating ADR content."""
        from gateway.services.workflow_service import generate_artifact_content
        from shared.contracts.devtools.workflow import ArtifactType

        content = generate_artifact_content(
            artifact_type=ArtifactType.ADR,
            title="Architecture Decision",
            description="An important decision",
            use_llm=False,  # Test template fallback
        )

        assert content["title"] == "Architecture Decision"
        assert content["status"] == "draft"
        assert "workflow" in content["context"].lower()

    def test_generate_full_workflow_requires_ai_full_mode(self) -> None:
        """Test that full generation requires AI-Full mode."""
        from gateway.services.workflow_service import (
            create_workflow,
            generate_full_workflow,
        )
        from shared.contracts.devtools.workflow import (
            GenerationStatus,
            WorkflowMode,
            WorkflowScenario,
        )

        # Create a manual workflow (not AI-Full)
        workflow = create_workflow(
            mode=WorkflowMode.MANUAL,
            scenario=WorkflowScenario.NEW_FEATURE,
            title="Manual Workflow",
        )

        # Try to generate - should fail
        response = generate_full_workflow(
            workflow_id=workflow.id,
            title="Test",
            description="Test",
        )

        assert response.status == GenerationStatus.FAILED
        assert len(response.errors) > 0
        assert "AI-Full" in response.errors[0]

    def test_generate_full_workflow_ai_full(self) -> None:
        """Test full generation in AI-Full mode."""
        from gateway.services.workflow_service import (
            create_workflow,
            generate_full_workflow,
        )
        from shared.contracts.devtools.workflow import (
            GenerationStatus,
            WorkflowMode,
            WorkflowScenario,
        )

        # Create AI-Full workflow
        workflow = create_workflow(
            mode=WorkflowMode.AI_FULL,
            scenario=WorkflowScenario.NEW_FEATURE,
            title="AI Full Workflow",
        )

        # Generate full workflow
        response = generate_full_workflow(
            workflow_id=workflow.id,
            title="Generated Feature",
            description="Auto-generated",
        )

        assert response.status == GenerationStatus.COMPLETED
        assert len(response.artifacts) == 4  # DISC, ADR, SPEC, PLAN
        assert len(response.errors) == 0

    def test_generation_request_response_models(self) -> None:
        """Test that generation models are importable."""
        from shared.contracts.devtools.workflow import (
            GenerationRequest,
            GenerationResponse,
            GenerationStatus,
        )

        request = GenerationRequest(
            workflow_id="WF-001",
            target_types=[],
            context={"title": "Test"},
        )
        assert request.workflow_id == "WF-001"

        response = GenerationResponse(
            artifacts=[],
            status=GenerationStatus.COMPLETED,
            errors=[],
        )
        assert response.status == GenerationStatus.COMPLETED


class TestRichPromptGeneration:
    """Tests for AI-Lite rich prompt generation (DISC-002)."""

    def test_generate_prompt_adr_to_spec(self) -> None:
        """Generate prompt for ADR -> SPEC transition."""
        from gateway.services.workflow_service import generate_prompt

        # Find an ADR to use
        adrs = scan_artifacts(artifact_type=ArtifactType.ADR)
        if not adrs:
            pytest.skip("No ADRs found in repository")

        adr = adrs[0]
        response = generate_prompt(
            artifact_id=adr.id,
            target_type=ArtifactType.SPEC,
        )

        assert response.target_type == ArtifactType.SPEC
        assert response.context["source_type"] == "adr"
        assert "SPEC" in response.prompt
        assert len(response.prompt) > 100  # Should be a rich prompt

    def test_generate_prompt_spec_to_plan(self) -> None:
        """Generate prompt for SPEC -> Plan transition."""
        from gateway.services.workflow_service import generate_prompt

        # Find a SPEC to use
        specs = scan_artifacts(artifact_type=ArtifactType.SPEC)
        if not specs:
            pytest.skip("No SPECs found in repository")

        spec = specs[0]
        response = generate_prompt(
            artifact_id=spec.id,
            target_type=ArtifactType.PLAN,
        )

        assert response.target_type == ArtifactType.PLAN
        assert response.context["source_type"] == "spec"
        assert "Plan" in response.prompt or "PLAN" in response.prompt

    def test_generate_prompt_discussion_to_adr(self) -> None:
        """Generate prompt for Discussion -> ADR transition."""
        from gateway.services.workflow_service import generate_prompt

        # Find a Discussion to use
        discussions = scan_artifacts(artifact_type=ArtifactType.DISCUSSION)
        if not discussions:
            pytest.skip("No Discussions found in repository")

        disc = discussions[0]
        response = generate_prompt(
            artifact_id=disc.id,
            target_type=ArtifactType.ADR,
        )

        assert response.target_type == ArtifactType.ADR
        assert response.context["source_type"] == "discussion"
        assert "ADR" in response.prompt

    def test_generate_prompt_spec_to_contract(self) -> None:
        """Generate prompt for SPEC -> Contract transition."""
        from gateway.services.workflow_service import generate_prompt

        # Find a SPEC to use
        specs = scan_artifacts(artifact_type=ArtifactType.SPEC)
        if not specs:
            pytest.skip("No SPECs found in repository")

        spec = specs[0]
        response = generate_prompt(
            artifact_id=spec.id,
            target_type=ArtifactType.CONTRACT,
        )

        assert response.target_type == ArtifactType.CONTRACT
        assert "Pydantic" in response.prompt or "contract" in response.prompt.lower()

    def test_generate_prompt_nonexistent_artifact(self) -> None:
        """Generate prompt for non-existent artifact returns fallback."""
        from gateway.services.workflow_service import generate_prompt

        response = generate_prompt(
            artifact_id="NONEXISTENT-999",
            target_type=ArtifactType.ADR,
        )

        assert "error" in response.context
        assert response.target_type == ArtifactType.ADR

    def test_prompt_contains_schema(self) -> None:
        """Rich prompts should contain target schema information."""
        from gateway.services.workflow_service import generate_prompt

        adrs = scan_artifacts(artifact_type=ArtifactType.ADR)
        if not adrs:
            pytest.skip("No ADRs found")

        response = generate_prompt(
            artifact_id=adrs[0].id,
            target_type=ArtifactType.SPEC,
        )

        # Rich prompts should include schema hints
        assert "schema" in response.prompt.lower() or "json" in response.prompt.lower()

    def test_prompt_version_in_context(self) -> None:
        """Rich prompts should include version in context."""
        from gateway.services.workflow_service import generate_prompt

        adrs = scan_artifacts(artifact_type=ArtifactType.ADR)
        if not adrs:
            pytest.skip("No ADRs found")

        response = generate_prompt(
            artifact_id=adrs[0].id,
            target_type=ArtifactType.SPEC,
        )

        # Should have prompt_version for rich prompts
        assert response.context.get("prompt_version") == "2.0"


class TestDiscussionSchema:
    """Tests for Discussion Pydantic schema (DISC-002)."""

    def test_discussion_schema_import(self) -> None:
        """Discussion schema should be importable."""
        from shared.contracts.devtools.discussion import (
            DiscussionStatus,
        )

        # Verify imports work
        assert DiscussionStatus.ACTIVE.value == "active"
        assert DiscussionStatus.DRAFT.value == "draft"

    def test_discussion_schema_creation(self) -> None:
        """Create a valid Discussion schema."""
        from shared.contracts.devtools.discussion import (
            DiscussionSchema,
            DiscussionStatus,
        )

        disc = DiscussionSchema(
            id="DISC-001",
            title="Test Discussion",
            status=DiscussionStatus.DRAFT,
            created_date="2025-12-30",
            updated_date="2025-12-30",
            author="Test User",
            summary="This is a test discussion about a feature.",
        )

        assert disc.id == "DISC-001"
        assert disc.status == DiscussionStatus.DRAFT
        assert disc.schema_type == "discussion"

    def test_discussion_schema_with_requirements(self) -> None:
        """Create Discussion with requirements."""
        from shared.contracts.devtools.discussion import (
            DiscussionRequirements,
            DiscussionSchema,
            DiscussionStatus,
            FunctionalRequirement,
            NonFunctionalRequirement,
        )

        reqs = DiscussionRequirements(
            functional=[
                FunctionalRequirement(id="FR-1", description="User can login"),
                FunctionalRequirement(id="FR-2", description="User can logout"),
            ],
            non_functional=[
                NonFunctionalRequirement(id="NFR-1", description="Response time < 200ms"),
            ],
        )

        disc = DiscussionSchema(
            id="DISC-002",
            title="Auth Discussion",
            status=DiscussionStatus.ACTIVE,
            created_date="2025-12-30",
            updated_date="2025-12-30",
            author="Test User",
            summary="Discussion about authentication.",
            requirements=reqs,
        )

        assert len(disc.requirements.functional) == 2
        assert len(disc.requirements.non_functional) == 1

    def test_discussion_summary_for_prompt(self) -> None:
        """Test DiscussionSummaryForPrompt extraction."""
        from shared.contracts.devtools.discussion import (
            DiscussionRequirements,
            DiscussionSchema,
            DiscussionStatus,
            DiscussionSummaryForPrompt,
            FunctionalRequirement,
            OpenQuestion,
            QuestionStatus,
        )

        disc = DiscussionSchema(
            id="DISC-003",
            title="Feature X",
            status=DiscussionStatus.ACTIVE,
            created_date="2025-12-30",
            updated_date="2025-12-30",
            author="User",
            summary="Discussing Feature X implementation.",
            requirements=DiscussionRequirements(
                functional=[FunctionalRequirement(id="FR-1", description="Do X")],
            ),
            open_questions=[
                OpenQuestion(id="Q-1", question="How to handle Y?", status=QuestionStatus.OPEN),
            ],
        )

        summary = DiscussionSummaryForPrompt.from_discussion(disc)

        assert summary.id == "DISC-003"
        assert summary.title == "Feature X"
        assert len(summary.functional_requirements) == 1
        assert len(summary.open_questions) == 1
        assert "FR-1" in summary.functional_requirements[0]

    def test_discussion_id_validation(self) -> None:
        """Discussion ID must start with DISC-."""
        import pydantic

        from shared.contracts.devtools.discussion import DiscussionSchema, DiscussionStatus

        with pytest.raises(pydantic.ValidationError):
            DiscussionSchema(
                id="INVALID-001",  # Should fail
                title="Test",
                status=DiscussionStatus.DRAFT,
                created_date="2025-12-30",
                updated_date="2025-12-30",
                author="User",
                summary="Test summary.",
            )
