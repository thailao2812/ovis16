# -*- coding: utf-8 -*-

import json
# import urllib.request
from odoo import api, fields, models, tools, _, SUPERUSER_ID
import requests
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_api_restful_token(self):
        for rcs in self:
            # url = "http://localhost:8019/api/purchase.order"
            synchronize_id = self.env['api.synchronize.data'].search([
                ('model', '=', rcs._name),
                ('res_id', '=', rcs.id)
            ])
            if not synchronize_id:
                synchronize_id = self.env['api.synchronize.data'].create({
                    'name': rcs.name,
                    'model': rcs._name,
                    'res_id': rcs.id
                })

            url = self.env.ref(
                'api_restful.default_api_restfull_url_config',
                False)
            if url:
                url = url.value + '/' + rcs._name

            # xử lý tìm kiếm data đã tạo
            if synchronize_id and synchronize_id.res_id_syn:
                url += '/' + str(synchronize_id.res_id_syn)

            access_token = self.env.ref(
                'api_restful.default_api_restfull_access_token_config',
                False)
            url = 'http://localhost:8019/api/res.country'

            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'access-token': access_token and access_token.value or False,
            }

            payload = {
                'limit': 1
            }

            response = requests.request(
                "GET",
                url,
                data=payload,
                headers=headers
            )
