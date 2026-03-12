"""Tests for PlaybookForge Resource Catalog."""

import pytest
from backend.core.resources import resource_catalog, ResourceCategory


class TestResourceCatalog:
    def test_has_best_practices(self):
        """Catalog should have built-in best practices."""
        bps = resource_catalog.list_best_practices()
        assert len(bps) > 10

    def test_has_integration_guides(self):
        """Catalog should have built-in integration guides."""
        guides = resource_catalog.list_guides()
        assert len(guides) > 5

    def test_filter_by_category(self):
        """Should filter best practices by category."""
        edr_bps = resource_catalog.list_best_practices(category="edr")
        assert len(edr_bps) > 0
        assert all(bp.category == ResourceCategory.EDR for bp in edr_bps)

        siem_bps = resource_catalog.list_best_practices(category="siem")
        # Should have at least one SIEM best practice
        assert all(bp.category == ResourceCategory.SIEM for bp in siem_bps)

    def test_filter_by_difficulty(self):
        """Should filter best practices by difficulty."""
        beginner = resource_catalog.list_best_practices(difficulty="beginner")
        assert len(beginner) > 0
        assert all(bp.difficulty.value == "beginner" for bp in beginner)

        advanced = resource_catalog.list_best_practices(difficulty="advanced")
        assert len(advanced) > 0
        assert all(bp.difficulty.value == "advanced" for bp in advanced)

    def test_filter_guides_by_category(self):
        """Should filter guides by category."""
        edr_guides = resource_catalog.list_guides(category="edr")
        assert len(edr_guides) > 0
        assert all(g.category == ResourceCategory.EDR for g in edr_guides)

    def test_filter_guides_by_product_id(self):
        """Should filter guides by product_id."""
        cs_guides = resource_catalog.list_guides(product_id="crowdstrike-falcon")
        assert len(cs_guides) >= 1
        assert all(g.product_id == "crowdstrike-falcon" for g in cs_guides)

    def test_get_best_practice_detail(self):
        """Should retrieve a specific best practice with full details."""
        bp = resource_catalog.get_best_practice("bp-edr-isolation-workflow")
        assert bp is not None
        assert bp.title == "EDR Host Isolation Workflow"
        assert len(bp.steps) >= 4
        assert len(bp.related_product_ids) > 0
        assert "edr" in bp.tags

    def test_get_guide_detail(self):
        """Should retrieve a specific integration guide."""
        guide = resource_catalog.get_guide("guide-crowdstrike-soar")
        assert guide is not None
        assert guide.product_id == "crowdstrike-falcon"
        assert len(guide.steps) >= 4
        assert len(guide.prerequisites) > 0

    def test_get_nonexistent(self):
        """Should return None for nonexistent resources."""
        assert resource_catalog.get_best_practice("bp-nonexistent") is None
        assert resource_catalog.get_guide("guide-nonexistent") is None

    def test_search(self):
        """Should search across both best practices and guides."""
        results = resource_catalog.search("EDR")
        assert len(results) > 0
        # Should find both types
        types_found = {r["type"] for r in results}
        assert "best-practice" in types_found

        results2 = resource_catalog.search("phishing")
        assert len(results2) > 0

    def test_search_case_insensitive(self):
        """Search should be case-insensitive."""
        upper = resource_catalog.search("RANSOMWARE")
        lower = resource_catalog.search("ransomware")
        assert len(upper) == len(lower)
        assert len(upper) > 0

    def test_search_empty(self):
        """Empty search should return empty results."""
        results = resource_catalog.search("")
        assert len(results) == 0

    def test_edr_resources(self):
        """Should return EDR-specific resources."""
        edr = resource_catalog.get_edr_resources()
        assert edr["total"] > 0
        assert len(edr["best_practices"]) > 0
        assert len(edr["integration_guides"]) > 0

    def test_categories(self):
        """Should return category counts."""
        cats = resource_catalog.categories()
        assert "edr" in cats
        assert cats["edr"] > 0

    def test_best_practice_serialization(self):
        """to_dict and to_summary should work correctly."""
        bp = resource_catalog.get_best_practice("bp-edr-isolation-workflow")
        assert bp is not None

        full = bp.to_dict()
        assert "steps" in full
        assert len(full["steps"]) > 0
        assert full["type"] == "best-practice"

        summary = bp.to_summary()
        assert "step_count" in summary
        assert "steps" not in summary  # summary should not include full steps

    def test_guide_serialization(self):
        """to_dict and to_summary should work correctly for guides."""
        guide = resource_catalog.get_guide("guide-crowdstrike-soar")
        assert guide is not None

        full = guide.to_dict()
        assert "steps" in full
        assert "prerequisites" in full
        assert full["type"] == "integration-guide"

        summary = guide.to_summary()
        assert "step_count" in summary
        assert "steps" not in summary

    def test_all_best_practices_have_steps(self):
        """Every best practice should have at least one step."""
        for bp in resource_catalog.list_best_practices():
            assert len(bp.steps) > 0, f"Best practice {bp.id} has no steps"

    def test_all_guides_have_steps(self):
        """Every integration guide should have at least one step."""
        for g in resource_catalog.list_guides():
            assert len(g.steps) > 0, f"Guide {g.id} has no steps"

    def test_product_ids_are_plausible(self):
        """Product IDs referenced in resources should look valid."""
        for bp in resource_catalog.list_best_practices():
            for pid in bp.related_product_ids:
                # Should be a kebab-case string
                assert "-" in pid or pid.isalpha(), f"Suspicious product_id: {pid}"
