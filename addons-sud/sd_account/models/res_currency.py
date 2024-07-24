# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from datetime import time, date, datetime, timedelta


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def cron_create_rate_currency(self, ids=None):
        for currency in self.search([]):
            sql = '''
                    select id, name
                    FROM 
                        res_currency_rate
                    where currency_id = %s
                        order by  name  desc
                    limit 1
                ''' % (currency.id)
            self.env.cr.execute(sql)
            for line in self.env.cr.dictfetchall():
                date = datetime.strptime(str(line['name']), DATE_FORMAT).date()
                current_date = datetime.now().date()
                while date < current_date:
                    sql = '''
                            SELECT '%s'::date +1 as date_name
                        ''' % (date)
                    self.env.cr.execute(sql)
                    for day in self.env.cr.dictfetchall():
                        date = day['date_name']
                    rate_id = self.env['res.currency.rate'].browse(line['id'])
                    rate_id.copy({'name': date})
