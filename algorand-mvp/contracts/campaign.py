from algopy import ARC4Contract, Txn, UInt64
from algopy.arc4 import abimethod


class CampaignContract(ARC4Contract):

    @abimethod(create="require")
    def create(self, cost_per_impression: UInt64) -> None:
        self.cost = cost_per_impression
        self.budget = UInt64(0)

    @abimethod()
    def deposit_budget(self, amount: UInt64) -> None:
        self.budget += amount

    @abimethod()
    def deduct(self) -> UInt64:
        assert self.budget >= self.cost
        self.budget -= self.cost
        return self.cost