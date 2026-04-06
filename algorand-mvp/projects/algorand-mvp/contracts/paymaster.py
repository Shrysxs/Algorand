"""GhostGas paymaster (gas sponsorship eligibility) contract."""

from algopy import Account, BoxMap, GlobalState, Txn, UInt64
from algopy.arc4 import ARC4Contract, String, abimethod


class PaymasterContract(ARC4Contract):
    """Tracks user sponsorship windows and usage limits."""

    admin = GlobalState(Account, description="Contract administrator")
    settlement_executor = GlobalState(Account, description="Entity that grants/consumes sponsorship")
    usage_window_seconds = GlobalState(UInt64, description="Eligibility duration after attestation")
    max_uses_per_window = GlobalState(UInt64, description="Cap to prevent abuse")
    # Key: wallet address string, Value: expiration unix timestamp.
    eligibility_expiry = BoxMap(String, UInt64, key_prefix="exp")
    # Key: wallet address string, Value: uses consumed in current window.
    user_uses = BoxMap(String, UInt64, key_prefix="uses")

    @abimethod(create=True)
    def create(self, settlement_executor: Account, usage_window_seconds: UInt64, max_uses_per_window: UInt64) -> None:
        assert usage_window_seconds > UInt64(0), "invalid window"
        assert max_uses_per_window > UInt64(0), "invalid limit"
        self.admin.value = Txn.sender
        self.settlement_executor.value = settlement_executor
        self.usage_window_seconds.value = usage_window_seconds
        self.max_uses_per_window.value = max_uses_per_window

    @abimethod()
    def set_settlement_executor(self, settlement_executor: Account) -> None:
        assert Txn.sender == self.admin.value, "only admin"
        self.settlement_executor.value = settlement_executor

    @abimethod()
    def grant_sponsorship(self, user_wallet: String, now_ts: UInt64) -> UInt64:
        assert Txn.sender == self.settlement_executor.value, "only settlement"
        assert now_ts > UInt64(0), "invalid timestamp"
        expiry = now_ts + self.usage_window_seconds.value
        self.eligibility_expiry[user_wallet] = expiry
        self.user_uses[user_wallet] = UInt64(0)
        return expiry

    @abimethod()
    def consume_sponsorship(self, user_wallet: String, now_ts: UInt64) -> UInt64:
        assert Txn.sender == self.settlement_executor.value, "only settlement"
        expiry, has_expiry = self.eligibility_expiry.maybe(user_wallet)
        assert has_expiry, "not eligible"
        assert now_ts <= expiry, "window expired"
        uses = self.user_uses.get(user_wallet, default=UInt64(0))
        assert uses < self.max_uses_per_window.value, "usage exhausted"
        next_uses = uses + UInt64(1)
        self.user_uses[user_wallet] = next_uses
        return next_uses

    @abimethod(readonly=True)
    def is_eligible(self, user_wallet: String, now_ts: UInt64) -> UInt64:
        expiry, has_expiry = self.eligibility_expiry.maybe(user_wallet)
        if not has_expiry:
            return UInt64(0)
        uses = self.user_uses.get(user_wallet, default=UInt64(0))
        if now_ts > expiry:
            return UInt64(0)
        if uses >= self.max_uses_per_window.value:
            return UInt64(0)
        return UInt64(1)
