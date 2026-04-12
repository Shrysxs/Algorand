from algokit_utils import get_algod_client, get_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import AssetConfigTxn, AssetTransferTxn, assign_group_id
from algosdk.logic import get_application_address

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


def main():
    client = get_algod_client()

    acct = get_account(client, "dispenser")
    signer = AccountTransactionSigner(acct.private_key)

    adv_addr = acct.address
    adv_sk = acct.private_key

    pub = get_account(client, "sandbox")
    pub_addr = pub.address

    user = get_account(client, "sandbox2")
    user_addr = user.address

    print("\n=== GhostGas Simulation ===")

    asset_id = create_asa(client, adv_sk, adv_addr)
    print("ASA:", asset_id)

    attestation = AttestationClient(client, adv_addr, signer)
    att_id, _, _ = attestation.create(verifier=adv_addr)

    paymaster = PaymasterClient(client, adv_addr, signer)
    pay_id, _, _ = paymaster.create(
        settlement_executor=adv_addr,
        asset_id=asset_id,
        usage_window_seconds=600,
        max_uses_per_window=3,
    )

    settlement = SettlementClient(client, adv_addr, signer)
    set_id, _, _ = settlement.create(
        oracle=adv_addr,
        publisher_bps=7000,
        gas_pool_bps=3000,
        attestation_app=att_id,
        paymaster_app=pay_id,
    )

    attestation.call("set_settlement", app_id=set_id)

    paymaster.call(
        "set_settlement_executor",
        settlement_executor=set_id
    )

    campaign = CampaignClient(client, adv_addr, signer)
    camp_id, _, _ = campaign.create(
        asset_id=asset_id,
        cost_per_impression=50_000,
        min_view_seconds=10,
        target_region="IN",
    )

    campaign.call(
        "set_settlement_executor",
        executor=set_id
    )

    campaign.call("opt_in_asset")
    paymaster.call("opt_in_asset")

    print("Campaign:", camp_id)

    params = client.suggested_params()

    payment_txn = AssetTransferTxn(
        sender=adv_addr,
        sp=params,
        receiver=get_application_address(camp_id),
        amt=500_000,
        index=asset_id,
    )

    app_call_txn = campaign.get_call_txn(
        "deposit_budget",
        amount=500_000,
    )

    assign_group_id([payment_txn, app_call_txn])

    client.send_transactions([
        payment_txn.sign(adv_sk),
        app_call_txn.sign(adv_sk),
    ])

    print("Campaign funded")

    proof_id = "user:campaign:123"

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
        user_view_seconds=15,
        user_region="IN",
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