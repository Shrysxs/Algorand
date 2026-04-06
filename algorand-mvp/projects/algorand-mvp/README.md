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
  - ASA-backed campaign budget (USDC or custom ASA)
  - Secure deposit via group transactions
  - Deducts spend for verified impressions only

- `contracts/attestation.py`
  - Stores one-time ad-watch proofs
  - Replay-safe via consume pattern

- `contracts/settlement.py`
  - Core execution engine
  - Verifies attestation, deducts campaign, splits funds
  - Routes funds to publisher and paymaster
  - Grants sponsorship eligibility

- `contracts/paymaster.py`
  - Holds gas sponsorship funds (ASA)
  - Tracks eligibility window and usage caps
  - Sponsors user transactions via asset transfer

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

1. Advertiser creates campaign and deposits ASA (USDC) into CampaignContract
2. User watches an ad inside a publisher dApp
3. Off-chain verifier records proof in AttestationContract
4. Oracle calls SettlementContract with proof_id
5. SettlementContract:
   - consumes attestation
   - deducts campaign budget
   - splits funds (publisher + paymaster)
   - funds PaymasterContract
   - grants user sponsorship eligibility
6. User receives sponsored balance and can submit transactions

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

