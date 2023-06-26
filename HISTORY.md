# Release History - `Contribution Service`

## 0.5.4 (2023-06-26)

- Bumps frameworks to `open-autonony-0.10.7` and `open-aea-1.35` # 121
- Fix olas links #120

## 0.5.3 (2023-06-20)

- Bumps to `open-autonony-0.10.6` #118
- Bumps to the latest impact evaluator service #119

## 0.5.2 (2023-06-07)

- Bumps to `open-autonony-0.10.5.post2` #117
- Bumps to `tomte@v0.2.12` and cleans up the repo #116

## 0.5.1 (2023-06-01)

- Bumps frameworks to `open-autonony-0.10.5.post1` and `open-aea-1.34`
- Bumps to the latest impact evaluator service

## 0.5.0 (2023-04-26)

- Bump to `open-autonomy@v0.10.2`
- Import packages from IEKit repository

## 0.4.0.post1 (2023-04-03)

- Bump to `open-autonomy@v0.10.0.post2`
- Sets the `p2p_libp2p_client` as none abstract to enable `ACN`

## 0.4.0 (2023-03-27)

- Bump to `open-autonomy@v0.10.0.post1`
- Adds liccheck to the linters
- Adds a script to verify that the reported scores are correct
- Updates documentation
- Add a release workflow

## 0.3.0 (2023-02-24)

- Bump to `open-autonomy@v0.9.1`
- Updates docs
- Removes the mock check during execution
- Uses the latest transition timestamp for the healthcheck
- The service now remembers the latest parsed block to avoid retrieving all data during every period.
- Splits big requests into smaller ones to avoid timeouts
- Updates service configuration

## 0.2.0.post1 (2023-01-31)

- Updates kits icons
- Fixes addresses configuration

# 0.2.0 (2023-01-25)

- Improved test coverage
- Improved handler routing implementation
- Added release workflow
- Added attributes to the token metadata
- Added layer threshold format during API data validation
- Changes handler health implementation to get proper healthcheck even if Tendermint dies
- Corrected how the seconds until next reset is calculated for the healthcheck
- Handle exceptions when the service account does not have write permissions.
- Added initial documentation to the repository
- Bumped open-autonomy framework to 0.8.0


# 0.1.0 (2022-12-14)

- First release of the Contribution Service
