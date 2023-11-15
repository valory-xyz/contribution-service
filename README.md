# Contribution Service
A dynamic NFT service built with the open-autonomy framework. The service checks a spreadsheet that contains scores for all the community members that
have minted a token and verified their addresses through Discord. NFT images will be upgraded according member scores. Find the frontend repository [here](https://github.com/valory-xyz/autonolas-contribution-service-frontend).

- Clone the repository:

      git clone git@github.com:valory-xyz/contribution-service.git

- System requirements:

    - Python `>=3.7`
    - [Tendermint](https://docs.tendermint.com/v0.34/introduction/install.html) `==0.34.19`
    - [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==0.6.0`
    - [Pipenv](https://pipenv.pypa.io/en/latest/installation.html) `>=2021.x.xx`
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

To learn how to run the service, check the [ContributionKit tutorial](https://docs.autonolas.network/product/coordinationkit/).
