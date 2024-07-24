# -*- coding: utf-8 -*-
from werkzeug.exceptions import BadRequest

from odoo import models, SUPERUSER_ID
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'
    
    @classmethod
    def _auth_method_api_key(cls):
        access_token = request.httprequest.headers.get('Authorization')
        if not access_token:
            # access_token = request.httprequest.headers.get('API-KEY')
            # if not access_token:
            raise BadRequest('Access token is missing')
        
        if access_token.startswith('Bearer '):
            access_token = access_token[7:]
            
        user_id = request.env['res.users.apikeys']._check_credentials(scope='odoo.restapi', key=access_token)
        if not user_id:
            raise BadRequest('Invalid access token')
        
        # take the identity of the API key user
        request.update_env(user=user_id)
