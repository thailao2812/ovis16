# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _


class ResPartnerArea(models.Model):
    """Inherit Drawing mixins model 'google.drawing.shape'"""
    _inherit = 'res.partner.area'

    deforestation = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Deforestation')

    link_to_deforestation = fields.Char(string='Deforestation Map')

    def check_deforestation(self):
        return {
            'name': _("Tracking Deforestation"),
            'type': 'ir.actions.act_url',
            'url': self.link_to_deforestation,
            'target': 'new',
        }
