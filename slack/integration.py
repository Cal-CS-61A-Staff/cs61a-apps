import abc
from typing import List, Type

from config_client import get_team_data


class Integration(abc.ABC):
    def __init__(self, message: str, token, team_id):
        self._message = message
        self._token = token
        self._team_id = team_id
        self._course, self._bot_token = get_team_data(team_id)
        self._process()

    def _process(self):
        pass

    @property
    def message(self):
        return self._message

    @property
    def attachments(self):
        return []

    @property
    def responses(self):
        return []


def combine_integrations(integrations: List[Type[Integration]]):
    class CombinedIntegration(Integration):
        def _process(self):
            text = self._message
            attachments = []
            responses = []
            for integration_type in integrations:
                integration = integration_type(text, self._token, self._team_id)
                text = integration.message
                attachments.extend(integration.attachments)
                responses.extend(integration.responses)
            self._text = text
            self._attachments = attachments
            self._responses = responses

        @property
        def message(self):
            return self._text

        @property
        def attachments(self):
            return self._attachments

        @property
        def responses(self):
            return self._responses

    return CombinedIntegration
