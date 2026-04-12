"""GhostGas paymaster contract (FIXED)."""

from algopy import *
from algopy.arc4 import ARC4Contract, String, abimethod


class PaymasterContract(ARC4Contract):

    admin = GlobalState(Account)
    settlement_executor = GlobalState(Account)

    asset_id = GlobalState(UInt64)
    balance = GlobalState(UInt64)

    usage_window_seconds = GlobalState(UInt64)
    max_uses_per_window = GlobalState(UInt64)

    eligibility_expiry = BoxMap(String, UInt64, key_prefix="exp")
    user_uses = BoxMap(String, UInt64, key_prefix="uses")

    @abimethod(create=True)
    def create(
        self,
        settlement_executor: Account,
        asset_id: UInt64,
        usage_window_seconds: UInt64,
        max_uses_per_window: UInt64,
    ) -> None:

        self.admin.value = Txn.sender
        self.settlement_executor.value = settlement_executor
        self.asset_id.value = asset_id

        self.usage_window_seconds.value = usage_window_seconds
        self.max_uses_per_window.value = max_uses_per_window

        self.balance.value = UInt64(0)

    @abimethod()
    def fund(self, amount: UInt64) -> None:

        pay = Gtxn[Txn.group_index - 1]

        assert pay.type_enum() == TxnType.AssetTransfer
        assert pay.xfer_asset() == self.asset_id.value
        assert pay.asset_receiver() == Global.current_application_address()
        assert pay.asset_amount() == amount

        self.balance.value += amount

    @abimethod()
    def sponsor(self, user: Account, amount: UInt64) -> None:

        assert Txn.sender == self.settlement_executor.value
        assert self.balance.value >= amount

        self.balance.value -= amount

        InnerTxnBuilder.Begin()
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.asset_receiver: user,
            TxnField.asset_amount: amount,
            TxnField.xfer_asset: self.asset_id.value,
        })
        InnerTxnBuilder.Submit()