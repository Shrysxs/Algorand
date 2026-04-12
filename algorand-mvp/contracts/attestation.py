from algopy import ARC4Contract, UInt64, String
from algopy.arc4 import abimethod


class AttestationContract(ARC4Contract):

    @abimethod(create="require")
    def create(self) -> None:
        pass

    @abimethod()
    def verify(self, proof_id: String) -> UInt64:
        return UInt64(1)