"""Plan Builder Service.

Builds frozen plan artifacts:
1. Lookup JSON - TOM-style data source configuration
2. Request Graph - Deduped partitions for data loading
3. Plan Manifest - SHA1 hashes for determinism
"""

import logging
from pathlib import Path
from uuid import UUID

from apps.pptx_generator.backend.models.drm import DerivedRequirementsManifest
from apps.pptx_generator.backend.models.environment_profile import EnvironmentProfile
from apps.pptx_generator.backend.models.mapping_manifest import MappingManifest
from apps.pptx_generator.backend.models.plan_artifacts import (
    LookupJSON,
    PlanArtifacts,
    PlanManifest,
    RequestGraph,
    RequestGraphPartition,
)

logger = logging.getLogger(__name__)


class PlanBuilderService:
    """Service for building frozen plan artifacts."""

    CODE_VERSION = "2.0.0"  # TOM v2 version

    def build_plan(
        self,
        drm: DerivedRequirementsManifest,
        mappings: MappingManifest,
        env_profile: EnvironmentProfile,
        project_id: UUID,
    ) -> PlanArtifacts:
        """Build complete plan artifacts.

        Args:
            drm: Derived requirements manifest.
            mappings: Mapping manifest.
            env_profile: Environment profile.
            project_id: Project ID.

        Returns:
            PlanArtifacts with all components.
        """
        logger.info(f"Building plan for project {project_id}")

        # Build lookup JSON
        lookup = self._build_lookup_json(env_profile)
        logger.info("Lookup JSON built")

        # Build request graph
        request_graph = self._build_request_graph(drm, mappings, env_profile)
        logger.info(f"Request graph built: {request_graph.total_partitions} partitions")

        # Generate manifest with hashes
        manifest = self._generate_manifest(drm, mappings, env_profile, lookup, request_graph)
        logger.info("Plan manifest generated with SHA1 hashes")

        # Create plan artifacts
        artifacts = PlanArtifacts(
            project_id=project_id,
            lookup=lookup,
            request_graph=request_graph,
            manifest=manifest,
        )

        logger.info("Plan artifacts complete")
        return artifacts

    def _build_lookup_json(self, env_profile: EnvironmentProfile) -> LookupJSON:
        """Build lookup JSON from environment profile.

        Args:
            env_profile: Environment profile.

        Returns:
            LookupJSON with TOM structure.
        """
        # Build job context folders using primary job context
        job_context_folders = {}
        primary_job_context = env_profile.get_primary_context()
        if primary_job_context:
            for value in primary_job_context.values:
                # Construct folder path for each job context value
                folder_path = str(
                    Path(env_profile.roots.output_root)
                    / env_profile.roots.dataagg_rel.format(run_key="{run_key}", category=value)
                )
                job_context_folders[value] = folder_path

        lookup = LookupJSON(
            fs_root=env_profile.roots.templates_root,
            fs_dataagg=env_profile.roots.output_root,
            job_context_folders=job_context_folders,
        )

        return lookup

    def _build_request_graph(
        self,
        _drm: DerivedRequirementsManifest,
        _mappings: MappingManifest,
        env_profile: EnvironmentProfile,
    ) -> RequestGraph:
        """Build request graph with deduped partitions.

        Args:
            drm: Derived requirements manifest.
            mappings: Mapping manifest.
            env_profile: Environment profile.

        Returns:
            RequestGraph with sorted, deduped partitions.
        """
        graph = RequestGraph()

        # For now, create placeholder partitions
        # In full implementation, this would scan data sources
        # and create partitions for each (run_key, job_context_value) combination

        # Example: Create partitions for each job context value
        primary_job_context = env_profile.get_primary_context()
        if primary_job_context:
            for job_context_value in primary_job_context.values:
                # Placeholder partition
                partition = RequestGraphPartition(
                    run_key="placeholder_run",
                    job_context_value=job_context_value,
                    file_paths=[],
                    deduped=False,
                )
                graph.add_partition(partition)

        # Deduplicate and sort for determinism
        graph.deduplicate()
        graph.sort_stable()

        return graph

    def _generate_manifest(
        self,
        drm: DerivedRequirementsManifest,
        mappings: MappingManifest,
        env_profile: EnvironmentProfile,
        lookup: LookupJSON,
        request_graph: RequestGraph,
    ) -> PlanManifest:
        """Generate plan manifest with SHA1 hashes.

        Args:
            drm: Derived requirements manifest.
            mappings: Mapping manifest.
            env_profile: Environment profile.
            lookup: Lookup JSON.
            request_graph: Request graph.

        Returns:
            PlanManifest with deterministic hashes.
        """
        manifest = PlanManifest(
            drm_sha1=PlanManifest.calculate_sha1(drm),
            mappings_sha1=PlanManifest.calculate_sha1(mappings),
            environment_sha1=PlanManifest.calculate_sha1(env_profile),
            lookup_sha1=PlanManifest.calculate_sha1(lookup),
            request_graph_sha1=PlanManifest.calculate_sha1(request_graph),
            code_version=self.CODE_VERSION,
        )

        return manifest


# Validation test
if __name__ == "__main__":
    from uuid import uuid4

    from apps.pptx_generator.backend.models.drm import (
        AggregationType,
        RequiredContext,
        RequiredMetric,
    )
    from apps.pptx_generator.backend.models.environment_profile import DataRoots, JobContext
    from apps.pptx_generator.backend.models.mapping_manifest import (
        ContextMapping,
        MappingSourceType,
        MetricMapping,
    )

    # Create test data
    drm = DerivedRequirementsManifest(
        template_id=uuid4(),
        required_contexts=[RequiredContext(name="side")],
        required_metrics=[RequiredMetric(name="CD", aggregation_type=AggregationType.MEAN)],
    )

    mappings = MappingManifest(
        project_id=uuid4(),
        context_mappings=[
            ContextMapping(
                context_name="side",
                source_type=MappingSourceType.COLUMN,
                source_column="SpaceCD_Side",
            )
        ],
        metrics_mappings=[
            MetricMapping(
                metric_name="CD",
                source_column="Space CD (nm)",
                aggregation_semantics=AggregationType.MEAN,
            )
        ],
    )

    from apps.pptx_generator.backend.models.environment_profile import SourceType

    env_profile = EnvironmentProfile(
        project_id=uuid4(),
        name="Test Profile",
        source=SourceType.FILESYSTEM,
        roots=DataRoots(
            templates_root="/templates",
            output_root="/output",
        ),
        job_context=JobContext(
            name="Sides",
            key="sides",
            values=["Left", "Right"],
        ),
    )

    # Build plan
    builder = PlanBuilderService()
    project_id = uuid4()
    artifacts = builder.build_plan(drm, mappings, env_profile, project_id)

    print("\nPlan Artifacts:")
    print(f"  Project ID: {artifacts.project_id}")
    print(f"  Lookup folders: {len(artifacts.lookup.job_context_folders)}")
    print(f"  Request graph partitions: {artifacts.request_graph.total_partitions}")
    print(f"  Manifest DRM SHA1: {artifacts.manifest.drm_sha1[:16]}...")
    print(f"  Code version: {artifacts.manifest.code_version}")

    # Test determinism - same inputs should produce same hashes
    artifacts2 = builder.build_plan(drm, mappings, env_profile, project_id)
    assert artifacts.manifest.drm_sha1 == artifacts2.manifest.drm_sha1
    assert artifacts.manifest.mappings_sha1 == artifacts2.manifest.mappings_sha1

    print("\nAll plan builder tests passed!")
