"""Stage graph configuration contract.

Per ADR-0004: 8-stage pipeline with lockable artifacts.
Per SPEC-0024: Dependencies and cascade targets defined.
"""


from pydantic import BaseModel

from .stage import DATStageType

__version__ = "1.0.0"


class StageDefinition(BaseModel):
    """Definition of a single stage in the pipeline."""

    stage_type: DATStageType
    is_optional: bool = False
    description: str = ""


class GatingRule(BaseModel):
    """Forward gating rule for stage progression."""

    target_stage: DATStageType
    required_stages: list[DATStageType]
    require_completion: bool = False


class CascadeRule(BaseModel):
    """Cascade unlock rule when a stage is unlocked."""

    trigger_stage: DATStageType
    cascade_targets: list[DATStageType]


class StageGraphConfig(BaseModel):
    """Complete stage graph configuration.

    Single source of truth for DAT pipeline structure.
    Per ADR-0004 and SPEC-0024.
    """

    stages: list[StageDefinition]
    gating_rules: list[GatingRule]
    cascade_rules: list[CascadeRule]
    optional_stages: frozenset[DATStageType] = frozenset({
        DATStageType.CONTEXT,
        DATStageType.PREVIEW,
    })

    @classmethod
    def default(cls) -> "StageGraphConfig":
        """Return the default DAT 8-stage pipeline configuration.

        Returns:
            StageGraphConfig: Default configuration per ADR-0004.
        """
        return cls(
            stages=[
                StageDefinition(
                    stage_type=DATStageType.DISCOVERY,
                    description="Scan filesystem for data files",
                ),
                StageDefinition(
                    stage_type=DATStageType.SELECTION,
                    description="Select files to process",
                ),
                StageDefinition(
                    stage_type=DATStageType.CONTEXT,
                    is_optional=True,
                    description="Set profile and aggregation context",
                ),
                StageDefinition(
                    stage_type=DATStageType.TABLE_AVAILABILITY,
                    description="Detect available tables in selected files",
                ),
                StageDefinition(
                    stage_type=DATStageType.TABLE_SELECTION,
                    description="Select tables to extract",
                ),
                StageDefinition(
                    stage_type=DATStageType.PREVIEW,
                    is_optional=True,
                    description="Preview data before parsing",
                ),
                StageDefinition(
                    stage_type=DATStageType.PARSE,
                    description="Extract and transform data",
                ),
                StageDefinition(
                    stage_type=DATStageType.EXPORT,
                    description="Export data as DataSet",
                ),
            ],
            gating_rules=[
                GatingRule(
                    target_stage=DATStageType.SELECTION,
                    required_stages=[DATStageType.DISCOVERY],
                ),
                GatingRule(
                    target_stage=DATStageType.CONTEXT,
                    required_stages=[DATStageType.SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.TABLE_AVAILABILITY,
                    required_stages=[DATStageType.SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.TABLE_SELECTION,
                    required_stages=[DATStageType.TABLE_AVAILABILITY],
                ),
                GatingRule(
                    target_stage=DATStageType.PREVIEW,
                    required_stages=[DATStageType.TABLE_SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.PARSE,
                    required_stages=[DATStageType.TABLE_SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.EXPORT,
                    required_stages=[DATStageType.PARSE],
                    require_completion=True,
                ),
            ],
            cascade_rules=[
                CascadeRule(
                    trigger_stage=DATStageType.DISCOVERY,
                    cascade_targets=[
                        DATStageType.SELECTION,
                        DATStageType.CONTEXT,
                        DATStageType.TABLE_AVAILABILITY,
                        DATStageType.TABLE_SELECTION,
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.SELECTION,
                    cascade_targets=[
                        DATStageType.CONTEXT,
                        DATStageType.TABLE_AVAILABILITY,
                        DATStageType.TABLE_SELECTION,
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.TABLE_AVAILABILITY,
                    cascade_targets=[
                        DATStageType.TABLE_SELECTION,
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.TABLE_SELECTION,
                    cascade_targets=[
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.PARSE,
                    cascade_targets=[DATStageType.EXPORT],
                ),
                # Context and Preview do NOT cascade (per ADR-0004)
                CascadeRule(
                    trigger_stage=DATStageType.CONTEXT,
                    cascade_targets=[],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.PREVIEW,
                    cascade_targets=[],
                ),
            ],
        )

    class Config:
        """Pydantic config."""

        frozen = True
