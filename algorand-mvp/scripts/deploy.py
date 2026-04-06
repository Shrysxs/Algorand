"""Build and deploy GhostGas contracts using AlgoKit."""

from __future__ import annotations

import subprocess
from pathlib import Path

from algokit_utils import get_algod_client, get_indexer_client, ApplicationClient
from algosdk.account import generate_account

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


def compile_all():
    for name in CONTRACT_NAMES:
        compile_contract(name)


def deploy():
    algod = get_algod_client()
    indexer = get_indexer_client()

    private_key, address = generate_account()

    print(f"Deployer: {address}")

    # === ATTTESTATION ===
    from artifacts.ghostgas.attestation.attestation_client import AttestationClient

    attestation = AttestationClient(
        algod_client=algod,
        creator=address,
        signer=private_key,
    )

    attestation_app_id, _, _ = attestation.create(
        verifier=address
    )

    print("Attestation App ID:", attestation_app_id)

    # === PAYMASTER ===
    from artifacts.ghostgas.paymaster.paymaster_client import PaymasterClient

    paymaster = PaymasterClient(
        algod_client=algod,
        creator=address,
        signer=private_key,
    )

    paymaster_app_id, _, _ = paymaster.create(
        settlement_executor=address,
        asset_id=0,  # replace with USDC ASA
        usage_window_seconds=600,
        max_uses_per_window=3,
    )

    print("Paymaster App ID:", paymaster_app_id)

    # === SETTLEMENT ===
    from artifacts.ghostgas.settlement.settlement_client import SettlementClient

    settlement = SettlementClient(
        algod_client=algod,
        creator=address,
        signer=private_key,
    )

    settlement_app_id, _, _ = settlement.create(
        oracle=address,
        publisher_bps=7000,
        gas_pool_bps=3000,
        attestation_app=attestation_app_id,
        paymaster_app=paymaster_app_id,
    )

    print("Settlement App ID:", settlement_app_id)

    # link attestation -> settlement
    attestation.call(
        "set_settlement",
        app_id=settlement_app_id
    )

    # === CAMPAIGN ===
    from artifacts.ghostgas.campaign.campaign_client import CampaignClient

    campaign = CampaignClient(
        algod_client=algod,
        creator=address,
        signer=private_key,
    )

    campaign_app_id, _, _ = campaign.create(
        asset_id=0,  # replace with USDC ASA
        cost_per_impression=50_000,  # example
        min_view_seconds=15,
        target_region="IN",
    )

    print("Campaign App ID:", campaign_app_id)

    # set settlement executor
    campaign.call(
        "set_settlement_executor",
        executor=address
    )

    print("\nDeployment complete.")
    print("Campaign:", campaign_app_id)
    print("Settlement:", settlement_app_id)
    print("Paymaster:", paymaster_app_id)
    print("Attestation:", attestation_app_id)


def main():
    compile_all()
    deploy()


if __name__ == "__main__":
    main()