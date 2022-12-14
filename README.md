# Contribution Service
A dynamic NFT service built with the open-autonomy framework. The service checks a spreadsheet that contains scores for all the community members that
have minted a token and verified their addresses through Discord. NFT images will be upgraded according member scores.

- Clone the repository:

      git clone git@github.com:valory-xyz/contribution-service.git

- System requirements:

    - Python `>=3.7`
    - [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.19`
    - [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==0.6.0`
    - [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
    - [Docker Engine](https://docs.docker.com/engine/install/)
    - [Docker Compose](https://docs.docker.com/compose/install/)

- Pull pre-built images:

      docker pull valory/autonolas-registries:latest
      docker pull valory/safe-contract-net:latest

- Create development environment:

      make new_env && pipenv shell

- Configure command line:

      autonomy init --reset --author valory --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"

- Pull packages:

      autonomy packages sync --update-packages

## Running the service

- Fetch the service from the remote registry:

      autonomy fetch --local --service valory/contribution
      cd contribution/

- Build the image

      autonomy build-image

- Export the environment variables: ETHEREUM_LEDGER_RPC, ETHEREUM_LEDGER_CHAIN_ID, LEADERBOARD_API_KEY, LEADERBOARD_SHEET_ID, OBSERVATION_INTERVAL, DYNAMIC_CONTRIBUTION_CONTRACT_ADDRESS.

- Build the deployment:

      autonomy deploy build --aev

- Run the deployment:

      autonomy deploy run --build-dir abci_build/

- Some examples on how to curl the service endpoints from inside the container:

      sudo apt install -y curl jq
      curl localhost:8000/1 | jq
      curl localhost:8000/healthcheck | jq