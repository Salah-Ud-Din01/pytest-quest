"""Shared pytest configuration for every level."""


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: tests that take a long time, like the oracle")
