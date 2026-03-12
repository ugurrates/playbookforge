"""
Tests for PlaybookForge Vendor Product Catalog.
"""

import pytest
from backend.core.products import (
    ProductCatalog,
    ProductCategory,
    Product,
    ProductAction,
    ActionParameter,
    product_catalog,
)


class TestProductCatalog:
    """Test the global product catalog instance."""

    def test_catalog_loads_all_products(self):
        assert product_catalog.count() == 26

    def test_all_products_have_unique_ids(self):
        products = product_catalog.list_all()
        ids = [p.id for p in products]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {[i for i in ids if ids.count(i) > 1]}"

    def test_all_products_have_actions(self):
        for p in product_catalog.list_all():
            assert len(p.actions) >= 3, f"Product {p.id} has only {len(p.actions)} actions (min 3)"

    def test_all_actions_have_unique_ids_per_product(self):
        for p in product_catalog.list_all():
            action_ids = [a.id for a in p.actions]
            assert len(action_ids) == len(set(action_ids)), (
                f"Product {p.id} has duplicate action IDs"
            )

    def test_all_actions_have_required_fields(self):
        for p in product_catalog.list_all():
            for a in p.actions:
                assert a.id, f"{p.id}: action missing id"
                assert a.name, f"{p.id}: action {a.id} missing name"
                assert a.description, f"{p.id}: action {a.id} missing description"
                assert a.http_method in ("GET", "POST", "PUT", "PATCH", "DELETE"), (
                    f"{p.id}: action {a.id} has invalid method {a.http_method}"
                )

    def test_all_products_have_metadata(self):
        for p in product_catalog.list_all():
            assert p.name, f"{p.id}: missing name"
            assert p.vendor, f"{p.id}: missing vendor"
            assert p.description, f"{p.id}: missing description"
            assert p.logo_abbr, f"{p.id}: missing logo_abbr"
            assert p.logo_color, f"{p.id}: missing logo_color"
            assert p.category, f"{p.id}: missing category"

    def test_all_categories_present(self):
        cats = set(p.category.value for p in product_catalog.list_all())
        # We have products in these categories at minimum
        expected = {"firewall", "edr-xdr", "siem", "email-security", "waf",
                    "identity-iam", "threat-intel", "ticketing"}
        assert expected.issubset(cats), f"Missing categories: {expected - cats}"


class TestCatalogFiltering:
    """Test filtering and search functionality."""

    def test_filter_by_category_firewall(self):
        firewalls = product_catalog.list_all(category="firewall")
        assert len(firewalls) == 4
        for p in firewalls:
            assert p.category == ProductCategory.FIREWALL

    def test_filter_by_category_edr(self):
        edr = product_catalog.list_all(category="edr-xdr")
        assert len(edr) == 5  # CrowdStrike, SentinelOne, MDE, Carbon Black, Cortex XDR
        for p in edr:
            assert p.category == ProductCategory.EDR_XDR

    def test_filter_by_category_identity(self):
        iam = product_catalog.list_all(category="identity-iam")
        assert len(iam) == 4  # Entra ID, AD, Okta, CyberArk
        for p in iam:
            assert p.category == ProductCategory.IDENTITY_IAM

    def test_filter_nonexistent_category(self):
        result = product_catalog.list_all(category="nonexistent")
        assert result == []

    def test_search_by_vendor(self):
        results = product_catalog.search("Microsoft")
        names = [p.name for p in results]
        assert any("Entra" in n for n in names)
        assert any("Defender" in n for n in names)

    def test_search_by_product_name(self):
        results = product_catalog.search("CrowdStrike")
        assert len(results) >= 1
        assert results[0].id == "crowdstrike_falcon"

    def test_search_case_insensitive(self):
        results = product_catalog.search("palo alto")
        assert len(results) >= 1
        ids = [p.id for p in results]
        assert "paloalto_ngfw" in ids

    def test_search_by_category(self):
        results = product_catalog.search("firewall")
        assert len(results) >= 2

    def test_search_empty(self):
        results = product_catalog.search("")
        # Empty string matches everything
        assert len(results) == 26


