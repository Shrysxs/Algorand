"""GhostGas campaign contract.

One campaign app per advertiser campaign keeps accounting isolated and upgrade-safe.
"""

from algopy import Account, GlobalState, Txn, UInt64
from algopy.arc4 import ARC4Contract, String, abimethod


class CampaignContract(ARC4Contract):
    """Escrow-style budget manager for one ad campaign."""

    advertiser = GlobalState(Account, description="Campaign owner allowed to configure terms")
    settlement_executor = GlobalState(Account, description="Trusted settlement caller")
    budget = GlobalState(UInt64, description="Remaining campaign budget in micro units")
    cost_per_impression = GlobalState(UInt64, description="Cost charged per valid impression")
    min_view_seconds = GlobalState(UInt64, description="Simple targeting guard")
    target_region = GlobalState(String, description="Simplified targeting field")
    spent = GlobalState(UInt64, description="Total amount consumed by campaign")
    active = GlobalState(UInt64, description="1 means active, 0 means paused")

    @abimethod(create=True)
    def create(
        self,
        cost_per_impression: UInt64,
        min_view_seconds: UInt64,
        target_region: String,
    ) -> None:
        assert cost_per_impression > UInt64(0), "invalid cpi"
        self.advertiser.value = Txn.sender
        self.settlement_executor.value = Txn.sender
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
        assert Txn.sender == self.advertiser.value, "only advertiser"
        assert cost_per_impression > UInt64(0), "invalid cpi"
        self.cost_per_impression.value = cost_per_impression
        self.min_view_seconds.value = min_view_seconds
        self.target_region.value = target_region

    @abimethod()
    def set_settlement_executor(self, executor: Account) -> None:
        assert Txn.sender == self.advertiser.value, "only advertiser"
        self.settlement_executor.value = executor

    @abimethod()
    def deposit_budget(self, amount: UInt64) -> UInt64:
        assert Txn.sender == self.advertiser.value, "only advertiser"
        assert amount > UInt64(0), "invalid amount"
        self.budget.value = self.budget.value + amount
        return self.budget.value

    @abimethod()
    def pause(self) -> None:
        assert Txn.sender == self.advertiser.value, "only advertiser"
        self.active.value = UInt64(0)

    @abimethod()
    def resume(self) -> None:
        assert Txn.sender == self.advertiser.value, "only advertiser"
        self.active.value = UInt64(1)

    @abimethod()
    def deduct_for_impression(self, user_view_seconds: UInt64, user_region: String) -> UInt64:
        """Deduct one impression; callable by settlement flow only."""
        assert Txn.sender == self.settlement_executor.value, "only settlement"
        assert self.active.value == UInt64(1), "campaign paused"
        assert user_view_seconds >= self.min_view_seconds.value, "view too short"
        assert user_region == self.target_region.value, "target mismatch"
        assert self.budget.value >= self.cost_per_impression.value, "insufficient budget"
        self.budget.value = self.budget.value - self.cost_per_impression.value
        self.spent.value = self.spent.value + self.cost_per_impression.value
        return self.cost_per_impression.value

    @abimethod(readonly=True)
    def get_budget(self) -> UInt64:
        return self.budget.value
