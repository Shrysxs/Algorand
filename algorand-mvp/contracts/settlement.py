from algopy import ARC4Contract, UInt64
from algopy.arc4 import abimethod


class SettlementContract(ARC4Contract):

    @abimethod(create="require")
    def create(self, publisher_bps: UInt64) -> None:
        self.publisher_bps = publisher_bps

    @abimethod()
    def settle(self, amount: UInt64) -> UInt64:
        return (amount * self.publisher_bps) // UInt64(10_000)