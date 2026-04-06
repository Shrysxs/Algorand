"""GhostGas settlement coordinator contract."""

from algopy import *
from algopy.arc4 import ARC4Contract, String, abimethod


class SettlementContract(ARC4Contract):

    admin = GlobalState(Account)
    oracle = GlobalState(Account)

    publisher_bps = GlobalState(UInt64)
    gas_pool_bps = GlobalState(UInt64)

    total_settled = GlobalState(UInt64)

    attestation_app = GlobalState(UInt64)
    paymaster_app = GlobalState(UInt64)

    settled_proofs = BoxMap(String, UInt64, key_prefix="stl")

    @abimethod(create=True)
    def create(
        self,
        oracle: Account,
        publisher_bps: UInt64,
        gas_pool_bps: UInt64,
        attestation_app: UInt64,
        paymaster_app: UInt64,
    ) -> None:

        assert publisher_bps + gas_pool_bps == UInt64(10_000)

        self.admin.value = Txn.sender
        self.oracle.value = oracle

        self.publisher_bps.value = publisher_bps
        self.gas_pool_bps.value = gas_pool_bps

        self.attestation_app.value = attestation_app
        self.paymaster_app.value = paymaster_app

        self.total_settled.value = UInt64(0)

    @abimethod()
    def set_oracle(self, oracle: Account) -> None:
        assert Txn.sender == self.admin.value
        self.oracle.value = oracle

    @abimethod()
    def set_splits(self, publisher_bps: UInt64, gas_pool_bps: UInt64) -> None:
        assert Txn.sender == self.admin.value
        assert publisher_bps + gas_pool_bps == UInt64(10_000)

        self.publisher_bps.value = publisher_bps
        self.gas_pool_bps.value = gas_pool_bps

    @abimethod()
    def settle_impression(
        self,
        proof_id: String,
        campaign_app: UInt64,
        publisher: Account,
        user: Account,
        now_ts: UInt64,
    ) -> None:

        assert Txn.sender == self.oracle.value

        # replay protection
        _, exists = self.settled_proofs.maybe(proof_id)
        assert not exists

        # verify + consume attestation
        attestation = Application(self.attestation_app.value)
        assert attestation.call("consume_attestation", proof_id) == UInt64(1)

        # deduct from campaign
        campaign = Application(campaign_app)
        amount = campaign.call("deduct_for_impression", UInt64(0), String(""))

        # split
        publisher_amount = (amount * self.publisher_bps.value) // UInt64(10_000)
        gas_pool_amount = amount - publisher_amount

        # pay publisher
        InnerTxnBuilder.Begin()
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.asset_receiver: publisher,
            TxnField.asset_amount: publisher_amount,
        })
        InnerTxnBuilder.Submit()

        # fund paymaster
        paymaster = Application(self.paymaster_app.value)
        paymaster.call("fund", gas_pool_amount)

        # grant sponsorship
        paymaster.call("grant_sponsorship", user, now_ts)

        self.settled_proofs[proof_id] = amount
        self.total_settled.value = self.total_settled.value + amount

    @abimethod(readonly=True)
    def is_settled(self, proof_id: String) -> UInt64:
        _, exists = self.settled_proofs.maybe(proof_id)
        return UInt64(1) if exists else UInt64(0)