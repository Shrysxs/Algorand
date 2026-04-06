# GhostGas (Algorand MVP)

Modular smart-contract workspace for GhostGas, a decentralized ad network on Algorand.

## Project Structure

- `contracts/`: GhostGas ARC4 contracts (`campaign`, `attestation`, `settlement`, `paymaster`)
- `smart_contracts/`: AlgoKit template contract area and build/deploy entrypoint
- `scripts/`: utility scripts (including GhostGas compile/deploy helper)
- `tests/`: contract and integration tests
- `config/`: environment/network configuration
- `utils/`: shared constants and helpers

## Local Development

1. Install dependencies:
   - `poetry install`
2. Generate environment values:
   - `algokit generate env-file -a target_network localnet`
3. Start LocalNet:
   - `algokit localnet start`
4. Compile GhostGas contracts:
   - `poetry run python scripts/deploy.py`



