# Contribution Service
A dynamic NFT service built with the open-autonomy framework

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