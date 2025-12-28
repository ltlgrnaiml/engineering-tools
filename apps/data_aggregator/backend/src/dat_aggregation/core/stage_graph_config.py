"""Configurable stage graph for DAT pipeline.

Per ADR-0001-DAT: Stage graph should be configurable for extensibility.

This module provides a StageGraphConfig that allows customization of:
- Stage ordering
- Forward gating rules
- Cascade unlock rules
- Optional stages
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__version__ = "0.1.0"


@dataclass
class StageDefinition:
    """Definition of a single stage in the graph."""
    name: str
    label: str
    description: str = ""
    is_optional: bool = False
    cascades_on_unlock: bool = True


@dataclass
class GatingRule:
    """Forward gating rule for a stage."""
    required_stage: str
    must_be_completed: bool = False


@dataclass
class StageGraphConfig:
    """Configurable stage graph for DAT pipeline.

    Per ADR-0001-DAT: Allows customization of the pipeline structure.

    Example:
        >>> config = StageGraphConfig.default()
        >>> config.add_stage(StageDefinition("custom", "Custom Stage"))
        >>> config.add_gate("custom", GatingRule("parse", must_be_completed=True))
    """

    stages: list[StageDefinition] = field(default_factory=list)
    forward_gates: dict[str, list[GatingRule]] = field(default_factory=dict)
    cascade_targets: dict[str, list[str]] = field(default_factory=dict)

    def add_stage(
        self,
        stage: StageDefinition,
        after: str | None = None,
    ) -> "StageGraphConfig":
        """Add a stage to the graph.

        Args:
            stage: Stage definition to add.
            after: Insert after this stage (None = append to end).

        Returns:
            Self for chaining.
        """
        if after is None:
            self.stages.append(stage)
        else:
            idx = self._find_stage_index(after)
            if idx is not None:
                self.stages.insert(idx + 1, stage)
            else:
                self.stages.append(stage)
        return self

    def add_gate(
        self,
        stage_name: str,
        rule: GatingRule,
    ) -> "StageGraphConfig":
        """Add a forward gating rule.

        Args:
            stage_name: Stage that the rule applies to.
            rule: Gating rule to add.

        Returns:
            Self for chaining.
        """
        if stage_name not in self.forward_gates:
            self.forward_gates[stage_name] = []
        self.forward_gates[stage_name].append(rule)
        return self

    def set_cascade_targets(
        self,
        stage_name: str,
        targets: list[str],
    ) -> "StageGraphConfig":
        """Set cascade unlock targets for a stage.

        Args:
            stage_name: Stage that triggers the cascade.
            targets: List of stages to unlock when this stage unlocks.

        Returns:
            Self for chaining.
        """
        self.cascade_targets[stage_name] = targets
        return self

    def get_stage(self, name: str) -> StageDefinition | None:
        """Get a stage definition by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def get_stage_order(self) -> list[str]:
        """Get ordered list of stage names."""
        return [s.name for s in self.stages]

    def get_optional_stages(self) -> list[str]:
        """Get list of optional stage names."""
        return [s.name for s in self.stages if s.is_optional]

    def get_gates(self, stage_name: str) -> list[GatingRule]:
        """Get gating rules for a stage."""
        return self.forward_gates.get(stage_name, [])

    def get_cascade_targets(self, stage_name: str) -> list[str]:
        """Get cascade unlock targets for a stage."""
        return self.cascade_targets.get(stage_name, [])

    def _find_stage_index(self, name: str) -> int | None:
        """Find index of a stage by name."""
        for i, stage in enumerate(self.stages):
            if stage.name == name:
                return i
        return None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the stage graph configuration.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
        errors: list[str] = []
        stage_names = {s.name for s in self.stages}

        # Check gating rules reference valid stages
        for stage_name, rules in self.forward_gates.items():
            if stage_name not in stage_names:
                errors.append(f"Gate references unknown stage: {stage_name}")
            for rule in rules:
                if rule.required_stage not in stage_names:
                    errors.append(
                        f"Gate for '{stage_name}' references unknown stage: "
                        f"{rule.required_stage}"
                    )

        # Check cascade targets reference valid stages
        for stage_name, targets in self.cascade_targets.items():
            if stage_name not in stage_names:
                errors.append(f"Cascade references unknown stage: {stage_name}")
            for target in targets:
                if target not in stage_names:
                    errors.append(
                        f"Cascade for '{stage_name}' references unknown stage: {target}"
                    )

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "stages": [
                {
                    "name": s.name,
                    "label": s.label,
                    "description": s.description,
                    "is_optional": s.is_optional,
                    "cascades_on_unlock": s.cascades_on_unlock,
                }
                for s in self.stages
            ],
            "forward_gates": {
                stage: [
                    {"required_stage": r.required_stage, "must_be_completed": r.must_be_completed}
                    for r in rules
                ]
                for stage, rules in self.forward_gates.items()
            },
            "cascade_targets": self.cascade_targets,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageGraphConfig":
        """Deserialize from dictionary."""
        config = cls()

        for stage_data in data.get("stages", []):
            config.add_stage(StageDefinition(
                name=stage_data["name"],
                label=stage_data["label"],
                description=stage_data.get("description", ""),
                is_optional=stage_data.get("is_optional", False),
                cascades_on_unlock=stage_data.get("cascades_on_unlock", True),
            ))

        for stage_name, rules in data.get("forward_gates", {}).items():
            for rule in rules:
                config.add_gate(stage_name, GatingRule(
                    required_stage=rule["required_stage"],
                    must_be_completed=rule.get("must_be_completed", False),
                ))

        for stage_name, targets in data.get("cascade_targets", {}).items():
            config.set_cascade_targets(stage_name, targets)

        return config

    @classmethod
    def default(cls) -> "StageGraphConfig":
        """Create default DAT stage graph configuration.

        Per ADR-0001-DAT: 8-stage pipeline.
        """
        config = cls()

        # Define stages
        config.add_stage(StageDefinition("discovery", "Discovery", "Scan for files"))
        config.add_stage(StageDefinition("selection", "Selection", "Select files"))
        config.add_stage(StageDefinition("context", "Context", "Configure context", is_optional=True))
        config.add_stage(StageDefinition("table_availability", "Table Availability", "Probe tables"))
        config.add_stage(StageDefinition("table_selection", "Table Selection", "Select tables"))
        config.add_stage(StageDefinition("preview", "Preview", "Preview data", is_optional=True))
        config.add_stage(StageDefinition("parse", "Parse", "Extract data"))
        config.add_stage(StageDefinition("export", "Export", "Export dataset"))

        # Define forward gates
        config.add_gate("selection", GatingRule("discovery"))
        config.add_gate("context", GatingRule("selection"))
        config.add_gate("table_availability", GatingRule("selection"))
        config.add_gate("table_selection", GatingRule("table_availability"))
        config.add_gate("preview", GatingRule("table_selection"))
        config.add_gate("parse", GatingRule("table_selection"))
        config.add_gate("export", GatingRule("parse", must_be_completed=True))

        # Define cascade targets
        config.set_cascade_targets("discovery", [
            "selection", "context", "table_availability",
            "table_selection", "preview", "parse", "export"
        ])
        config.set_cascade_targets("selection", [
            "context", "table_availability", "table_selection",
            "preview", "parse", "export"
        ])
        config.set_cascade_targets("table_availability", [
            "table_selection", "preview", "parse", "export"
        ])
        config.set_cascade_targets("table_selection", ["preview", "parse", "export"])
        config.set_cascade_targets("parse", ["export"])
        # Context and Preview do NOT cascade (per ADR-0003)
        config.set_cascade_targets("context", [])
        config.set_cascade_targets("preview", [])

        return config


# Singleton default config
_default_config: StageGraphConfig | None = None


def get_default_stage_graph() -> StageGraphConfig:
    """Get the default stage graph configuration."""
    global _default_config
    if _default_config is None:
        _default_config = StageGraphConfig.default()
    return _default_config


def set_stage_graph_config(config: StageGraphConfig) -> None:
    """Set a custom stage graph configuration."""
    global _default_config
    _default_config = config
