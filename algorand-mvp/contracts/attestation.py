"""GhostGas attestation registry contract (FIXED)."""

from algopy import *
from algopy.arc4 import *


class AttestationContract(ARC4Contract):

    admin = GlobalState(Account)
    verifier = GlobalState(Account)

    attestations = BoxMap(String, UInt64, key_prefix="att")

    settlement = GlobalState(UInt64)

    EXPIRY_WINDOW = UInt64(300)  # 5 min

    @abimethod(create=True)
    def create(self, verifier: Account) -> None:
        self.admin.value = Txn.sender
        self.verifier.value = verifier
        self.settlement.value = UInt64(0)

    @abimethod()
    def set_verifier(self, verifier: Account) -> None:
        assert Txn.sender == self.admin.value
        self.verifier.value = verifier

    @abimethod()
    def set_settlement(self, app_id: UInt64) -> None:
        assert Txn.sender == self.admin.value
        self.settlement.value = app_id

    @abimethod()
    def record_attestation(self, proof_id: String, observed_at: UInt64) -> None:
        assert Txn.sender == self.verifier.value
        assert observed_at > UInt64(0)

        _, exists = self.attestations.maybe(proof_id)
        assert not exists

        self.attestations[proof_id] = observed_at

    @abimethod()
    def consume_attestation(self, proof_id: String) -> UInt64:

        if self.settlement.value != UInt64(0):
            assert Txn.sender.application_id() == self.settlement.value

        observed_at, exists = self.attestations.maybe(proof_id)
        assert exists

        # 🔥 expiry check
        assert Global.latest_timestamp() - observed_at <= self.EXPIRY_WINDOW

        del self.attestations[proof_id]

        return UInt64(1)

    @abimethod(readonly=True)
    def is_valid_attestation(self, proof_id: String) -> UInt64:
        _, exists = self.attestations.maybe(proof_id)
        return UInt64(1) if exists else UInt64(0)