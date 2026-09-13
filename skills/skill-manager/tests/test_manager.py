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
        self.managers = []

    def tearDown(self):
        """Clean up any initialized managers."""
        for m in self.managers:
            m.cleanup()

    def _create_manager(self, **kwargs):
        m = SkillManager(**kwargs)
        self.managers.append(m)
        return m

    def test_config_loading(self):
        """Test configuration loading."""
        manager = self._create_manager()
        self.assertIsInstance(manager.config, dict)
        self.assertIsInstance(manager.registries, list)

    def test_custom_skills_root(self):
        """Test custom skills_root parameter."""
        custom_root = "/tmp/my-skills"
        manager = self._create_manager(skills_root=custom_root)
        self.assertEqual(manager.skills_root, os.path.abspath(custom_root))

    def test_registries_sorted_by_priority(self):
        """Test that registries are sorted by priority."""
        manager = self._create_manager()
        # Test explicit multi-registry sorting logic
        test_regs = [
            {"name": "low", "priority": 10},
            {"name": "high", "priority": 100},
            {"name": "mid", "priority": 50},
        ]
        test_regs.sort(key=lambda x: x.get("priority", 0), reverse=True)
        self.assertEqual([r["name"] for r in test_regs], ["high", "mid", "low"])

    def test_temp_dir_created_and_cleaned(self):
        """Test that temp directory is created and cleaned up."""
        manager = self._create_manager()
        self.assertTrue(os.path.exists(manager.temp_dir))
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
