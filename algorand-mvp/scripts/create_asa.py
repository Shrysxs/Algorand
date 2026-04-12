from algokit_utils import get_algod_client, get_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.future.transaction import AssetCreateTxn


def create_asa(
    algod: AlgodClient,
    creator_address: str,
    signer: AccountTransactionSigner,
) -> int:

    params = algod.suggested_params()

    txn = AssetCreateTxn(
        sender=creator_address,
        sp=params,
        total=1_000_000_000,
        decimals=6,
        default_frozen=False,
        unit_name="gUSD",
        asset_name="Ghost USD",
        manager=creator_address,
        reserve=creator_address,
        freeze=creator_address,
        clawback=creator_address,
        url="",
        note=b"GhostGas stable asset",
    )

    signed_txn = txn.sign(signer.private_key)
    tx_id = algod.send_transaction(signed_txn)

    result = algod.pending_transaction_info(tx_id)

    asset_id = result["asset-index"]

    return asset_id


def main():
    algod = get_algod_client()

    acct = get_account(algod, "dispenser")
    signer = AccountTransactionSigner(acct.private_key)

    asset_id = create_asa(
        algod,
        acct.address,
        signer,
    )

    print("ASA CREATED")
    print("ASA ID:", asset_id)


if __name__ == "__main__":
    main()