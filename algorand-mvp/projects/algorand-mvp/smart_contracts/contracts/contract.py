from algopy import *
from algopy.arc4 import *


class Contracts(ARC4Contract):

    # Global state
    counter = GlobalState(UInt64)
    total_calls = GlobalState(UInt64)

    # Local state (per user)
    user_calls = LocalState(UInt64)

    # Create method (runs on deploy)
    @abimethod(create=True)
    def create(self) -> None:
        self.counter = UInt64(0)
        self.total_calls = UInt64(0)

    # User opt-in (required before using local state)
    @abimethod()
    def opt_in(self) -> None:
        self.user_calls[Txn.sender] = UInt64(0)

    # State-changing method
    @abimethod()
    def increment(self) -> None:
        sender = Txn.sender

        self.counter = self.counter + UInt64(1)
        self.total_calls = self.total_calls + UInt64(1)
        self.user_calls[sender] = self.user_calls[sender] + UInt64(1)

    # Read-only methods
    @abimethod(readonly=True)
    def get_counter(self) -> UInt64:
        return self.counter

    @abimethod(readonly=True)
    def get_total_calls(self) -> UInt64:
        return self.total_calls

    @abimethod(readonly=True)
    def get_user_calls(self, user: Address) -> UInt64:
        return self.user_calls[user]

    # Reset method
    @abimethod()
    def reset_counter(self) -> None:
        self.counter = UInt64(0)