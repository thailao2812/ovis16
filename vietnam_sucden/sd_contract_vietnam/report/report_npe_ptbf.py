# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"



class Parser(models.AbstractModel):
    _inherit = 'report.report_contract_ptbf_npe'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()

        localcontext.update({
            'get_license_2nd': self.get_license_2nd
        })
        return localcontext


    def get_license_2nd(self, purchase):
        if purchase:
            if purchase.license_2nd_id:
                return '(' + purchase.license_2nd_id.name + ')'
            else:
                return ''
        else:
            return ''