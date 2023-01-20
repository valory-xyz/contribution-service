![ContributionKit](images/autonolas-contribute-logo.png){ align=left width="150" }

The ContributionKit helps you build services to show off community contributions by minting badges which evolve as users make contributions to the DAO. Such services work by minting badges and activate them to witness an update, showing off contributions on NFT-enabled social media sites.

Autonolas Contribute, a service based on the ContributionKit, streamlines the contribution experience for members of the Autonolas community.
When someone mints a badge, they will start at the first tier. As they complete actions that contribute to the success of Autonolas, you'll earn points and climb the leaderboard. When you earn enough points to reach a higher badge tier, their badge will automatically update to reflect the new rank. This is a great way to demonstrate contributions on NFT-enabled social media sites and earn recognition that reflects your contribution within the Autonolas community.

Every few minutes an Autonolas Contribute checks the leaderboard. If a user has earned enough points to put them in a new [badge tier](https://contribute.autonolas.network/docs#section-badge) the service will automatically update your badge NFT’s image. By completing certain actions, users climb the leaderboard and upgrade their badge.

## Demo

!!! warning "Important"

	This section is currently being reviewed. You might encounter some difficulty when executing some steps in the tutorial.
	We are working to update it soon.

Once you have {{set_up_system}} to work with the Open Autonomy framework, you can run a local demo of the El Collectooorr service as follows:

1. Fetch the Autonolas Contribute service.

	```bash
	autonomy fetch valory/contribution:0.1.0:bafybeiflabosdgds5ry373izhggnff4t7ggmjb5evz5nbnuvp2bq4n6y7i --service
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

4. Build the service deployment.

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

1. Fork the [ContributionKit repository](https://github.com/valory-xyz/contribution-service).
2. Make the necessary adjustments to tailor the service to your needs. This could include:
    * Adjust configuration parameters (e.g., in the `service.yaml` file).
    * Expand the service finite-state machine with your custom states.
3. Run your service as detailed above.

!!! tip "Looking for help building your own?"

    Refer to the [Autonolas Discord community](https://discord.com/invite/z2PT65jKqQ), or consider ecosystem services like [Valory Propel](https://propel.valory.xyz) for the fastest way to get your first autonomous service in production.