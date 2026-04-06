# GhostGas (Algorand MVP)

Production-oriented modular contract scaffold for GhostGas, a decentralized ad network where:
- advertisers fund campaigns
- ad impressions are verified
- settlement splits are recorded trustlessly
- gas sponsorship eligibility is managed on-chain

## 1) Folder Structure

```text
.
├── contracts/
│   ├── campaign.py
│   ├── attestation.py
│   ├── settlement.py
│   └── paymaster.py
├── scripts/
│   └── deploy.py
├── tests/
├── utils/
│   └── constants.py
└── config/
    └── networks.py
```

## 2) Smart Contracts

- `contracts/campaign.py`
  - Campaign budget, targeting, CPI, pause/resume state
  - Deducts spend for verified impressions only
  - Security: advertiser-only config, settlement-executor-only deductions

- `contracts/attestation.py`
  - Stores immutable watch proofs in box storage
  - Security: verifier-only writes, replay protection by `proof_id`

- `contracts/settlement.py`
  - Applies deterministic revenue splits in basis points
  - Security: oracle-only settlement, one-time settlement per proof

- `contracts/paymaster.py`
  - Tracks user eligibility windows and spend caps
  - Security: settlement-only grant/consume, usage cap and expiry checks

## 3) Deployment Scripts and AlgoKit Setup

### LocalNet setup

1. Install dependencies:
   - `poetry install`
2. Bootstrap env files:
   - `algokit generate env-file -a target_network localnet`
3. Start local network:
   - `algokit localnet start`
4. Compile all GhostGas contracts:
   - `poetry run python scripts/deploy.py`

### Deployment entry point

- `scripts/deploy.py`
  - Compiles each contract with `algokit compile python`
  - Generates typed clients with `algokit generate client`
  - Writes artifacts to `artifacts/ghostgas/<contract_name>/`

## 4) Example Flow

1. Advertiser creates campaign and deposits budget in `CampaignContract`
2. User watches an ad
3. Off-chain verifier records proof in `AttestationContract`
4. Settlement oracle settles impression in `SettlementContract`
5. Settlement executor deducts campaign budget and grants user eligibility in `PaymasterContract`
6. User submits sponsored transaction while within eligibility window and usage cap

## 5) Testing Strategy

### Unit tests
- Contract state transitions (create/configure/pause/resume)
- Split math correctness for settlement
- Eligibility window and usage counter behavior
- Attestation uniqueness and replay prevention

### Edge-case tests
- Double claim using identical `proof_id` is rejected
- Replay settlement for same `proof_id` is rejected
- Campaign deduction fails on insufficient budget
- Sponsorship consume fails when expired or usage exhausted
- Unauthorized sender checks on every privileged endpoint

