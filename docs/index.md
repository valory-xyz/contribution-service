![CoordinationKit](images/coordinationkit.svg){ align=left }
The CoordinationKit helps you build services to show off community contributions by letting users mint badges which evolve as they make contributions to the DAO. Such services work by monitoring user contributions, updating their badges accordingly and showing off contributions on NFT-enabled social media sites.

Autonolas Contribute, a service based on the CoordinationKit, streamlines the contribution experience for members of the Autonolas community.
When someone mints a badge, they will start at the first tier. As they complete actions that contribute to the success of Autonolas, they will earn points and climb the leaderboard. When they earn enough points to reach a higher badge tier, their badge will automatically update to reflect the new rank. This is a great way to demonstrate contributions on NFT-enabled social media sites and earn recognition that reflects users' contribution within the Autonolas community.

Every few minutes an Autonolas Contribute checks the leaderboard. If a user has earned enough points to put them in a new [badge tier](https://contribute.autonolas.network/docs#section-badge) the service will automatically update your badge NFT’s image. By completing certain actions, users climb the leaderboard and upgrade their badge.

## Demo

!!! warning "Important"

	This section is under active development - please report issues in the [Autonolas Discord](https://discord.com/invite/z2PT65jKqQ).

Once you have {{set_up_system}} to work with the Open Autonomy framework, you can run a local demo of the Autonolas Contribute service as follows:

1. Fetch the Autonolas Contribute service.

	```bash
	autonomy fetch valory/contribution:0.1.0:bafybeiax2k7nf5qf7p6uuawgfplsuqcdjvwoby36wbbbe7x2hptl25zl5m --service
	```

2. Build the Docker image of the service agents

	```bash
	cd contribution
	autonomy build-image
	```

3. Prepare the `keys.json` file containing the wallet address and the private key for each of the agents.

    ??? example "Example of a `keys.json` file"

        <span style="color:red">**WARNING: Use this file for testing purposes only. Never use the keys or addresses provided in this example in a production environment or for personal use.**</span>

        ```json
        [
          {
              "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
              "private_key": "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"
          },
          {
              "address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
              "private_key": "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
          },
          {
              "address": "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
              "private_key": "0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e"
          },
          {
              "address": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
              "private_key": "0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356"
          }
        ]
        ```

4. Prepare the environment and build the service deployment.

	1. Create a service token (you can follow [this guide](https://www.sharperlight.com/uncategorized/2022/04/06/accessing-the-google-sheets-api-via-sharperlight-query-builder/)).

	2. Create an `.env` file with the required environment variables.

	```bash
	ETHEREUM_LEDGER_RPC=https://goerli.infura.io/v3/<infura_api_key>
	DYNAMIC_CONTRIBUTION_CONTRACT_ADDRESS=0x7c3b976434fae9986050b26089649d9f63314bd8
	EARLIEST_BLOCK_TO_MONITOR=8053690
	IPFS_GATEWAY_BASE_URL=https://gateway.staging.autonolas.tech/ipfs/
	LEADERBOARD_API_KEY=<google_api_key_here>
	LEADERBOARD_BASE_ENDPOINT=https://sheets.googleapis.com/v4/spreadsheets
	LEADERBOARD_LAYERS_RANGE=Layers!B1:Z32
	LEADERBOARD_POINTS_RANGE=Ranking!B2:C302
	LEADERBOARD_SHEET_ID=1m7jUYBoK4bFF0F2ZRnT60wUCAMWGMJ_ZfALsLfW5Dxc
	OBSERVATION_INTERVAL=10 SERVICE_AUTH=<service_auth_here>
	```

	3. Build the service deployment.

    ```bash
    autonomy deploy build keys.json --aev
    ```

5. Run the service.

	```bash
	cd abci_build
	autonomy deploy run
	```

	You can cancel the local execution at any time by pressing ++ctrl+c++.

## Build

1. Fork the [CoordinationKit repository](https://github.com/valory-xyz/contribution-service).
2. Make the necessary adjustments to tailor the service to your needs. This could include:
    * Adjust configuration parameters (e.g., in the `service.yaml` file).
    * Expand the service finite-state machine with your custom states.
3. Run your service as detailed above.

!!! tip "Looking for help building your own?"

    Refer to the [Autonolas Discord community](https://discord.com/invite/z2PT65jKqQ), or consider ecosystem services like [Valory Propel](https://propel.valory.xyz) for the fastest way to get your first autonomous service in production.
