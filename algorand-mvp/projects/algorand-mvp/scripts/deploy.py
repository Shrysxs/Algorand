"""Build and deploy GhostGas contracts using AlgoKit tooling."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "contracts"
ARTIFACTS_DIR = ROOT / "artifacts" / "ghostgas"
CONTRACT_NAMES = ["campaign", "attestation", "settlement", "paymaster"]


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or f"Command failed: {' '.join(cmd)}")


def compile_contract(contract_name: str) -> None:
    contract_file = CONTRACTS_DIR / f"{contract_name}.py"
    out_dir = ARTIFACTS_DIR / contract_name
    out_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "algokit",
            "--no-color",
            "compile",
            "python",
            str(contract_file),
            f"--out-dir={out_dir}",
            "--output-source-map",
        ]
    )
    run(
        [
            "algokit",
            "generate",
            "client",
            str(out_dir),
            "--output",
            str(out_dir / f"{contract_name}_client.py"),
        ]
    )


def main() -> None:
    for contract_name in CONTRACT_NAMES:
        compile_contract(contract_name)

    print("GhostGas contract compilation complete.")
    print("Next: run `algokit project deploy localnet` for network deployment workflow.")


if __name__ == "__main__":
    main()
