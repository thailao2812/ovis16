# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from apispec import BasePlugin
from ..tools import ROUTING_DECORATOR_ATTR


class RestMethodSecurityPlugin(BasePlugin):
    def __init__(self, service, apikey_auths=("api_key",)):
        super(RestMethodSecurityPlugin, self).__init__()
        self._service = service
        self._supported_user_auths = apikey_auths

    # pylint: disable=W8110
    def init_spec(self, spec):
        super(RestMethodSecurityPlugin, self).init_spec(spec)
        self.spec = spec
        self.openapi_version = spec.openapi_version
        api_key_scheme = {"type": "apiKey", "in": "header", "name": "Authorization"}
        spec.components.security_scheme("api_key", api_key_scheme)

    def operation_helper(self, path=None, operations=None, **kwargs):
        routing = kwargs.get(ROUTING_DECORATOR_ATTR)
        if not routing:
            super(RestMethodSecurityPlugin, self).operation_helper(
                path, operations, **kwargs
            )
        if not operations:
            return
        default_auth = self.spec._params.get("default_auth")
        auth = routing.get("auth", default_auth)
        if auth in self._supported_user_auths or (
            auth == "public_or_default" and default_auth == "api_key"
        ):
            for _method, params in operations.items():
                security = params.setdefault("security", [])
                security.append({"api_key": []})
