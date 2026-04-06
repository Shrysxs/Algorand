from algopy import *
from algopy.arc4 import ARC4Contract, String, abimethod


class CampaignContract(ARC4Contract):

    advertiser = GlobalState(Account)
    settlement_executor = GlobalState(Account)

    asset_id = GlobalState(UInt64)
    budget = GlobalState(UInt64)

    cost_per_impression = GlobalState(UInt64)
    min_view_seconds = GlobalState(UInt64)
    target_region = GlobalState(String)

    spent = GlobalState(UInt64)
    active = GlobalState(UInt64)

    @abimethod(create=True)
    def create(
        self,
        asset_id: UInt64,
        cost_per_impression: UInt64,
        min_view_seconds: UInt64,
        target_region: String,
    ) -> None:
        assert cost_per_impression > UInt64(0)

        self.advertiser.value = Txn.sender
        self.settlement_executor.value = Txn.sender

        self.asset_id.value = asset_id
        self.budget.value = UInt64(0)

        self.cost_per_impression.value = cost_per_impression
        self.min_view_seconds.value = min_view_seconds
        self.target_region.value = target_region

        self.spent.value = UInt64(0)
        self.active.value = UInt64(1)

    @abimethod()
    def configure(
        self,
        cost_per_impression: UInt64,
        min_view_seconds: UInt64,
        target_region: String,
    ) -> None:
        assert Txn.sender == self.advertiser.value
        assert cost_per_impression > UInt64(0)

        self.cost_per_impression.value = cost_per_impression
        self.min_view_seconds.value = min_view_seconds
        self.target_region.value = target_region

    @abimethod()
    def set_settlement_executor(self, executor: Account) -> None:
        assert Txn.sender == self.advertiser.value
        self.settlement_executor.value = executor

    @abimethod()
    def deposit_budget(self, amount: UInt64) -> UInt64:
        assert Txn.sender == self.advertiser.value
        assert amount > UInt64(0)

        pay = Gtxn[Txn.group_index - 1]

        assert pay.type_enum() == TxnType.AssetTransfer
        assert pay.xfer_asset() == self.asset_id.value
        assert pay.asset_receiver() == Global.current_application_address()
        assert pay.asset_amount() == amount

        self.budget.value = self.budget.value + amount
        return self.budget.value

    @abimethod()
    def pause(self) -> None:
        assert Txn.sender == self.advertiser.value
        self.active.value = UInt64(0)

    @abimethod()
    def resume(self) -> None:
        assert Txn.sender == self.advertiser.value
        self.active.value = UInt64(1)

    @abimethod()
    def deduct_for_impression(
        self,
        user_view_seconds: UInt64,
        user_region: String,
    ) -> UInt64:

        assert Txn.sender == self.settlement_executor.value
        assert self.active.value == UInt64(1)

        assert user_view_seconds >= self.min_view_seconds.value
        assert user_region == self.target_region.value

        assert self.budget.value >= self.cost_per_impression.value

        self.budget.value = self.budget.value - self.cost_per_impression.value
        self.spent.value = self.spent.value + self.cost_per_impression.value

        return self.cost_per_impression.value

    @abimethod(readonly=True)
    def get_budget(self) -> UInt64:
        return self.budget.value