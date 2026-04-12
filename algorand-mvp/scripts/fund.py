from algokit_utils import get_algod_client, get_account
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.transaction import AssetTransferTxn


ASA_ID = 0
CAMPAIGN_APP_ID = 0
PAYMASTER_APP_ID = 0


def get_app_address(app_id: int) -> str:
    from algosdk.logic import get_application_address
    return get_application_address(app_id)


def send_asa(algod, sender, signer, receiver, amount):
    params = algod.suggested_params()

    txn = AssetTransferTxn(
        sender=sender,
        sp=params,
        receiver=receiver,
        amt=amount,
        index=ASA_ID,
    )

    signed = txn.sign(signer.private_key)
    txid = algod.send_transaction(signed)
    algod.wait_for_confirmation(txid, 4)


def main():
    algod = get_algod_client()

    acct = get_account(algod, "dispenser")
    signer = AccountTransactionSigner(acct.private_key)

    campaign_addr = get_app_address(CAMPAIGN_APP_ID)
    paymaster_addr = get_app_address(PAYMASTER_APP_ID)

    send_asa(algod, acct.address, signer, campaign_addr, 1_000_000)
    send_asa(algod, acct.address, signer, paymaster_addr, 500_000)

    print("Funding complete")


if __name__ == "__main__":
    main()