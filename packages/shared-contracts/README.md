# shared-contracts

Canonical, language-neutral definition of the **Agent ⇄ Server** protocol and the
core domain shapes shared by every app.

* `protocol.json` — human-readable spec (the source of truth for reviewers).
* `python/lw_contracts/` — installable Python package (`lw-contracts`) with Pydantic
  models + enums. Imported by **backend** and **player-agent**.
* `typescript/contracts.ts` — TypeScript mirror imported by the **mini-app**.

When you change a message shape, update **all three**. The Python models are the
runtime-validated ones; the JSON and TS are kept in lock-step by review.
