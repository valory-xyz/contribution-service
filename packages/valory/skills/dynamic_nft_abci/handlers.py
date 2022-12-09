# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the handlers for the skill of DynamicNFTAbciApp."""

import json
import re
from typing import Callable, Dict, Optional, Tuple, cast
from urllib.parse import urlparse

from aea.protocols.base import Message

from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_PUBLIC_ID,
)
from packages.valory.protocols.http.message import HttpMessage
from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler as BaseABCIRoundHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler as BaseContractApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    LedgerApiHandler as BaseLedgerApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    SigningHandler as BaseSigningHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    TendermintHandler as BaseTendermintHandler,
)
from packages.valory.skills.dynamic_nft_abci.dialogues import (
    HttpDialogue,
    HttpDialogues,
)
from packages.valory.skills.dynamic_nft_abci.rounds import SynchronizedData


ABCIRoundHandler = BaseABCIRoundHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler
OK_CODE = 200
NOT_FOUND_CODE = 404
BAD_REQUEST_CODE = 400


class HttpHandler(BaseHttpHandler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""
        uri_base_hostname = urlparse(self.context.params.token_uri_base).hostname
        hostname_regex = rf".*({uri_base_hostname}|localhost|127.0.0.1)(:\d+)?"
        address_regex = r"0x[a-fA-F0-9]{40}"

        self.handler_url_regex = rf"{hostname_regex}\/.*"
        self.metadata_url_regex = rf"{hostname_regex}\/\d+"
        self.leaderboard_url_regex = rf"{hostname_regex}\/leaderboard"
        self.address_status_url_regex = (
            rf"{hostname_regex}\/address_status/(?P<address>{address_regex})"
        )
        self.link_wallet_url_regex = rf"{hostname_regex}\/link"

        self.json_content_header = "Content-Type: application/json\n"

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return SynchronizedData(
            db=self.context.state.round_sequence.latest_synchronized_data.db
        )

    def _get_handler(self, http_msg: HttpMessage) -> Tuple[Optional[Callable], Dict]:
        """Check if an url is meant to be handled in this handler and return its handling method

        We expect url to match the pattern {hostname}/.*,
        where hostname is allowed to be localhost, 127.0.0.1 or the token_uri_base's hostname.
        Examples:
            localhost:8000/0
            127.0.0.1:8000/100
            https://pfp.staging.autonolas.tech/45
            http://pfp.staging.autonolas.tech/120

        :param url: the url to check
        :returns: the handling method if the message is intended to be handled by this handler, None otherwise, and the regex captures
        """

        if not re.match(self.handler_url_regex, http_msg.url):
            self.context.logger.info(
                f"The url {http_msg.url} does not match the DynamicNFT HttpHandler's pattern"
            )
            return None, {}

        if http_msg.method in ("get", "head"):

            if re.match(self.metadata_url_regex, http_msg.url):
                return self._handle_get_metadata, {}

            if re.match(self.leaderboard_url_regex, http_msg.url):
                return self._handle_get_leaderboard, {}

            m = re.match(self.address_status_url_regex, http_msg.url)
            if m:
                return self._handle_get_address_status, m.groupdict()

        if http_msg.method in ("post"):

            if re.match(self.link_wallet_url_regex, http_msg.url):
                return self._handle_post_link, {}

        self.context.logger.info(
            f"The message [{http_msg.method}] {http_msg.url} is intended for the DynamicNFT HttpHandler but did not match any valid pattern"
        )
        return self._handle_bad_request, {}

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)
        handler, kwargs = self._get_handler(http_msg)

        # Check if this message is for this skill. If not, send to super()
        if (
            http_msg.performative != HttpMessage.Performative.REQUEST
            or message.sender != str(HTTP_SERVER_PUBLIC_ID.without_hash())
            or not handler
        ):
            super().handle(message)
            return

        # Retrieve dialogues
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))

        # Invalid message
        if http_dialogue is None:
            self.context.logger.info(
                "Received invalid http message={}, unidentified dialogue.".format(
                    http_msg
                )
            )
            return

        # Handle message
        self.context.logger.info(
            "Received http request with method={}, url={} and body={!r}".format(
                http_msg.method,
                http_msg.url,
                http_msg.body,
            )
        )
        handler(http_msg, http_dialogue, **kwargs)

    def _handle_bad_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http bad request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=BAD_REQUEST_CODE,
            status_text="Bad request",
            headers=http_msg.headers,
            body=b"",
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_get_metadata(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle the metadata Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        # Get the requested uri and the redirects table
        request_uri = http_msg.url
        token_id = request_uri.split("/")[-1]
        redirects = self.synchronized_data.redirects

        # Token not in redirects
        if token_id not in redirects:
            self.context.logger.info(
                f"Requested URL {request_uri} is not present in redirect table"
            )
            self._send_not_found_response(http_msg, http_dialogue)
            return

        # Token in redirects
        self.context.logger.info(
            f"Requested URL {request_uri} is present in redirect table"
        )

        redirect_uri = redirects[token_id]
        image_hash = redirect_uri.split("/")[-1]  # get the hash only

        # Build token metadata
        metadata = {
            "title": "Autonolas Dynamic Contribution",
            "name": f"Autonolas Dynamic Contribution {token_id}",
            "description": "This NFT recognizes the contributions made by the holder to the Autonolas Community.",
            "image": f"ipfs://{image_hash}",
            "attributes": [],  # TODO: add attributes
        }

        self.context.logger.info(f"Responding with token metadata={metadata}")
        self._send_ok_response(http_msg, http_dialogue, metadata)

    def _handle_get_leaderboard(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle the leaderboard Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        data = {"result": self.context.sheet.read()}
        self._send_ok_response(http_msg, http_dialogue, data)

    def _handle_get_address_status(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue, address: str
    ) -> None:
        """
        Handle the address_status Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        data = {
            "address": address,
            "status": self.context.sheet.get_wallet_status(wallet_address=address),
        }
        self._send_ok_response(http_msg, http_dialogue, data)

    def _handle_post_link(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle the link Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        body = json.loads(http_msg.body)

        if "discord_id" not in body or "wallet_address" not in body:
            self._send_not_found_response(http_msg, http_dialogue)
            return

        discord_id = str(body["discord_id"])
        wallet_address = body["wallet_address"]

        self.context.sheet.write(discord_id=discord_id, wallet_address=wallet_address)
        self._send_ok_response(http_msg, http_dialogue, {})

    def _send_ok_response(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue, data: Dict
    ) -> None:
        """Send an OK response with the provided data"""
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=OK_CODE,
            status_text="Success",
            headers=f"{self.json_content_header}{http_msg.headers}",
            body=json.dumps(data).encode("utf-8"),
        )

        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _send_not_found_response(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """Send an not found response"""
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=NOT_FOUND_CODE,
            status_text="Not found",
            headers=http_msg.headers,
            body=b"",
        )
        # Send response
        self.context.logger.info("Responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)
