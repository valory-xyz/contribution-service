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

from typing import cast

from aea.protocols.base import Message

from packages.fetchai.protocols.default import DefaultMessage
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
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
)


ABCIRoundHandler = BaseABCIRoundHandler
HttpHandler = BaseHttpHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler

TEMPORARY_REDIRECT_CODE = 307
NOT_FOUND_CODE = 404
BAD_REQUEST_CODE = 400


class HttpHandler(BaseHttpHandler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # handle message
        if http_msg.performative == HttpMessage.Performative.REQUEST:
            # recover dialogue
            http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
            http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))
            if http_dialogue is None:
                self._handle_unidentified_dialogue(http_msg)
                return
            self._handle_request(http_msg, http_dialogue)
        else:
            super().handle(message)

    def _handle_unidentified_dialogue(self, http_msg: HttpMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param http_msg: the message
        """
        self.context.logger.info(
            "received invalid http message={}, unidentified dialogue.".format(http_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=http_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"http_message": http_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _handle_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.info(
            "received http request with method={}, url={} and body={!r}".format(
                http_msg.method,
                http_msg.url,
                http_msg.body,
            )
        )
        if http_msg.method == "get":
            self._handle_get(http_msg, http_dialogue)
        else:
            self._handle_non_get(http_msg, http_dialogue)  # reject other methods

    def _handle_get(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        # Get the requested uri and the redirects table
        request_uri = http_msg.url
        redirects = self.context.state.round_sequence.latest_synchronized_data.redirects

        # Check if the uri exists in the redirect table
        if request_uri not in redirects:
            http_response = http_dialogue.reply(
                performative=HttpMessage.Performative.RESPONSE,
                target_message=http_msg,
                version=http_msg.version,
                status_code=NOT_FOUND_CODE,
                status_text="Not found",
                headers=http_msg.headers,
                body=b"",
            )
        else:
            redirect_uri = redirects[request_uri]
            location_headers = f"Location: {redirect_uri}\n"

            http_response = http_dialogue.reply(
                performative=HttpMessage.Performative.RESPONSE,
                target_message=http_msg,
                version=http_msg.version,
                status_code=TEMPORARY_REDIRECT_CODE,
                status_text="Temporary redirect",
                headers=f"{location_headers}{http_msg.headers}",
                body=b"",
            )

        # Send response
        self.context.logger.info("responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_non_get(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request different from GET.

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
        self.context.logger.info("responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_invalid(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle an invalid http message.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.warning(
            "cannot handle http message of performative={} in dialogue={}.".format(
                http_msg.performative, http_dialogue
            )
        )

    def teardown(self) -> None:
        """Implement the handler teardown."""
