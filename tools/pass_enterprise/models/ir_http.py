# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):

        result = super(Http, self).session_info()
        result['support_url'] = "https://www.odoo.com/help"
        if 'expiration_date' in result:
            del result["expiration_date"]
        if 'warning' in result:
            del result["warning"]
        if 'expiration_reason' in result:
            del result["expiration_reason"]
        return result
