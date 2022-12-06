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
...
├── contracts (WIP)
│   ├── dynamic_contribution
│   │   ├── build
│   │   │   └── DynamicContribution.json
│   │   ├── contract.py
get_all_erc721_transfers()
_mint() { // implemented
...
emit Transfer(address(0), to, id);
}

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
def get_member_to_token_id(self) -> Generator[None, None, dict]:
        """Get member to token id data."""
        contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.params.dynamic_contribution_contract_address,
            contract_id=str(DynamicContributionContract.contract_id),
            contract_callable="get_all_erc721_transfers",
            from_address=NULL_ADDRESS,
        )
Transfer(address(0), to, id); => correct
Keep in mind that you can always know in advance the block in which the contract is created. 
Example: https://etherscan.io/tx/0x4da20a09b78d6c3d04489f464b9fd98e0f09c59bbb60e74e44c46c1cb8a58c81
Block: 16097553
Timestamp: Dec-02-2022 01:54:35 PM +UTC
This idea was implemented in the revisions following the commit being checked.
+ from_block=self.params.earliest_block_to_monitor,
https://github.com/valory-xyz/contribution-service/commit/2aa2c0b4e22f2d0c7fe81a8eb2105c386b46170e
    │   ├── data
    │   │   └── layers
    │   │       ├── classes
    │   │       │   └── 0.png
    │   │       └── frames
    │   │           ├── 0.png
    │   │           ├── 1.png
    │   │           ├── 2.png
    │   │           └── 3.png
    │   ├── dialogues.py (ok)
    │   ├── fsm_specification.yaml
    │   ├── handlers.py (ok)
    │   ├── __init__.py
    │   ├── io_ (ok)
    │   │   ├── __init__.py
    │   │   ├── load.py
    │   │   └── store.py
    │   ├── models.py (ok)
    │   ├── payloads.py (ok)
    │   ├── rounds.py (ok)
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
    │   └── tools.py (ok)
    ├── __init__.py
    ├── registration_abci (out of scope)
...
76 directories, 297 files
```
