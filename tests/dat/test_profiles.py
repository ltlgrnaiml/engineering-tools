"""Tests for DAT profile loading and parsing."""
import pytest
from pathlib import Path

from apps.data_aggregator.backend.src.dat_aggregation.profiles import (
    DATProfile,
    load_profile,
    load_profile_from_string,
    get_builtin_profiles,
    get_profile_by_id,
)


PROFILES_DIR = Path(__file__).parent.parent.parent / "apps" / "data_aggregator" / "backend" / "src" / "dat_aggregation" / "profiles"


class TestProfileLoader:
    """Test profile loading functionality."""
    
    def test_load_cdsem_profile(self):
        """Test loading the CD-SEM metrology profile."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert profile.profile_id == "cdsem-metrology-v1"
        assert profile.title == "CD-SEM Metrology Data Profile"
        assert profile.schema_version == "1.0.0"
        assert profile.version == 1
    
    def test_profile_meta_fields(self):
        """Test profile metadata is correctly parsed."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert profile.created_by == "CDU-DAT Engineering Team"
        assert profile.description is not None
        assert len(profile.description) > 0
    
    def test_profile_datasource(self):
        """Test datasource configuration parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert profile.datasource_id == "cdsem-json"
        assert profile.datasource_format == "json"
        assert "json" in profile.datasource_options
    
    def test_profile_levels(self):
        """Test levels configuration parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert len(profile.levels) == 2
        
        run_level = profile.get_level("run")
        assert run_level is not None
        assert len(run_level.tables) > 0
        
        image_level = profile.get_level("image")
        assert image_level is not None
        assert len(image_level.tables) > 0
    
    def test_profile_tables(self):
        """Test table configuration parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        # Check run_summary table
        run_summary = profile.get_table("run", "run_summary")
        assert run_summary is not None
        assert run_summary.label == "Run Summary"
        assert run_summary.select.strategy == "flat_object"
        assert run_summary.select.path == "$.summary"
        
        # Check table with headers_data strategy
        run_stats = profile.get_table("run", "run_statistics")
        assert run_stats is not None
        assert run_stats.select.strategy == "headers_data"
        assert run_stats.select.headers_key == "columns"
        assert run_stats.select.data_key == "values"
    
    def test_profile_tables_with_repeat_over(self):
        """Test table configuration with repeat_over parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        cd_by_site = profile.get_table("run", "cd_by_site")
        assert cd_by_site is not None
        assert cd_by_site.select.repeat_over is not None
        assert cd_by_site.select.repeat_over["path"] == "$.sites"
    
    def test_profile_context_defaults(self):
        """Test context defaults parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert profile.context_defaults is not None
        assert "jobname" in profile.context_defaults.defaults
        assert len(profile.context_defaults.regex_patterns) > 0
    
    def test_profile_regex_patterns(self):
        """Test regex pattern parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        patterns = profile.context_defaults.regex_patterns
        lot_pattern = next((p for p in patterns if p.field == "lot_id"), None)
        
        assert lot_pattern is not None
        assert "LOT" in lot_pattern.pattern
        assert lot_pattern.required is True
    
    def test_extract_context_from_filename(self):
        """Test context extraction from filename using regex patterns."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        filename = "LOTABC12345_W01_CDSEM001_20251227_measurement.json"
        context = profile.extract_context_from_filename(filename)
        
        assert context.get("lot_id") == "LOTABC12345"
        assert context.get("wafer_id") == "W01"
        assert context.get("tool_id") == "CDSEM001"
    
    def test_profile_normalization(self):
        """Test normalization settings parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert "N/A" in profile.nan_values
        assert profile.units_policy == "preserve"
        assert profile.numeric_coercion is True
    
    def test_profile_outputs(self):
        """Test output configuration parsing."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        assert len(profile.default_outputs) > 0
        assert len(profile.optional_outputs) > 0
        
        run_export = next((o for o in profile.default_outputs if o.id == "run_summary_export"), None)
        assert run_export is not None
        assert run_export.from_level == "run"
        assert "run_summary" in run_export.from_tables
    
    def test_get_all_tables(self):
        """Test getting all tables across levels."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        all_tables = profile.get_all_tables()
        assert len(all_tables) > 0
        
        # Should have tables from both run and image levels
        run_tables = [t for level, t in all_tables if level == "run"]
        image_tables = [t for level, t in all_tables if level == "image"]
        
        assert len(run_tables) > 0
        assert len(image_tables) > 0
    
    def test_load_profile_from_string(self):
        """Test loading profile from YAML string."""
        yaml_content = """
schema_version: "1.0.0"
version: 1

meta:
  profile_id: "test-profile"
  title: "Test Profile"
  description: "A test profile"

levels:
  - name: "test"
    tables:
      - id: "test_table"
        label: "Test Table"
        select:
          strategy: "flat_object"
          path: "$.data"
"""
        profile = load_profile_from_string(yaml_content)
        
        assert profile.profile_id == "test-profile"
        assert profile.title == "Test Profile"
        assert len(profile.levels) == 1
        assert profile.levels[0].tables[0].id == "test_table"
    
    def test_get_builtin_profiles(self):
        """Test getting list of built-in profiles."""
        profiles = get_builtin_profiles()
        
        assert isinstance(profiles, dict)
        assert "cdsem-metrology-v1" in profiles
    
    def test_get_profile_by_id(self):
        """Test loading profile by ID."""
        profile = get_profile_by_id("cdsem-metrology-v1")
        
        assert profile is not None
        assert profile.profile_id == "cdsem-metrology-v1"
    
    def test_get_profile_by_invalid_id(self):
        """Test loading profile with invalid ID returns None."""
        profile = get_profile_by_id("nonexistent-profile")
        
        assert profile is None


class TestProfileValidation:
    """Test profile validation and error handling."""
    
    def test_profile_with_missing_required_fields(self):
        """Test handling of profile with missing required fields."""
        yaml_content = """
schema_version: "1.0.0"
version: 1
"""
        profile = load_profile_from_string(yaml_content)
        
        # Should load with empty/default values
        assert profile.profile_id == ""
        assert profile.title == ""
    
    def test_profile_stable_columns(self):
        """Test stable columns configuration."""
        profile_path = PROFILES_DIR / "cdsem_metrology_profile.yaml"
        profile = load_profile(profile_path)
        
        run_summary = profile.get_table("run", "run_summary")
        assert "total_images" in run_summary.stable_columns
        assert run_summary.stable_columns_mode == "warn"
        assert run_summary.stable_columns_subset is True
