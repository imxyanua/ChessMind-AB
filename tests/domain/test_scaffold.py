"""Smoke tests for project scaffold (P1-0)."""

from chessmind_ab import __version__


def test_package_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_domain_package_imports() -> None:
    import chessmind_ab.domain as domain

    assert domain is not None
