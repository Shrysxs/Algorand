from algokit_utils import get_algod_client
from algosdk.account import generate_account
from algosdk.transaction import (
    AssetConfigTxn,
    AssetTransferTxn,
    assign_group_id,
)
from algosdk import encoding

from artifacts.ghostgas.campaign.campaign_client import CampaignClient
from artifacts.ghostgas.attestation.attestation_client import AttestationClient
from artifacts.ghostgas.settlement.settlement_client import SettlementClient
from artifacts.ghostgas.paymaster.paymaster_client import PaymasterClient


def create_asa(client, creator_sk, creator_addr):
    params = client.suggested_params()

    txn = AssetConfigTxn(
        sender=creator_addr,
        sp=params,
        total=10_000_000,
        decimals=6,
        default_frozen=False,
        unit_name="gUSDC",
        asset_name="GhostGas USD",
    )

    signed = txn.sign(creator_sk)
    txid = client.send_transaction(signed)
    result = client.pending_transaction_info(txid)

    return result["asset-index"]


def opt_in_asset(client, account_sk, account_addr, asset_id):
    params = client.suggested_params()

    txn = AssetTransferTxn(
        sender=account_addr,
        sp=params,
        receiver=account_addr,
        amt=0,
        index=asset_id,
    )

    client.send_transaction(txn.sign(account_sk))


def main():
    client = get_algod_client()

    # accounts
    adv_sk, adv_addr = generate_account()
    pub_sk, pub_addr = generate_account()
    user_sk, user_addr = generate_account()

    print("\n=== GhostGas Production Simulation ===")

    asset_id = create_asa(client, adv_sk, adv_addr)
    print("ASA created:", asset_id)

    opt_in_asset(client, pub_sk, pub_addr, asset_id)
    opt_in_asset(client, user_sk, user_addr, asset_id)

    attestation = AttestationClient(client, adv_addr, adv_sk)
    att_id, _, _ = attestation.create(verifier=adv_addr)

    paymaster = PaymasterClient(client, adv_addr, adv_sk)
    pay_id, _, _ = paymaster.create(
        settlement_executor=adv_addr,
        asset_id=asset_id,
        usage_window_seconds=600,
        max_uses_per_window=3,
    )

    settlement = SettlementClient(client, adv_addr, adv_sk)
    set_id, _, _ = settlement.create(
        oracle=adv_addr,
        publisher_bps=7000,
        gas_pool_bps=3000,
        attestation_app=att_id,
        paymaster_app=pay_id,
    )

    campaign = CampaignClient(client, adv_addr, adv_sk)
    camp_id, _, _ = campaign.create(
        asset_id=asset_id,
        cost_per_impression=50_000,
        min_view_seconds=10,
        target_region="IN",
    )

    campaign.call("set_settlement_executor", executor=adv_addr)

    print("\nContracts deployed")
    print("Campaign:", camp_id)
=

    params = client.suggested_params()

    payment_txn = AssetTransferTxn(
        sender=adv_addr,
        sp=params,
        receiver=encoding.encode_address(
            encoding.decode_address(campaign.app_address)
        ),
        amt=500_000,
        index=asset_id,
    )

    app_call_txn = campaign.get_call_txn(
        "deposit_budget",
        amount=500_000,
    )

    assign_group_id([payment_txn, app_call_txn])

    signed_payment = payment_txn.sign(adv_sk)
    signed_call = app_call_txn.sign(adv_sk)

    client.send_transactions([signed_payment, signed_call])

    print("Campaign funded with ASA")


    proof_id = "user1:ad1:123"

    attestation.call(
        "record_attestation",
        proof_id=proof_id,
        observed_at=123456,
    )

    print("Attestation recorded")

    settlement.call(
        "settle_impression",
        proof_id=proof_id,
        campaign_app=camp_id,
        publisher=pub_addr,
        user=user_addr,
        now_ts=123456,
    )

    print("Settlement executed")


    eligible = paymaster.call(
        "is_eligible",
        user_wallet=user_addr,
        now_ts=123456,
    )

    print("User eligible:", bool(eligible))

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
