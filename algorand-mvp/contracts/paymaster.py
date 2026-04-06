"""GhostGas paymaster (gas sponsorship eligibility + funding) contract."""

from algopy import *
from algopy.arc4 import ARC4Contract, String, abimethod


class PaymasterContract(ARC4Contract):

    admin = GlobalState(Account)
    settlement_executor = GlobalState(Account)

    asset_id = GlobalState(UInt64)

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
        assert usage_window_seconds > UInt64(0)
        assert max_uses_per_window > UInt64(0)

        self.admin.value = Txn.sender
        self.settlement_executor.value = settlement_executor
        self.asset_id.value = asset_id

        self.usage_window_seconds.value = usage_window_seconds
        self.max_uses_per_window.value = max_uses_per_window

    @abimethod()
    def set_settlement_executor(self, settlement_executor: Account) -> None:
        assert Txn.sender == self.admin.value
        self.settlement_executor.value = settlement_executor

    @abimethod()
    def fund(self, amount: UInt64) -> None:
        pay = Gtxn[Txn.group_index - 1]

        assert pay.type_enum() == TxnType.AssetTransfer
        assert pay.xfer_asset() == self.asset_id.value
        assert pay.asset_receiver() == Global.current_application_address()
        assert pay.asset_amount() == amount

    @abimethod()
    def grant_sponsorship(self, user_wallet: String, now_ts: UInt64) -> UInt64:
        assert Txn.sender == self.settlement_executor.value
        assert now_ts > UInt64(0)

        expiry = now_ts + self.usage_window_seconds.value

        self.eligibility_expiry[user_wallet] = expiry
        self.user_uses[user_wallet] = UInt64(0)

        return expiry

    @abimethod()
    def consume_sponsorship(self, user_wallet: String, now_ts: UInt64) -> UInt64:
        assert Txn.sender == self.settlement_executor.value

        expiry, has_expiry = self.eligibility_expiry.maybe(user_wallet)
        assert has_expiry
        assert now_ts <= expiry

        uses = self.user_uses.get(user_wallet, default=UInt64(0))
        assert uses < self.max_uses_per_window.value

        next_uses = uses + UInt64(1)
        self.user_uses[user_wallet] = next_uses

        return next_uses

    @abimethod()
    def sponsor(self, user: Account, amount: UInt64) -> None:
        assert Txn.sender == self.settlement_executor.value

        InnerTxnBuilder.Begin()
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.asset_receiver: user,
            TxnField.asset_amount: amount,
            TxnField.xfer_asset: self.asset_id.value,
        })
        InnerTxnBuilder.Submit()

    @abimethod(readonly=True)
    def is_eligible(self, user_wallet: String, now_ts: UInt64) -> UInt64:
        expiry, has_expiry = self.eligibility_expiry.maybe(user_wallet)

        if not has_expiry:
            return UInt64(0)

        uses = self.user_uses.get(user_wallet, default=UInt64(0))

        if now_ts > expiry:
            return UInt64(0)

        if uses >= self.max_uses_per_window.value:
            return UInt64(0)

        return UInt64(1)