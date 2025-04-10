# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _


class ConfigurationEDUR(models.Model):
    _name = 'edur.configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Configuration EUDR"

    deforestation_percentage = fields.Float(string='Deforestation Percentage')