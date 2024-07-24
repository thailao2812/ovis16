from odoo import http
from odoo.http import Response
import logging
_logger = logging.getLogger(__name__)


class WebFormController(http.Controller):

    @http.route('/odoo/test', type='json',
                auth='public', methods=['POST'], website=True)
    def index(self, **args):
        _logger.info('CONNECTION SUCCESSFUL')
        _logger.info(args)
        name = args.get('name', False)
        email = args.get('email', False)
        _logger.info(name)
        _logger.info(email)
        if not name:
            Response.status = '400 Bad Request'
        return '{"response": "OK"}'