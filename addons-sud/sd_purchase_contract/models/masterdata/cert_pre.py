# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression



class CertificatePre(models.Model):
    _name = 'cert.pre'

    name = fields.Char(string='Name', default='Configuration For Cert Pre')
    effective_date = fields.Date(string='Effective Date')
    end_date = fields.Date(string='End Date')
    cert_pre_line_ids = fields.One2many('cert.pre.line', 'cert_pre_id')
    state = fields.Selection([
        ('run', 'Running'),
        ('stop', 'Stop')
    ], string='State', default='run')

    def action_stop_config(self):
        for record in self:
            record.write({
                'state': 'stop',
                'end_date': datetime.now().date()
            })
    @api.constrains('name')
    def constrains_for_cert_pre(self):
        check = self.search([
            ('name', '=', self.name),
            ('id', '!=', self.id)
        ])
        if check:
            raise UserError(_("You just need to have 1 config, please check again"))


class CertificatePreLine(models.Model):
    _name = 'cert.pre.line'

    cert_pre_id = fields.Many2one('cert.pre')
    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    price_in_usd = fields.Float(string='Price (USD)')
    price_in_vnd = fields.Float(string='Price (VND)')