class TestCatalogLookup:
    """Test single product lookup."""

    def test_get_existing_product(self):
        p = product_catalog.get("crowdstrike_falcon")
        assert p is not None
        assert p.name == "CrowdStrike Falcon"
        assert p.vendor == "CrowdStrike"
        assert p.category == ProductCategory.EDR_XDR

    def test_get_nonexistent_product(self):
        assert product_catalog.get("nonexistent_product") is None

    def test_get_cortex_xdr(self):
        p = product_catalog.get("cortex_xdr")
        assert p is not None
        assert p.vendor == "Palo Alto Networks"
        assert p.category == ProductCategory.EDR_XDR
        action_ids = [a.id for a in p.actions]
        assert "isolate_endpoint" in action_ids
        assert "block_file_hash" in action_ids

    def test_get_entra_id(self):
        p = product_catalog.get("entra_id")
        assert p is not None
        assert p.vendor == "Microsoft"
        assert p.category == ProductCategory.IDENTITY_IAM
        action_ids = [a.id for a in p.actions]
        assert "disable_user" in action_ids
        assert "revoke_sessions" in action_ids
        assert "get_risky_users" in action_ids

    def test_get_virustotal(self):
        p = product_catalog.get("virustotal")
        assert p is not None
        assert len(p.actions) == 5  # lookup_hash, ip, domain, url, submit_file


class TestCatalogCategories:
    """Test categories method."""

    def test_categories_returns_dict(self):
        cats = product_catalog.categories()
        assert isinstance(cats, dict)
        assert "firewall" in cats
        assert "edr-xdr" in cats

    def test_categories_counts_correct(self):
        cats = product_catalog.categories()
        assert cats["firewall"] == 4
        assert cats["edr-xdr"] == 5
        assert cats["siem"] == 3
        assert cats["identity-iam"] == 4
        assert cats["ticketing"] == 2


class TestProductActions:
    """Test get_actions_for_products method."""

    def test_get_actions_for_single_product(self):
        result = product_catalog.get_actions_for_products(["virustotal"])
        assert "virustotal" in result
        assert len(result["virustotal"]) == 5
        action_names = [a["name"] for a in result["virustotal"]]
        assert "Lookup File Hash" in action_names

    def test_get_actions_for_multiple_products(self):
        result = product_catalog.get_actions_for_products(["crowdstrike_falcon", "entra_id"])
        assert len(result) == 2
        assert "crowdstrike_falcon" in result
        assert "entra_id" in result

    def test_get_actions_nonexistent_product(self):
        result = product_catalog.get_actions_for_products(["nonexistent"])
        assert result == {}

    def test_get_actions_mixed(self):
        result = product_catalog.get_actions_for_products(["virustotal", "nonexistent"])
        assert "virustotal" in result
        assert "nonexistent" not in result


class TestSpecificProducts:
    """Test specific products are correctly defined."""

    @pytest.mark.parametrize("product_id", [
        "paloalto_ngfw", "fortinet_fortigate", "checkpoint_firewall", "cisco_asa",
        "crowdstrike_falcon", "sentinelone", "ms_defender_endpoint", "vmware_carbon_black",
        "cortex_xdr", "splunk_enterprise", "ibm_qradar", "elastic_siem",
        "proofpoint_tap", "mimecast", "ms_defender_office365",
        "cloudflare_waf", "aws_waf",
        "entra_id", "active_directory", "okta", "cyberark",
        "virustotal", "abuseipdb", "alienvault_otx",
        "servicenow", "jira",
    ])
    def test_product_exists(self, product_id: str):
        p = product_catalog.get(product_id)
        assert p is not None, f"Product {product_id} not found"
        assert len(p.actions) >= 3, f"Product {product_id} needs at least 3 actions"
