# Internal audit of contribution-service (tag: v0.1.0-pre-audit)

This is the first internal audit. <br>

The review has been performed based on the contract code in the following repository:<br>
https://github.com/valory-xyz/contribution-service <br>
commit: `f0f33622d1e3c3598d38091626de8a60cc1d5c1f`  or `tag: v0.1.0-pre-audit`

## Objectives
The audit is focused on [packages/valory](https://github.com/valory-xyz/contribution-service/tree/main/packages/valory/) in this repo.

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
Possible attack vectors are shown in the diagram [Contribution_Service_Diagram_Attacks](https://github.com/valory-xyz/contribution-service/tree/main/audit/Contribution_Service_Diagram_Attacks.drawio.png)

List of attack vectors: <br>
- ddos to BaseURI
- dns hijacking (details: https://www.imperva.com/learn/application-security/dns-spoofing/ )
- http/https MiTM
- MiTM in communications
- lost or stolen private key (wallet)
- lost or stolen API key

Countermeasures: <br>
- Attack #1. ddos to BaseURI
Protection at the level of the service provider. <br>
The choice of a service provider such as Amazon provides a sufficient level of protection. In the case of constant and massive attacks, can be buying an additional service. <br>
https://expertinsights.com/compare/aws-shield-vs-cloudflare-advanced-ddos-protection <br>
https://www.gartner.com/reviews/market/ddos-mitigation-services

Non-traditional way of protection: <br>
- Move metadata JSON object to IPFS. Details in Ref: List of useful links. Possibly an interesting solution.   
- Move metadata JSON to on-chain. Details in Ref: List of useful links. An very expensive solution in terms of gas. Only for networks with very cheap gas.

- Attack #2. dns hijacking 
The direct hijacking of a DNS server is only possible if an attacker gains access to accounts. Use multi-factor authentication (MFA) with each account. <br>
https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/data-protection.html

DNS spoofing. Despite its attractiveness, the technology DNSSEC is still quite controversial. <br>
https://www.infoblox.com/dns-security-resource-center/dns-security-faq/what-is-the-purpose-of-dnssec/ <br>
https://web.mit.edu/6.033/www/papers/dnssec.pdf

Here is a common practical problem related to the use DNSSEC. You can block some users whose requests go through firewall of ISP/DC. <br> 
It is a common occurrence for some security technologies to conflict with other security technologies. <br>
Example: https://community.cisco.com/t5/network-security/ios-firewall-dnssec/td-p/1368306
I do not recommend to use DNSSEC.

- Attack #3. http/https MiTM
Traditional protection with the TLS/SSL protocol. Pay attention to the current issue. [DevOps issue](#devops-issue)

- Attack #4. MiTM in communications
It means the interception of messages between 'community member' and 'community manager'. Use proven messengers/communication tools. Preferably with end-to-end encryption (E2EE). <br>
Try to find a balance between convenience ("communications as a service") and security ("client-side encryption"). <br>

- Attack #5. lost or stolen private key (wallet)
Not your keys, not your coins (c) <br>
The traditional recommendation is to use hardware wallet. <br> 
In this case, avoid using gnosis_safe. This is not supported on OpenSea. <br>
https://www.reddit.com/r/opensea/comments/t4ax9h/opensea_and_gnosis_safe_via_wallet_connect/ <br>
https://levelup.gitconnected.com/how-to-allow-multi-sig-wallets-to-authenticate-with-your-dapp-8f8a74e145ea

- Attack #6. lost or stolen API key/account
General recommendations should be followed for google accounts (2FA) <br>
https://support.google.com/answer/2451907?hl=en <br>
https://support.google.com/a/answer/175197?hl=en <br>
https://handsondataviz.org/google-sheets-api-key.html <br>


#### DevOps issue.
Self-signed certificate in "web-server" pfp.autonolas.tech
```
https://etherscan.io/address/0x02c26437b292d86c5f4f21bbcce0771948274f84#readContract
baseURI: https://pfp.autonolas.tech/ 

The certificate is self-signed. Users will receive a warning when accessing this site unless the certificate is manually added as a trusted certificate to their web browser.
None of the common names in the certificate match the name that was entered (pfp.autonolas.tech). You may receive an error when accessing this site in a web browser.
 
openssl s_client -connect pfp.autonolas.tech:443
CONNECTED(00000003)
depth=0 O = Acme Co, CN = Kubernetes Ingress Controller Fake Certificate
verify error:num=18:self-signed certificate
verify return:1
depth=0 O = Acme Co, CN = Kubernetes Ingress Controller Fake Certificate
verify return:1

https://security.stackexchange.com/questions/184969/how-mitm-attack-got-performed-on-self-signed-certificate-while-private-keys-is-g
https://security.stackexchange.com/questions/56389/ssl-certificate-framework-101-how-does-the-browser-actually-verify-the-validity?noredirect=1&lq=1

Self-signed certificates make automatic verification impossible and make MiTM much easier. If possible, avoid this in public projects (public web site).
```
### Review of `packages/valory/`
A quick code review with short notes for each file in the project can be found in the file <br>
packages/balancer: [packages_valory.md](packages_valory.md).

Update: 06-12-22. <br>
* So far, the code has been reviewed up to
```
    │   └── tools.py
    ├── __init__.py
```

Notes: <br>
It is not an error, but it is desirable to add numbers from the subject area to the metadata. <br>
Details: https://docs.opensea.io/docs/metadata-standards#numeric-traits

#### List of useful links
OpenSea Metadata structure: <br>
https://docs.opensea.io/docs/metadata-standards

Hold all metadata and SVG images on-chain: <br>
https://gist.github.com/Chmarusso/045ee79fa9a1fae55928a613044c9067

Add your metadata file to IPFS: <br>
https://blog.chain.link/build-deploy-and-sell-your-own-dynamic-nft/ <br>
https://github.com/PatrickAlphaC/dungeons-and-dragons-nft/blob/master/scripts/set-token-uri.js

