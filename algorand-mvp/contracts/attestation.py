"""GhostGas attestation registry contract."""

from algopy import *
from algopy.arc4 import *


class AttestationContract(ARC4Contract):
    """Stores one-time ad-watch attestations to block replay + enable validation."""

    admin = GlobalState(Account)
    verifier = GlobalState(Account)


    attestations = BoxMap(String, UInt64, key_prefix="att")


    settlement = GlobalState(UInt64)

    @abimethod(create=True)
    def create(self, verifier: Account) -> None:
        self.admin.value = Txn.sender
        self.verifier.value = verifier
        self.settlement.value = UInt64(0)

    @abimethod()
    def set_verifier(self, verifier: Account) -> None:
        assert Txn.sender == self.admin.value, "only admin"
        self.verifier.value = verifier

    @abimethod()
    def set_settlement(self, app_id: UInt64) -> None:
        """Optional: restrict who can consume attestations"""
        assert Txn.sender == self.admin.value, "only admin"
        self.settlement.value = app_id


    @abimethod()
    def record_attestation(self, proof_id: String, observed_at: UInt64) -> None:
        assert Txn.sender == self.verifier.value, "only verifier"
        assert observed_at > UInt64(0), "invalid timestamp"

        # prevent replay
        _, exists = self.attestations.maybe(proof_id)
        assert not exists, "already recorded"

        self.attestations[proof_id] = observed_at


    @abimethod()
    def consume_attestation(self, proof_id: String) -> UInt64:
        """Returns 1 if valid and deletes it (one-time use)."""

        # optional restriction
        if self.settlement.value != UInt64(0):
            assert Txn.sender.application_id() == self.settlement.value, "only settlement"

        val, exists = self.attestations.maybe(proof_id)
        assert exists, "invalid proof"


        del self.attestations[proof_id]

        return UInt64(1)

    @abimethod(readonly=True)
    def is_valid_attestation(self, proof_id: String) -> UInt64:
        _, exists = self.attestations.maybe(proof_id)
        return UInt64(1) if exists else UInt64(0)