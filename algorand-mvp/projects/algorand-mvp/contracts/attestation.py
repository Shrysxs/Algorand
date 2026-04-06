"""GhostGas attestation registry contract."""

from algopy import Account, BoxMap, GlobalState, Txn, UInt64
from algopy.arc4 import ARC4Contract, String, abimethod


class AttestationContract(ARC4Contract):
    """Stores one-time ad-watch attestations to block replay."""

    admin = GlobalState(Account, description="Controls verifier rotation")
    verifier = GlobalState(Account, description="Off-chain attestation signer/relayer")
    # Key format: "{wallet}:{ad_id}:{unix_ts}" to keep it deterministic.
    attestations = BoxMap(String, UInt64, key_prefix="att")

    @abimethod(create=True)
    def create(self, verifier: Account) -> None:
        self.admin.value = Txn.sender
        self.verifier.value = verifier

    @abimethod()
    def set_verifier(self, verifier: Account) -> None:
        assert Txn.sender == self.admin.value, "only admin"
        self.verifier.value = verifier

    @abimethod()
    def record_attestation(self, proof_id: String, observed_at: UInt64) -> None:
        assert Txn.sender == self.verifier.value, "only verifier"
        assert observed_at > UInt64(0), "invalid timestamp"
        assert proof_id not in self.attestations, "proof already exists"
        self.attestations[proof_id] = observed_at

    @abimethod(readonly=True)
    def is_valid_attestation(self, proof_id: String) -> UInt64:
        _, exists = self.attestations.maybe(proof_id)
        return UInt64(1) if exists else UInt64(0)
