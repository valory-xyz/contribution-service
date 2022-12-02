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
│   │   ├── contract.yaml
│   │   └── __init__.py
│   ├── __init__.py
│   └── service_registry
│       ├── build
│       │   └── ServiceRegistry.json
│       ├── contract.py
│       ├── contract.yaml
│       ├── __init__.py
│       └── tests
│           ├── __init__.py
│           └── test_contract.py
├── __init__.py
├── protocols
│   ├── abci
│   │   ├── abci_pb2.py
│   │   ├── abci.proto
│   │   ├── custom_types.py
│   │   ├── dialogues.py
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── protocol.yaml
│   │   ├── README.md
│   │   ├── serialization.py
│   │   └── tests
│   │       ├── conftest.py
│   │       ├── __init__.py
│   │       └── test_abci.py
│   ├── acn
│   │   ├── acn_pb2.py
│   │   ├── acn.proto
│   │   ├── custom_types.py
│   │   ├── dialogues.py
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── protocol.yaml
│   │   ├── README.md
│   │   ├── serialization.py
│   │   └── tests
│   │       ├── __init__.py
│   │       └── test_acn.py
│   ├── contract_api
│   │   ├── contract_api_pb2.py
│   │   ├── contract_api.proto
│   │   ├── custom_types.py
│   │   ├── dialogues.py
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── protocol.yaml
│   │   ├── README.md
│   │   ├── serialization.py
│   │   └── tests
│   │       ├── __init__.py
│   │       └── test_contract_api.py
│   ├── http
│   │   ├── dialogues.py
│   │   ├── http_pb2.py
│   │   ├── http.proto
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── protocol.yaml
│   │   ├── README.md
│   │   ├── serialization.py
│   │   └── tests
│   │       ├── __init__.py
│   │       └── test_http.py
│   ├── __init__.py
│   ├── ledger_api
│   │   ├── custom_types.py
│   │   ├── dialogues.py
│   │   ├── __init__.py
│   │   ├── ledger_api_pb2.py
│   │   ├── ledger_api.proto
│   │   ├── message.py
│   │   ├── protocol.yaml
│   │   ├── README.md
│   │   ├── serialization.py
│   │   └── tests
│   │       ├── __init__.py
│   │       └── test_ledger_api.py
│   └── tendermint
│       ├── custom_types.py
│       ├── dialogues.py
│       ├── __init__.py
│       ├── message.py
│       ├── protocol.yaml
│       ├── README.md
│       ├── serialization.py
│       ├── tendermint_pb2.py
│       └── tendermint.proto
├── services
│   └── contribution
│       ├── README.md
│       └── service.yaml
└── skills
    ├── abstract_abci
    │   ├── dialogues.py
    │   ├── handlers.py
    │   ├── __init__.py
    │   ├── README.md
    │   ├── skill.yaml
    │   └── tests
    │       ├── __init__.py
    │       ├── test_dialogues.py
    │       └── test_handlers.py
    ├── abstract_round_abci
    │   ├── abci_app_chain.py
    │   ├── base.py
    │   ├── behaviours.py
    │   ├── behaviour_utils.py
    │   ├── common.py
    │   ├── dialogues.py
    │   ├── handlers.py
    │   ├── __init__.py
    │   ├── io_
    │   │   ├── __init__.py
    │   │   ├── ipfs.py
    │   │   ├── load.py
    │   │   ├── paths.py
    │   │   └── store.py
    │   ├── models.py
    │   ├── README.md
    │   ├── serializer.py
    │   ├── skill.yaml
    │   ├── tests
    │   │   ├── data
    │   │   │   ├── dummy_abci
    │   │   │   │   ├── behaviours.py
    │   │   │   │   ├── dialogues.py
    │   │   │   │   ├── handlers.py
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── models.py
    │   │   │   │   ├── payloads.py
    │   │   │   │   ├── rounds.py
    │   │   │   │   └── skill.yaml
    │   │   │   └── __init__.py
    │   │   ├── __init__.py
    │   │   ├── test_abci_app_chain.py
    │   │   ├── test_base.py
    │   │   ├── test_base_rounds.py
    │   │   ├── test_behaviours.py
    │   │   ├── test_behaviours_utils.py
    │   │   ├── test_common.py
    │   │   ├── test_dialogues.py
    │   │   ├── test_handlers.py
    │   │   ├── test_io
    │   │   │   ├── conftest.py
    │   │   │   ├── __init__.py
    │   │   │   ├── test_ipfs.py
    │   │   │   ├── test_load.py
    │   │   │   └── test_store.py
    │   │   ├── test_models.py
    │   │   ├── test_serializer.py
    │   │   ├── test_tools
    │   │   │   ├── __init__.py
    │   │   │   ├── test_base.py
    │   │   │   ├── test_common.py
    │   │   │   ├── test_integration.py
    │   │   │   └── test_rounds.py
    │   │   └── test_utils.py
    │   ├── test_tools
    │   │   ├── abci_app.py
    │   │   ├── base.py
    │   │   ├── common.py
    │   │   ├── __init__.py
    │   │   ├── integration.py
    │   │   └── rounds.py
    │   └── utils.py
    ├── contribution_skill_abci
    │   ├── behaviours.py
    │   ├── composition.py
    │   ├── dialogues.py
    │   ├── fsm_specification.yaml
    │   ├── handlers.py
    │   ├── __init__.py
    │   ├── models.py
    │   ├── skill.yaml
    │   └── tests
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
