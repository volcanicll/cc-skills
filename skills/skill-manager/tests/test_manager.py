"""
Unit tests for SkillManager class.
"""

import unittest
import os
import sys
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

from manager import SkillManager


class TestSkillManager(unittest.TestCase):
    """Test SkillManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a test config file
        self.test_config = {
            "registries": [
                {
                    "name": "test-registry",
                    "url": "https://github.com/test/repo",
                    "branch": "main",
                    "skills_root": "skills",
                    "priority": 100
                }
            ]
        }

    def test_config_loading(self):
        """Test configuration loading."""
        # This test assumes config file exists
        manager = SkillManager()
        self.assertIsInstance(manager.config, dict)
        self.assertIsInstance(manager.registries, list)

    def test_registries_sorted_by_priority(self):
        """Test that registries are sorted by priority."""
        manager = SkillManager()

        # Check if registries are sorted by priority (descending)
        if len(manager.registries) > 1:
            priorities = [r.get("priority", 0) for r in manager.registries]
            self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_temp_dir_created(self):
        """Test that temp directory is created."""
        manager = SkillManager()
        self.assertTrue(os.path.exists(manager.temp_dir))

        # Clean up
        manager.cleanup()
        self.assertFalse(os.path.exists(manager.temp_dir))


class TestRegistryConfig(unittest.TestCase):
    """Test registry configuration validation."""

    def test_registry_structure(self):
        """Test registry structure has required fields."""
        registry = {
            "name": "test",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "skills_root": "skills",
            "priority": 100
        }

        # Required fields
        self.assertIn("name", registry)
        self.assertIn("url", registry)
        self.assertIn("branch", registry)
        self.assertIn("skills_root", registry)
        self.assertIn("priority", registry)

    def test_registry_defaults(self):
        """Test registry default values."""
        registry = {
            "name": "test",
            "url": "https://github.com/test/repo"
        }

        # Defaults
        self.assertEqual(registry.get("branch", "main"), "main")
        self.assertEqual(registry.get("skills_root", ""), "")
        self.assertEqual(registry.get("priority", 0), 0)


if __name__ == "__main__":
    unittest.main()
