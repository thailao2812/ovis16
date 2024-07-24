# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResCurrency(models.Model):
    _inherit = "res.currency"

    currency_type = fields.Selection([
        ('basic', 'Basic'),
        ('small', 'Smaller'),
        ('larger', 'Larger')
        ], string='Currency Type', index=True, copy=False, default='basic')

    # THANH 20220503 - override original function
    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        # currency_rates = (from_currency + to_currency)._get_rates(company, date)
        # res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)
        # return res

        # THANH 20220508 - return rate = 1 when from_currency = to_currency
        if from_currency == to_currency:
            return 1.0

        # THANH 20220503 - check and raise error when from_currency and to_currency has currency_type is basic
        if from_currency.currency_type == 'basic' and to_currency.currency_type == 'basic':
            raise UserError(
                _("Currency Type of %s is the same type basic with %s , it's should be larger or smaller !")
                % (from_currency.name, to_currency.name))

        # THANH - get rate passed from context
        currency_rate = self._context.get('currency_rate') or from_currency._context.get(
            'currency_rate') or to_currency._context.get('currency_rate')
        if currency_rate and currency_rate < 1.0 and from_currency != to_currency:
            currency_rate = False
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        from_rate = currency_rates.get(from_currency.id)
        to_rate = currency_rates.get(to_currency.id)

        if to_currency.currency_type == 'basic':
            if currency_rate:
                from_rate = currency_rate
            if from_currency.currency_type == 'larger':
                return from_rate#, from_rate
            else:
                return from_rate and 1 / from_rate or 1#, from_rate

        if from_currency.currency_type == 'basic':
            if currency_rate:
                to_rate = currency_rate
            if to_currency.currency_type == 'small':
                return to_rate#, to_rate
            else:
                return to_rate and 1 / to_rate or 1#, to_rate

        # THANH: Both currency is not basic (This method based on only one Basic Currency, Others can be Smaller or Larger)
        # exchange 5 USD -> ? EUR, ex: 28,000 (EUR compare to VND), 22,000 (USD compare to USD)
        # value EUR = 5 * (22,000 / 28,000) = ???
        # In the other case, exchange 5 EUR -> ? USD
        # value USD = 5 * (28,000 / 22,000)
        # fomular = from_amount * (from_rate / to_rate)
        res = to_rate and from_rate / to_rate or 1#, to_rate and from_rate / to_rate or 1
        return res
