"""Storage service for file management."""

import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from apps.pptx_generator.backend.core.config import settings


class StorageService:
    """
    Service for managing file storage operations.

    Handles file uploads, downloads, and cleanup operations.
    """

    def __init__(self) -> None:
        """Initialize the storage service."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.generated_dir = Path(settings.GENERATED_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(
        self,
        file: BinaryIO,
        file_id: UUID,
        extension: str,
    ) -> Path:
        """
        Save an uploaded file to the upload directory.

        Args:
            file: Binary file object to save.
            file_id: Unique identifier for the file.
            extension: File extension (e.g., '.pptx', '.xlsx').

        Returns:
            Path: Path to the saved file.

        Raises:
            IOError: If file cannot be saved.
        """
        file_path = self.upload_dir / f"{file_id}{extension}"
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file, buffer)
        return file_path

    async def save_generated(
        self,
        source_path: Path,
        file_id: UUID,
        extension: str = ".pptx",
    ) -> Path:
        """
        Save a generated file to the generated directory.

        Args:
            source_path: Path to the source file to copy.
            file_id: Unique identifier for the generated file.
            extension: File extension (default: '.pptx').

        Returns:
            Path: Path to the saved generated file.

        Raises:
            IOError: If file cannot be saved.
        """
        file_path = self.generated_dir / f"{file_id}{extension}"
        shutil.copy2(source_path, file_path)
        return file_path

    async def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to the file to delete.

        Returns:
            bool: True if file was deleted, False if file didn't exist.

        Raises:
            IOError: If file cannot be deleted.
        """
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_upload_path(self, file_id: UUID, extension: str) -> Path:
        """
        Get the path for an uploaded file.

        Args:
            file_id: Unique identifier for the file.
            extension: File extension.

        Returns:
            Path: Path to the uploaded file.
        """
        return self.upload_dir / f"{file_id}{extension}"

    def get_generated_path(self, file_id: UUID, extension: str = ".pptx") -> Path:
        """
        Get the path for a generated file.

        Args:
            file_id: Unique identifier for the file.
            extension: File extension (default: '.pptx').

        Returns:
            Path: Path to the generated file.
        """
        return self.generated_dir / f"{file_id}{extension}"
