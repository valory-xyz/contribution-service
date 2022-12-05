```
.
├── agents
│   ├── contribution (ok)
│   │   ├── aea-config.yaml
│   │   ├── __init__.py
│   │   └── tests
│   │       ├── helpers
│   │       │   ├── constants.py
│   │       │   ├── data
│   │       │   │   └── json_server
│   │       │   │       └── data.json
│   │       │   ├── docker.py
│   │       │   ├── fixtures.py
│   │       │   └── __init__.py
│   │       ├── __init__.py
│   │       └── test_contribution.py
│   └── __init__.py
├── connections (out of scope)

├── contracts (WIP)
│   ├── dynamic_contribution
│   │   ├── build
│   │   │   └── DynamicContribution.json
│   │   ├── contract.py
get_all_erc721_transfers()
https://github.com/transmissions11/solmate/blob/8d910d876f51c3b2585c9109409d601f600e68e1/src/tokens/ERC721.sol#L11
so, factory_contract.events.Transfer.createFilter(... "from": from_address) is correct.

maybe these ideas will be useful
https://coinsbench.com/web3-py-fetching-all-transfer-events-on-single-tokens-from-a-given-timestamp-90bd6ec08e33
https://ethereum.stackexchange.com/questions/87676/infura-returns-strange-error-query-returned-more-than-10000-results
https://community.infura.io/t/getlogs-error-query-returned-more-than-1000-results/358/4
│   │   └── __init__.py
│   │   ├── contract.yaml
│   │   └── __init__.py
│   ├── __init__.py
│   └── service_registry (out of scope)
...
├── __init__.py
├── protocols (out of scope)
...
├── services (ok, no codebase)
│   └── contribution
│       ├── README.md
│       └── service.yaml
└── skills
    ├── abstract_abci (out of scope)
...
    ├── abstract_round_abci (out of scope)
...
    ├── contribution_skill_abci
    │   ├── behaviours.py (ok)
    │   ├── composition.py (ok)
    │   ├── dialogues.py (ok)
    │   ├── fsm_specification.yaml 
    │   ├── handlers.py (ok)
    │   ├── __init__.py
    │   ├── models.py (ok)
    │   ├── skill.yaml
    │   └── tests (ok)
    │       ├── __init__.py
    │       ├── test_behaviours.py
    │       ├── test_dialogues.py
    │       ├── test_handlers.py
    │       └── test_models.py

    ├── dynamic_nft_abci
    │   ├── behaviours.py
    │   ├── data
    │   │   └── layers
    │   │       ├── classes
    │   │       │   └── 0.png
    │   │       └── frames
    │   │           ├── 0.png
    │   │           ├── 1.png
    │   │           ├── 2.png
    │   │           └── 3.png
    │   ├── dialogues.py
    │   ├── fsm_specification.yaml
    │   ├── handlers.py
    │   ├── __init__.py
    │   ├── io_
    │   │   ├── __init__.py
    │   │   ├── load.py
    │   │   └── store.py
    │   ├── models.py
    │   ├── payloads.py
    │   ├── rounds.py
    │   ├── skill.yaml
    │   ├── tests
    │   │   ├── __init__.py
    │   │   ├── test_behaviours.py
    │   │   ├── test_dialogues.py
    │   │   ├── test_dummy_e2e.py
    │   │   ├── test_handlers.py
    │   │   ├── test_io
    │   │   │   ├── conftest.py
    │   │   │   ├── __init__.py
    │   │   │   ├── test_load.py
    │   │   │   └── test_store.py
    │   │   ├── test_models.py
    │   │   ├── test_payloads.py
    │   │   └── test_rounds.py
    │   └── tools.py
    ├── __init__.py
    ├── registration_abci
    │   ├── behaviours.py
    │   ├── dialogues.py
    │   ├── fsm_specification.yaml
    │   ├── handlers.py
    │   ├── __init__.py
    │   ├── models.py
    │   ├── payloads.py
    │   ├── README.md
    │   ├── rounds.py
    │   ├── skill.yaml
    │   └── tests
    │       ├── __init__.py
    │       ├── test_behaviours.py
    │       ├── test_dialogues.py
    │       ├── test_handlers.py
    │       ├── test_models.py
    │       ├── test_payloads.py
    │       └── test_rounds.py
    └── reset_pause_abci
        ├── behaviours.py
        ├── dialogues.py
        ├── fsm_specification.yaml
        ├── handlers.py
        ├── __init__.py
        ├── models.py
        ├── payloads.py
        ├── README.md
        ├── rounds.py
        ├── skill.yaml
        └── tests
            ├── __init__.py
            ├── test_behaviours.py
            ├── test_dialogues.py
            ├── test_handlers.py
            ├── test_payloads.py
            └── test_rounds.py

76 directories, 297 files
```
