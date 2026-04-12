"""Build and deploy GhostGas contracts using AlgoKit."""

from __future__ import annotations

import subprocess
from pathlib import Path

from algokit_utils import get_algod_client, get_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "contracts"
ARTIFACTS_DIR = ROOT / "artifacts" / "ghostgas"

CONTRACT_NAMES = ["campaign", "attestation", "settlement", "paymaster"]

ASA_ID = 0


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

    acct = get_account(algod, "dispenser")
    signer = AccountTransactionSigner(acct.private_key)

    from artifacts.ghostgas.attestation.attestation_client import AttestationClient
    from artifacts.ghostgas.paymaster.paymaster_client import PaymasterClient
    from artifacts.ghostgas.settlement.settlement_client import SettlementClient
    from artifacts.ghostgas.campaign.campaign_client import CampaignClient

    attestation = AttestationClient(algod, acct.address, signer)
    attestation_app_id, _, _ = attestation.create(verifier=acct.address)

    paymaster = PaymasterClient(algod, acct.address, signer)
    paymaster_app_id, _, _ = paymaster.create(
        settlement_executor=acct.address,
        asset_id=ASA_ID,
        usage_window_seconds=600,
        max_uses_per_window=3,
    )

    settlement = SettlementClient(algod, acct.address, signer)
    settlement_app_id, _, _ = settlement.create(
        oracle=acct.address,
        publisher_bps=7000,
        gas_pool_bps=3000,
        attestation_app=attestation_app_id,
        paymaster_app=paymaster_app_id,
    )

    attestation.call("set_settlement", app_id=settlement_app_id)

    paymaster.call(
        "set_settlement_executor",
        settlement_executor=settlement_app_id
    )

    campaign = CampaignClient(algod, acct.address, signer)
    campaign_app_id, _, _ = campaign.create(
        asset_id=ASA_ID,
        cost_per_impression=50_000,
        min_view_seconds=15,
        target_region="IN",
    )

    campaign.call(
        "set_settlement_executor",
        executor=settlement_app_id
    )

    print("ASA_ID:", ASA_ID)
    print("Campaign:", campaign_app_id)
    print("Settlement:", settlement_app_id)
    print("Paymaster:", paymaster_app_id)
    print("Attestation:", attestation_app_id)


def main():
    compile_all()
    deploy()


if __name__ == "__main__":
    main()