from odoo import api, fields, http, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'id desc'

    weightbridge_update = fields.Boolean(string='API Update', default=False, readonly=True)