"""Data processor service for handling user data files."""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class DataProcessorService:
    """
    Service for processing user data files and domain knowledge.

    Handles reading, parsing, and transforming data from various file formats.
    """

    async def read_data_file(self, file_path: Path) -> pd.DataFrame:
        """
        Read a data file and return as a pandas DataFrame.

        Args:
            file_path: Path to the data file (CSV or Excel).

        Returns:
            pd.DataFrame: Parsed data as a DataFrame.

        Raises:
            FileNotFoundError: If data file doesn't exist.
            ValueError: If file format is unsupported or file is invalid.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        file_extension = file_path.suffix.lower()

        try:
            if file_extension == ".csv":
                df = pd.read_csv(file_path)
            elif file_extension in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            # Apply column renames from domain config
            df = self._apply_column_renames(df)

            return df
        except Exception as e:
            raise ValueError(f"Error reading data file: {str(e)}") from e

    def _apply_column_renames(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply column renames from domain config.

        Args:
            df: DataFrame to rename columns.

        Returns:
            DataFrame with renamed columns.
        """
        try:
            from apps.pptx_generator.backend.core.domain_config_service import get_domain_config
            config = get_domain_config()
            rename_map = config.metrics.rename_map

            if rename_map:
                # Only rename columns that exist in the DataFrame
                actual_renames = {k: v for k, v in rename_map.items() if k in df.columns}
                if actual_renames:
                    df = df.rename(columns=actual_renames)
                    print(f"Applied column renames: {actual_renames}")

            return df
        except Exception as e:
            print(f"Could not apply column renames: {e}")
            return df

    async def get_column_names(self, file_path: Path) -> list[str]:
        """
        Get column names from a data file.

        Args:
            file_path: Path to the data file.

        Returns:
            List[str]: List of column names.

        Raises:
            FileNotFoundError: If data file doesn't exist.
            ValueError: If file cannot be read.
        """
        df = await self.read_data_file(file_path)
        return df.columns.tolist()

    async def get_row_count(self, file_path: Path) -> int:
        """
        Get the number of rows in a data file.

        Args:
            file_path: Path to the data file.

        Returns:
            int: Number of data rows (excluding header).

        Raises:
            FileNotFoundError: If data file doesn't exist.
            ValueError: If file cannot be read.
        """
        df = await self.read_data_file(file_path)
        return len(df)

    async def read_domain_knowledge(self, file_path: Path) -> dict[str, Any]:
        """
        Read domain knowledge configuration from YAML or JSON file.

        Args:
            file_path: Path to the domain knowledge file.

        Returns:
            Dict[str, Any]: Domain knowledge configuration.

        Raises:
            FileNotFoundError: If domain knowledge file doesn't exist.
            ValueError: If file format is unsupported or invalid.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Domain knowledge file not found: {file_path}")

        file_extension = file_path.suffix.lower()

        try:
            with file_path.open(encoding="utf-8") as f:
                if file_extension in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                elif file_extension == ".json":
                    import json

                    return json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            raise ValueError(f"Error reading domain knowledge file: {str(e)}") from e

    def apply_transformation(
        self,
        value: Any,
        transformation: str | None,
        domain_knowledge: dict[str, Any] | None = None,
    ) -> Any:
        """
        Apply a transformation to a data value.

        Args:
            value: The value to transform.
            transformation: Type of transformation to apply.
            domain_knowledge: Optional domain-specific transformation rules.

        Returns:
            Any: Transformed value.
        """
        if transformation is None or value is None:
            return value

        if transformation == "currency":
            try:
                currency_symbol = "$"
                if domain_knowledge and "currency_format" in domain_knowledge:
                    currency_map = {"USD": "$", "EUR": "€", "GBP": "£"}
                    currency_symbol = currency_map.get(
                        domain_knowledge["currency_format"],
                        "$",
                    )

                decimal_places = 2
                if domain_knowledge and "decimal_places" in domain_knowledge:
                    decimal_places = domain_knowledge["decimal_places"]

                return f"{currency_symbol}{float(value):,.{decimal_places}f}"
            except (ValueError, TypeError):
                return value

        elif transformation == "percentage":
            try:
                decimal_places = 1
                if domain_knowledge and "decimal_places" in domain_knowledge:
                    decimal_places = domain_knowledge["decimal_places"]

                return f"{float(value):.{decimal_places}f}%"
            except (ValueError, TypeError):
                return value

        elif transformation == "uppercase":
            return str(value).upper()

        elif transformation == "lowercase":
            return str(value).lower()

        elif transformation == "title":
            return str(value).title()

        return value

    async def prepare_data_for_generation(
        self,
        data_path: Path,
        mappings: list[dict[str, Any]],
        domain_knowledge: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Prepare data for presentation generation by applying mappings and transformations.

        Args:
            data_path: Path to the data file.
            mappings: List of data mapping configurations.
            domain_knowledge: Optional domain-specific transformation rules.

        Returns:
            List[Dict[str, Any]]: List of records with transformed data ready for generation.

        Raises:
            FileNotFoundError: If data file doesn't exist.
            ValueError: If data cannot be processed.
        """
        df = await self.read_data_file(data_path)

        # Normalize column names
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]
        df.columns = [
            col.replace("imagecolumn", "imcol").replace("imagerow", "imrow") for col in df.columns
        ]

        prepared_data = []

        for _, row in df.iterrows():
            record = {}

            # First, include ALL columns from the DataFrame
            for col in df.columns:
                record[col] = row[col] if not pd.isna(row[col]) else None

            # Then apply explicit mappings (these can override)
            for mapping in mappings:
                shape_name = mapping["shape_name"]
                # Normalize the data_column name to match the normalized DataFrame columns
                data_column = (
                    mapping["data_column"]
                    .lower()
                    .replace(" ", "_")
                    .replace("imagecolumn", "imcol")
                    .replace("imagerow", "imrow")
                )
                transformation = mapping.get("transformation")
                default_value = mapping.get("default_value")

                if data_column in df.columns:
                    value = row[data_column]
                    if pd.isna(value):
                        value = default_value
                    else:
                        value = self.apply_transformation(
                            value,
                            transformation,
                            domain_knowledge,
                        )
                else:
                    value = default_value

                # Store with the original shape_name (which may be uppercase like 'CD')
                record[shape_name] = value

            prepared_data.append(record)

        return prepared_data
