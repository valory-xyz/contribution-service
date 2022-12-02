# Internal audit of contribution-service (tag: v0.1.0-pre-audit)

This is the first internal audit. <br>

The review has been performed based on the contract code in the following repository:<br>
https://github.com/valory-xyz/contribution-service <br>
commit: `f0f33622d1e3c3598d38091626de8a60cc1d5c1f`  or `tag: v0.1.0-pre-audit`

## Objectives
The audit is focused on [packages/balancer](https://github.com/valory-xyz/contribution-service/tree/main/packages/valory/) in this repo.

## Checks on quick start guides
These checks were made on the basis of the following existing documentation:
  - https://github.com/valory-xyz/contribution-service/README.md

```
- Pull pre-built images:

      docker pull valory/autonolas-registries:latest
      docker pull valory/safe-contract-net:latest
# ok

- Create development environment:

      make new_env && pipenv shell
# ok
- Configure command line:

      autonomy init --reset --author valory --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"
# ok
autonomy packages sync --update-packages
# ok
make formatters
# ok
make code-checks
# ok
make security
# ok
make generators
# ok
make common-checks-1
# ok
gitleaks detect --report-format json --report-path leak_report
# ok
tox -e py3.10 -- -m 'not e2e'
...

---------- coverage: platform linux, python 3.10.6-final-0 -----------
Name                                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------------------
packages/valory/skills/dynamic_nft_abci/__init__.py                       3      0   100%
packages/valory/skills/dynamic_nft_abci/behaviours.py                   312     79    75%   485-598, 602-642, 650-665, 677-704, 764-773
packages/valory/skills/dynamic_nft_abci/dialogues.py                     34      0   100%
packages/valory/skills/dynamic_nft_abci/handlers.py                      70      2    97%   102-105
packages/valory/skills/dynamic_nft_abci/io_/__init__.py                   1      0   100%
packages/valory/skills/dynamic_nft_abci/io_/load.py                      17      0   100%
packages/valory/skills/dynamic_nft_abci/io_/store.py                     31      0   100%
packages/valory/skills/dynamic_nft_abci/models.py                        28      0   100%
packages/valory/skills/dynamic_nft_abci/payloads.py                      33      0   100%
packages/valory/skills/dynamic_nft_abci/rounds.py                       128      0   100%
packages/valory/skills/dynamic_nft_abci/tests/__init__.py                 1      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py        276     69    75%   72-74, 672, 728-762, 771-826, 842, 861-862, 886-920, 929-972
packages/valory/skills/dynamic_nft_abci/tests/test_dialogues.py          17      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_dummy_e2e.py           5      1    80%   27
packages/valory/skills/dynamic_nft_abci/tests/test_handlers.py           80      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/__init__.py         1      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/conftest.py        13      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/test_load.py       40      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/test_store.py      34      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_models.py              6      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_payloads.py           17      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_rounds.py             80      0   100%
packages/valory/skills/dynamic_nft_abci/tools.py                          2      0   100%
---------------------------------------------------------------------------------------------------
TOTAL                                                                  1229    151    88%
Coverage XML written to file coverage.xml

========================================================================================================= short test summary info ==========================================================================================================
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationErrorBehaviour::test_whitelist_error[test_case0-kwargs0] - RuntimeError: Could not start IPFS daemon.
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationErrorBehaviour::test_generation_error[test_case0] - RuntimeError: Could not start IPFS daemon.
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationErrorBehaviour::test_send_to_ipfs_error - RuntimeError: Could not start IPFS daemon.
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationBehaviour::test_run_redownload_layers - RuntimeError: Could not start IPFS daemon.
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationBehaviour::test_run[test_case0-kwargs0] - RuntimeError: Could not start IPFS daemon.
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationBehaviour::test_run[test_case2-kwargs2] - RuntimeError: Could not start IPFS daemon.
ERROR packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py::TestImageGenerationBehaviour::test_run[test_case1-kwargs1] - RuntimeError: Could not start IPFS daemon.
=============================================================================================== 57 passed, 1 deselected, 7 errors in 31.66s ================================================================================================
ERROR: InvocationError for command /home/andrey/valory/contribution-service/.tox/py3.10/bin/pytest -rfE --doctest-modules packages/valory/skills/dynamic_nft_abci/tests --cov=packages/valory/skills/dynamic_nft_abci --cov-report=xml --cov-report=term --cov-report=term-missing --cov-config=.coveragerc -m 'not e2e' (exited with code 1)
_________________________________________________________________________________________________________________ summary __________________________________________________________________________________________________________________
ERROR:   py3.10: commands failed
(contribution-service) andrey@v510:~/valory/contribution-service$ ipfs --version
ipfs version 0.6.0

after run:
(contribution-service) andrey@v510:~/valory/contribution-service$ ipfs init

fixed:
tox -e py3.10 -- -m 'not e2e'
...
---------- coverage: platform linux, python 3.10.6-final-0 -----------
Name                                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------------------
packages/valory/skills/dynamic_nft_abci/__init__.py                       3      0   100%
packages/valory/skills/dynamic_nft_abci/behaviours.py                   312     23    93%   602-642, 650-665, 678, 700-701
packages/valory/skills/dynamic_nft_abci/dialogues.py                     34      0   100%
packages/valory/skills/dynamic_nft_abci/handlers.py                      70      2    97%   102-105
packages/valory/skills/dynamic_nft_abci/io_/__init__.py                   1      0   100%
packages/valory/skills/dynamic_nft_abci/io_/load.py                      17      0   100%
packages/valory/skills/dynamic_nft_abci/io_/store.py                     31      0   100%
packages/valory/skills/dynamic_nft_abci/models.py                        28      0   100%
packages/valory/skills/dynamic_nft_abci/payloads.py                      33      0   100%
packages/valory/skills/dynamic_nft_abci/rounds.py                       128      0   100%
packages/valory/skills/dynamic_nft_abci/tests/__init__.py                 1      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py        276      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_dialogues.py          17      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_dummy_e2e.py           5      1    80%   27
packages/valory/skills/dynamic_nft_abci/tests/test_handlers.py           80      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/__init__.py         1      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/conftest.py        13      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/test_load.py       40      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/test_store.py      34      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_models.py              6      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_payloads.py           17      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_rounds.py             80      0   100%
packages/valory/skills/dynamic_nft_abci/tools.py                          2      0   100%
---------------------------------------------------------------------------------------------------
TOTAL                                                                  1229     26    98%
Coverage XML written to file coverage.xml

==================================================================================================== 64 passed, 1 deselected in 31.20s =====================================================================================================
_________________________________________________________________________________________________________________ summary __________________________________________________________________________________________________________________
  py3.10: commands succeeded
  congratulations :)


tox -e py3.10 -- -m 'e2e'
packages/valory/skills/dynamic_nft_abci/tests/test_dummy_e2e.py::test_dummy_e2e PASSED                                                                                                                                               [100%]

---------- coverage: platform linux, python 3.10.6-final-0 -----------
Name                                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------------------
packages/valory/skills/dynamic_nft_abci/__init__.py                       3      0   100%
packages/valory/skills/dynamic_nft_abci/behaviours.py                   312    234    25%   80, 85, 90, 101-146, 150-162, 173-196, 205-294, 304-313, 323-351, 368-411, 423-443, 456-467, 485-598, 602-642, 650-665, 677-704, 718-726, 730, 745-773, 791-811
packages/valory/skills/dynamic_nft_abci/dialogues.py                     34      4    88%   94-107
packages/valory/skills/dynamic_nft_abci/handlers.py                      70     37    47%   79, 97-107, 115-141, 152-162, 172-210, 221-233
packages/valory/skills/dynamic_nft_abci/io_/__init__.py                   1      0   100%
packages/valory/skills/dynamic_nft_abci/io_/load.py                      17      5    71%   49-50, 66-69
packages/valory/skills/dynamic_nft_abci/io_/store.py                     31      6    81%   69-75, 90-92
packages/valory/skills/dynamic_nft_abci/models.py                        28     15    46%   40, 48-67
packages/valory/skills/dynamic_nft_abci/payloads.py                      33      2    94%   54, 59
packages/valory/skills/dynamic_nft_abci/rounds.py                       128     59    54%   68, 73, 78, 83, 88, 97, 112-143, 160-174, 189-199, 212-231, 244-271
packages/valory/skills/dynamic_nft_abci/tests/__init__.py                 1      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_behaviours.py        276    132    52%   69-74, 233-235, 239-240, 245-251, 259-263, 281, 316-322, 351-357, 386-403, 471-488, 512-532, 544, 571-588, 611-612, 629, 638-659, 672, 728-762, 771-826, 842, 861-862, 886-920, 929-972, 996-997, 1005-1007, 1013, 1017, 1021-1022
packages/valory/skills/dynamic_nft_abci/tests/test_dialogues.py          17      5    71%   45-46, 52-62
packages/valory/skills/dynamic_nft_abci/tests/test_dummy_e2e.py           5      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_handlers.py           80     46    42%   72-94, 109-110, 115-134, 163-214, 222-267, 274-275
packages/valory/skills/dynamic_nft_abci/tests/test_io/__init__.py         1      0   100%
packages/valory/skills/dynamic_nft_abci/tests/test_io/conftest.py        13      2    85%   37, 50
packages/valory/skills/dynamic_nft_abci/tests/test_io/test_load.py       40     24    40%   70-82, 96-148
packages/valory/skills/dynamic_nft_abci/tests/test_io/test_store.py      34     18    47%   69-83, 98-113
packages/valory/skills/dynamic_nft_abci/tests/test_models.py              6      1    83%   33
packages/valory/skills/dynamic_nft_abci/tests/test_payloads.py           17      5    71%   80-84
packages/valory/skills/dynamic_nft_abci/tests/test_rounds.py             80      8    90%   205-212, 276, 323, 356, 401, 437
packages/valory/skills/dynamic_nft_abci/tools.py                          2      0   100%
---------------------------------------------------------------------------------------------------
TOTAL                                                                  1229    603    51%
Coverage XML written to file coverage.xml


===================================================================================================== 1 passed, 64 deselected in 1.05s =====================================================================================================
_________________________________________________________________________________________________________________ summary __________________________________________________________________________________________________________________
  py3.10: commands succeeded
  congratulations :)

```
Conclusions: <br>
Everything generally works as described in the file https://github.com/valory-xyz/contribution-service/README.md <br>
Not 100% coverage is a minor issue. <br>
It would be good to pay attention to lines of code not covered by tests. <br>

### Review of diagram. Possible attack vectors
WIP

### Review of `packages/valory/`
A quick code review with short notes for each file in the project can be found in the file <br>
packages/balancer: [packages_valory.md](packages_valory.md).


Update: 02-12-22. <br>
* So far, the code has been reviewed up to
```

├── contracts (WIP)
│   ├── dynamic_contribution
```
