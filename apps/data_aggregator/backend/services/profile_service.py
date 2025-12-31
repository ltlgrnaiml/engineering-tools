"""Profile CRUD service.

Per SPEC-0007: Profile management with deterministic IDs.
Per ADR-0012: Profile-driven extraction using Tier-0 DATProfile contracts.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.contracts.dat.profile import DATProfile
from shared.utils.stage_id import compute_stage_id

__version__ = "1.0.0"

# Default profile storage directory
PROFILES_DIR = Path("data/profiles")


class ProfileService:
    """Service for managing DAT extraction profiles.

    Per ADR-0012: Profile-driven extraction.
    Per ADR-0005: Deterministic IDs.
    """

    def __init__(self, profiles_dir: Path | None = None):
        """Initialize profile service.

        Args:
            profiles_dir: Directory for profile storage.
        """
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _compute_profile_id(self, profile: DATProfile) -> str:
        """Compute deterministic profile ID.

        Per ADR-0005: SHA-256 based IDs.
        """
        inputs = {
            "title": profile.title,
            "levels": [level.model_dump() for level in profile.levels],
            "datasource_id": profile.datasource_id,
        }
        return compute_stage_id(inputs, prefix="profile_")

    def _get_profile_path(self, profile_id: str) -> Path:
        """Get path to profile JSON file."""
        return self.profiles_dir / f"{profile_id}.json"

    async def create(self, data: dict[str, Any]) -> DATProfile:
        """Create a new profile from data dict.

        Args:
            data: Profile data dictionary (YAML-like structure).

        Returns:
            Created DATProfile.

        Raises:
            ValueError: If profile with same ID already exists.
        """
        profile = DATProfile(**data)

        profile_id = self._compute_profile_id(profile)
        profile_path = self._get_profile_path(profile_id)

        if profile_path.exists():
            raise ValueError(f"Profile already exists: {profile_id}")

        # Serialize profile with computed ID
        profile_dict = profile.model_dump(mode="json")
        profile_dict["profile_id"] = profile_id

        profile_path.write_text(json.dumps(profile_dict, default=str, indent=2))

        return DATProfile(**profile_dict)

    async def get(self, profile_id: str) -> DATProfile | None:
        """Get a profile by ID.

        Args:
            profile_id: Profile identifier.

        Returns:
            DATProfile or None if not found.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            return None

        data = json.loads(profile_path.read_text())
        return DATProfile(**data)

    async def update(
        self,
        profile_id: str,
        updates: dict[str, Any],
    ) -> DATProfile | None:
        """Update an existing profile.

        Args:
            profile_id: Profile identifier.
            updates: Fields to update.

        Returns:
            Updated DATProfile or None if not found.
        """
        existing = await self.get(profile_id)
        if not existing:
            return None

        # Apply updates
        profile_dict = existing.model_dump(mode="json")
        profile_dict.update(updates)
        profile_dict["modified_at"] = datetime.now(UTC).isoformat()

        profile_path = self._get_profile_path(profile_id)
        profile_path.write_text(json.dumps(profile_dict, default=str, indent=2))

        return DATProfile(**profile_dict)

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

    async def list_all(self) -> list[DATProfile]:
        """List all profiles.

        Returns:
            List of all profiles.
        """
        profiles = []
        for profile_path in self.profiles_dir.glob("*.json"):
            data = json.loads(profile_path.read_text())
            profiles.append(DATProfile(**data))
        return profiles
