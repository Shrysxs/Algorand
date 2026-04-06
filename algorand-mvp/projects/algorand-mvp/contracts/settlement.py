"""GhostGas settlement coordinator contract.

This contract records settlement outcomes after an off-chain verifier confirms ad watch events.
"""

from algopy import Account, BoxMap, GlobalState, Txn, UInt64
from algopy.arc4 import ARC4Contract, String, abimethod


class SettlementContract(ARC4Contract):
    """Calculates publisher and gas pool splits for each valid impression."""

    admin = GlobalState(Account, description="Config owner")
    oracle = GlobalState(Account, description="Trusted ad-watch verifier")
    publisher_bps = GlobalState(UInt64, description="Publisher split in basis points")
    gas_pool_bps = GlobalState(UInt64, description="Gas sponsorship split in basis points")
    total_settled = GlobalState(UInt64, description="Total amount settled")
    # Key: proof_id, Value: amount settled for this proof.
    settled_proofs = BoxMap(String, UInt64, key_prefix="stl")

    @abimethod(create=True)
    def create(self, oracle: Account, publisher_bps: UInt64, gas_pool_bps: UInt64) -> None:
        assert publisher_bps + gas_pool_bps == UInt64(10_000), "invalid split"
        self.admin.value = Txn.sender
        self.oracle.value = oracle
        self.publisher_bps.value = publisher_bps
        self.gas_pool_bps.value = gas_pool_bps
        self.total_settled.value = UInt64(0)

    @abimethod()
    def set_oracle(self, oracle: Account) -> None:
        assert Txn.sender == self.admin.value, "only admin"
        self.oracle.value = oracle

    @abimethod()
    def set_splits(self, publisher_bps: UInt64, gas_pool_bps: UInt64) -> None:
        assert Txn.sender == self.admin.value, "only admin"
        assert publisher_bps + gas_pool_bps == UInt64(10_000), "invalid split"
        self.publisher_bps.value = publisher_bps
        self.gas_pool_bps.value = gas_pool_bps

    @abimethod()
    def settle_impression(
        self,
        proof_id: String,
        campaign_charge: UInt64,
    ) -> tuple[UInt64, UInt64]:
        """Stores a deterministic split for one already-verified proof."""
        assert Txn.sender == self.oracle.value, "only oracle"
        assert proof_id not in self.settled_proofs, "proof already settled"
        assert campaign_charge > UInt64(0), "invalid charge"

        publisher_amount = (campaign_charge * self.publisher_bps.value) // UInt64(10_000)
        gas_pool_amount = campaign_charge - publisher_amount

        self.settled_proofs[proof_id] = campaign_charge
        self.total_settled.value = self.total_settled.value + campaign_charge
        return publisher_amount, gas_pool_amount

    @abimethod(readonly=True)
    def is_settled(self, proof_id: String) -> UInt64:
        _, exists = self.settled_proofs.maybe(proof_id)
        return UInt64(1) if exists else UInt64(0)
