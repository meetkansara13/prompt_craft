"""
tests/unit/test_frameworks.py
================================
Unit tests for the Framework registry.
These tests run with zero external dependencies — no API, no Flask.
"""

import pytest
from app.core.frameworks.registry import (
    get_framework, all_frameworks, FRAMEWORK_REGISTRY, Framework,
)


class TestFrameworkRegistry:

    def test_all_frameworks_returns_list(self):
        frameworks = all_frameworks()
        assert isinstance(frameworks, list)
        assert len(frameworks) >= 10

    def test_every_framework_has_required_fields(self):
        for fw in all_frameworks():
            assert fw.key,         f"{fw.name}: missing key"
            assert fw.name,        f"{fw.key}: missing name"
            assert fw.components,  f"{fw.key}: missing components"
            assert fw.tier,        f"{fw.key}: missing tier"
            assert fw.best_for,    f"{fw.key}: missing best_for"

    def test_risen_exists_and_correct(self):
        fw = get_framework("RISEN")
        assert fw.key == "RISEN"
        assert "Role" in fw.components
        assert "Instructions" in fw.components
        assert fw.tier == "expert"

    def test_ptcf_is_gemini_tier(self):
        fw = get_framework("PTCF")
        assert fw.tier == "gemini"
        assert "Persona" in fw.components

    def test_rtf_is_simple_tier(self):
        fw = get_framework("RTF")
        assert fw.tier == "simple"
        assert len(fw.components) == 3

    def test_get_framework_unknown_key_raises(self):
        with pytest.raises(KeyError, match="Unknown framework"):
            get_framework("NONEXISTENT")

    def test_registry_dict_matches_list(self):
        list_keys = {fw.key for fw in all_frameworks()}
        dict_keys  = set(FRAMEWORK_REGISTRY.keys())
        assert list_keys == dict_keys

    def test_all_framework_keys_unique(self):
        keys = [fw.key for fw in all_frameworks()]
        assert len(keys) == len(set(keys)), "Duplicate framework keys found"
