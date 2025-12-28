"""Environment Profile models.

Models for configuring data source environments and job context taxonomy.
"""

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    """Data source type."""

    FILESYSTEM = "filesystem"
    ADLS = "adls"
    SQL = "sql"


class JobContext(BaseModel):
    """Job context dimension configuration.

    Replaces hardcoded 'sides' with flexible dimension.

    Attributes:
        name: Display name (e.g., 'Sides', 'Wafer', 'CD Target').
        key: Stable machine key (e.g., 'sides', 'wafer').
        values: List of valid values (e.g., ['Left', 'Right']).
        aliases: Mapping of aliases to canonical values.
    """

    name: str = Field(..., description="Display name for UI")
    key: str = Field(..., description="Stable machine key")
    values: list[str] = Field(..., description="Valid values")
    aliases: dict[str, str] = Field(default_factory=dict, description="Aliases to canonical values")

    def resolve_value(self, value: str) -> str | None:
        """Resolve a value through aliases.

        Args:
            value: Value to resolve.

        Returns:
            Canonical value if found, None otherwise.
        """
        # Check if already canonical
        if value in self.values:
            return value
        # Check aliases
        return self.aliases.get(value)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Sides",
            "key": "sides",
            "values": ["Left", "Right"],
            "aliases": {"l": "Left", "left": "Left", "r": "Right", "right": "Right"},
        }
    })


class DataRoots(BaseModel):
    """Data root paths configuration.

    Attributes:
        templates_root: Root directory for templates.
        output_root: Root directory for outputs.
        dataagg_rel: Relative path pattern for data aggregation.
    """

    templates_root: str = Field(..., description="Templates root path")
    output_root: str = Field(..., description="Output root path")
    dataagg_rel: str = Field(
        default="{run_key}/DataAgg/{category}",
        description="Relative data aggregation path pattern",
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "templates_root": "C:/Users/user/templates",
            "output_root": "C:/Users/user/output",
            "dataagg_rel": "{run_key}/DataAgg/{category}",
        }
    })


class EnvironmentProfile(BaseModel):
    """Complete environment profile configuration.

    Attributes:
        id: Unique identifier.
        project_id: Associated project ID.
        name: Profile name.
        source: Data source type.
        roots: Data root paths.
        job_contexts: Job context dimensions configuration.
        primary_job_context_key: Key of the primary job context.
        encoding_policy: List of encodings to try.
    """

    id: UUID = Field(default_factory=uuid4, description="Profile ID")
    project_id: UUID | None = Field(None, description="Associated project ID")
    name: str = Field(..., description="Profile name")
    source: SourceType = Field(..., description="Data source type")
    roots: DataRoots = Field(..., description="Data root paths")
    job_contexts: list[JobContext] = Field(
        default_factory=list, description="Job context dimensions"
    )
    primary_job_context_key: str = Field(
        default="side", description="Key of primary job context"
    )
    encoding_policy: list[str] = Field(
        default_factory=lambda: ["utf-8", "utf-8-sig", "cp1252"],
        description="Encoding policy",
    )

    def get_primary_context(self) -> JobContext | None:
        """Get the primary job context.

        Returns:
            Primary JobContext if found, None otherwise.
        """
        for ctx in self.job_contexts:
            if ctx.key == self.primary_job_context_key:
                return ctx
        return None

    def get_context_by_key(self, key: str) -> JobContext | None:
        """Get a specific context by key.

        Args:
            key: Job context key.

        Returns:
            JobContext if found, None otherwise.
        """
        for ctx in self.job_contexts:
            if ctx.key == key:
                return ctx
        return None

    @classmethod
    def create_preset(
        cls, preset_name: str, project_id: UUID | None = None
    ) -> "EnvironmentProfile":
        """Create a preset environment profile.

        Args:
            preset_name: Name of preset ('local_filesystem', 'azure_adls', 'sql_server').
            project_id: Optional project ID to associate.

        Returns:
            EnvironmentProfile with preset configuration.

        Raises:
            ValueError: If preset_name is unknown.
        """
        if preset_name == "local_filesystem":
            return cls(
                project_id=project_id,
                name="Local Filesystem",
                source=SourceType.FILESYSTEM,
                roots=DataRoots(
                    templates_root="C:/Users/user/templates",
                    output_root="C:/Users/user/output",
                ),
                job_contexts=[
                    JobContext(
                        name="Sides",
                        key="side",
                        values=["Left", "Right"],
                        aliases={"l": "Left", "left": "Left", "r": "Right", "right": "Right"},
                    )
                ],
                primary_job_context_key="side",
            )
        elif preset_name == "azure_adls":
            return cls(
                project_id=project_id,
                name="Azure Data Lake",
                source=SourceType.ADLS,
                roots=DataRoots(
                    templates_root="abfss://container/templates",
                    output_root="abfss://container/output",
                ),
                job_contexts=[
                    JobContext(
                        name="Wafer",
                        key="wafer",
                        values=["W1", "W2", "W3"],
                        aliases={"w1": "W1", "w2": "W2", "w3": "W3"},
                    )
                ],
                primary_job_context_key="wafer",
            )
        else:
            raise ValueError(f"Unknown preset: {preset_name}")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Local Filesystem",
            "source": "filesystem",
            "roots": {
                "templates_root": "C:/Users/user/templates",
                "output_root": "C:/Users/user/output",
            },
            "job_contexts": [
                {
                    "name": "Sides",
                    "key": "side",
                    "values": ["Left", "Right"],
                }
            ],
            "primary_job_context_key": "side",
        }
    })


# Validation test
if __name__ == "__main__":
    # Test preset creation
    profile = EnvironmentProfile.create_preset("local_filesystem")
    assert profile.source == SourceType.FILESYSTEM
    primary_ctx = profile.get_primary_context()
    assert primary_ctx is not None
    assert primary_ctx.key == "side"
    assert "Left" in primary_ctx.values

    # Test job context value resolution
    assert primary_ctx.resolve_value("Left") == "Left"
    assert primary_ctx.resolve_value("l") == "Left"
    assert primary_ctx.resolve_value("invalid") is None

    # Test Azure preset
    azure_profile = EnvironmentProfile.create_preset("azure_adls")
    assert azure_profile.source == SourceType.ADLS
    azure_primary_ctx = azure_profile.get_primary_context()
    assert azure_primary_ctx is not None
    assert azure_primary_ctx.key == "wafer"

    print("All environment profile tests passed!")
