"""Environment-driven network configuration for GhostGas deployment."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkConfig:
    algod_url: str
    algod_token: str
    indexer_url: str
    indexer_token: str
    deployer_alias: str


def load_network_config() -> NetworkConfig:
    """Loads deployment values from env produced by AlgoKit."""
    return NetworkConfig(
        algod_url=os.getenv("ALGOD_SERVER", "http://localhost:4001"),
        algod_token=os.getenv(
            "ALGOD_TOKEN", "a" * 64
        ),
        indexer_url=os.getenv("INDEXER_SERVER", "http://localhost:8980"),
        indexer_token=os.getenv(
            "INDEXER_TOKEN", "a" * 64
        ),
        deployer_alias=os.getenv("DEPLOYER_ALIAS", "DEPLOYER"),
    )
