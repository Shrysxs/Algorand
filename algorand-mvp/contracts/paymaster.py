from algopy import ARC4Contract, UInt64
from algopy.arc4 import abimethod


class PaymasterContract(ARC4Contract):

    @abimethod(create="require")
    def create(self) -> None:
        self.balance = UInt64(0)

    @abimethod()
    def fund(self, amount: UInt64) -> None:
        self.balance += amount

    @abimethod()
    def sponsor(self, amount: UInt64) -> None:
        assert self.balance >= amount
        self.balance -= amount