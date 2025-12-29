"""Profile CRUD service.

Per SPEC-DAT-0005: Profile management with deterministic IDs.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from shared.contracts.dat.profile import (
    ExtractionProfile,
    CreateProfileRequest,
    UpdateProfileRequest,
)
from shared.utils.stage_id import compute_stage_id

__version__ = "1.0.0"

# Default profile storage directory
PROFILES_DIR = Path("data/profiles")


class ProfileService:
    """Service for managing extraction profiles.

    Per ADR-0011: Profile-driven extraction.
    Per ADR-0004: Deterministic IDs.
    """

    def __init__(self, profiles_dir: Path | None = None):
        """Initialize profile service.

        Args:
            profiles_dir: Directory for profile storage.
        """
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _compute_profile_id(self, profile: ExtractionProfile) -> str:
        """Compute deterministic profile ID.

        Per ADR-0004: SHA-256 based IDs.
        """
        inputs = {
            "name": profile.name,
            "file_patterns": [p.model_dump() for p in profile.file_patterns],
            "column_mappings": [m.model_dump() for m in profile.column_mappings],
        }
        return compute_stage_id(inputs, prefix="profile_")

    def _get_profile_path(self, profile_id: str) -> Path:
        """Get path to profile JSON file."""
        return self.profiles_dir / f"{profile_id}.json"

    async def create(self, request: CreateProfileRequest) -> ExtractionProfile:
        """Create a new profile.

        Args:
            request: Profile creation request.

        Returns:
            Created ExtractionProfile.

        Raises:
            ValueError: If profile with same ID already exists.
        """
        profile = ExtractionProfile(
            name=request.name,
            description=request.description,
            file_patterns=request.file_patterns,
            column_mappings=request.column_mappings,
            aggregation_rules=request.aggregation_rules,
            validation_rules=request.validation_rules,
            created_at=datetime.now(timezone.utc),
        )

        profile_id = self._compute_profile_id(profile)
        profile_path = self._get_profile_path(profile_id)

        if profile_path.exists():
            raise ValueError(f"Profile already exists: {profile_id}")

        # Add ID to profile
        profile_dict = profile.model_dump()
        profile_dict["profile_id"] = profile_id

        profile_path.write_text(json.dumps(profile_dict, default=str, indent=2))

        return ExtractionProfile(**profile_dict)

    async def get(self, profile_id: str) -> ExtractionProfile | None:
        """Get a profile by ID.

        Args:
            profile_id: Profile identifier.

        Returns:
            ExtractionProfile or None if not found.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            return None

        data = json.loads(profile_path.read_text())
        return ExtractionProfile(**data)

    async def update(
        self,
        profile_id: str,
        request: UpdateProfileRequest,
    ) -> ExtractionProfile | None:
        """Update an existing profile.

        Args:
            profile_id: Profile identifier.
            request: Update request.

        Returns:
            Updated ExtractionProfile or None if not found.
        """
        existing = await self.get(profile_id)
        if not existing:
            return None

        # Apply updates
        update_data = request.model_dump(exclude_unset=True)
        profile_dict = existing.model_dump()
        profile_dict.update(update_data)
        profile_dict["updated_at"] = datetime.now(timezone.utc)

        profile_path = self._get_profile_path(profile_id)
        profile_path.write_text(json.dumps(profile_dict, default=str, indent=2))

        return ExtractionProfile(**profile_dict)

    async def delete(self, profile_id: str) -> bool:
        """Delete a profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if deleted, False if not found.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            return False

        profile_path.unlink()
        return True

    async def list_all(self) -> list[ExtractionProfile]:
        """List all profiles.

        Returns:
            List of all profiles.
        """
        profiles = []
        for profile_path in self.profiles_dir.glob("*.json"):
            data = json.loads(profile_path.read_text())
            profiles.append(ExtractionProfile(**data))
        return profiles
