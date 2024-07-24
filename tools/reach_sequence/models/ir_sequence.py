# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from odoo.addons.base.models import ir_sequence

_logger = logging.getLogger(__name__)

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def init(self):
        # THANH 020123 - change sql sequence of SO & PO
        so_sequence_id = self.env['ir.model.data']._xmlid_to_res_id('sale.seq_sale_order')
        if so_sequence_id:
            sql = '''
                update ir_sequence 
                set implementation='reach_sequence', rollback_rule='Monthly', prefix='SO-%(y)s-%(month)s-'
            '''
            sql += "where id=%s and prefix='S';" % (so_sequence_id)
            self.env.cr.execute(sql)
        po_sequence_id = self.env['ir.model.data']._xmlid_to_res_id('purchase.seq_purchase_order')
        if po_sequence_id:
            sql = '''
                update ir_sequence 
                set implementation='reach_sequence', rollback_rule='Monthly', prefix='PO-%(y)s-%(month)s-'
            '''
            sql += "where id=%s and prefix='P';" % (po_sequence_id)
            self.env.cr.execute(sql)

    # THANH 020123 - override original function
    def _get_number_next_actual(self):
        '''Return number from ir_sequence row when no_gap implementation,
        and number from postgres sequence when standard implementation.'''
        for seq in self:
            if not seq.id:
                seq.number_next_actual = 0
            # elif seq.implementation != 'standard': THANH override odoo
            elif seq.implementation in ('no_gap', 'reach_sequence'):
                # THANH reach_sequence goes this way
                seq.number_next_actual = seq.number_next
            else:
                seq_id = "%03d" % seq.id
                seq.number_next_actual = ir_sequence._predict_nextval(self, seq_id)

    # THANH 020123 - add new implementation reach_sequence standard
    implementation = fields.Selection(selection_add=[
        ('reach_sequence', 'REACH SEQUENCE Standard')],
        string='Implementation', required=True, default='standard', ondelete={'reach_sequence': 'set default'},
          help="While assigning a sequence number to a record, the 'no gap' sequence implementation ensures that each previous sequence number has been assigned already. "
          "While this sequence implementation will not skip any sequence number upon assignment, there can still be gaps in the sequence if records are deleted. "
          "The 'no gap' implementation is slower than the standard one.")

    # THANH 020123 - re-define field number_next_actual to inherit compute function
    # number_next_actual = fields.Integer(compute='_get_number_next_actual', inverse='_set_number_next_actual',
    #                                     string='Actual Next Number',
    #                                     help="Next number that will be used. This number can be incremented "
    #                                          "frequently so the displayed value might already be obsolete")

    encoding = fields.Selection([('normal', 'Normal'),('ean13', 'EAN-13'), ('ean8', 'EAN-8'), ('upca', 'UPC-A')],
                                string='Encoding', required=True, default='normal')
    rollback_rule = fields.Selection([
        ('None', 'None'),
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly')], string='Rule restart', default='None', required=True)
    sequence_his = fields.One2many('ir.sequence.his', 'seq_id', string='Sequence Histories', readonly=False)

    # THANH - new function
    @api.onchange('implementation')
    def _onchange_implementation(self):
        if self.implementation == 'reach_sequence' and self.encoding == 'normal':
            self.rollback_rule = 'Monthly'
            self.padding = 5
        return

    # THANH 020123 - override odoo
    @api.model
    def next_by_code(self, sequence_code, sequence_date=None):
        """ Draw an interpolated string using a sequence with the requested code.
            If several sequences with the correct code are available to the user
            (multi-company cases), the one from the user's current company will
            be used.
        """
        self.check_access_rights('read')
        company_id = self.env.company.id
        seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [company_id, False])],
                              order='company_id')
        if not seq_ids:
            _logger.debug(
                "No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current company." % sequence_code)
            return False
        seq_id = seq_ids[0]
        # THANH 20211024 - generate sequence number
        next_code = seq_id._next(sequence_date=sequence_date)
        if seq_id.encoding != 'normal':
            # THANH 20211024 - generate barcode
            next_code = seq_id.generate_barcode(barcode_base=next_code)
        return next_code

    # THANH - new function add inherit function get prefix
    def _get_prefix_suffix_inherit(self):
        return {}

    # THANH 020123 - override odoo
    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            return res

        self.ensure_one()
        d = _interpolation_dict()
        # THANH 20211024 -  mở rộng thêm prefix hoặc suffice được truyền vào từ module kế thừa
        d.update(self._get_prefix_suffix_inherit())
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % self.name)
        return interpolated_prefix, interpolated_suffix

    # THANH 020123 - inherit odoo
    def get_next_char(self, number_next):
        if self.implementation != 'reach_sequence':
            return super(IrSequence, self).get_next_char(number_next)

        # THANH - get sequence by reach standard
        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix()
        if self._context.get('ir_sequence_date', False):
            transaction_date = datetime.strptime(self._context['ir_sequence_date'], '%Y-%m-%d')
            day = int(transaction_date.strftime('%d'))
            month = int(transaction_date.strftime('%m'))
            year = int(transaction_date.strftime('%Y'))
        else:
            today = fields.Date.today()
            day = today.day
            month = today.month
            year = today.year

        sql = "select his.number_current from ir_sequence_his his where his.seq_id=%s"%(self.id)
        # THANH - filter by company_id
        company_id = self._context.get('company_id', self.company_id.id)
        if not company_id and len(self._context.get('allowed_company_ids', [])) == 1:
            company_id = self._context.get('allowed_company_ids', [])[0]

        if company_id:
            sql += ' and company_id=%s'%(company_id)
        elif self.encoding == 'normal':
            raise UserError(_('REACH SEQUENCE STANDARD required passed context company_id to genertate Sequence Number.\nSequence %s') %(self.name))

        if self.rollback_rule == 'Yearly':
            sql += " AND his.year = %s" % (year)
        if self.rollback_rule == 'Monthly':
            sql += " AND his.year = %s AND his.month = %s" % (year, month)
        if self.rollback_rule == 'Daily':
            sql += " AND his.year = %s AND his.month = %s AND his.day = %s" % (year, month, day)

        # Vuong: - Remove NOWAIT to ignore raise error when 2 query select same time on same row
        #       - Query 2 much wait until query 1 done first, affected by FOR UPDATE
        sql = sql + ' order by his.number_current desc limit 1 FOR UPDATE;'
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()
        if result and result[0] != 0:
            number_current = result[0]
            number_next = number_current + self.number_increment
        else:
            number_next = self.number_next

        sequence = interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix
        # Thanh - Insert into History
        self.env.cr.execute('''
                    INSERT INTO ir_sequence_his (create_uid,create_date,write_uid,write_date,
                        seq_id,generate_code, company_id,
                        number_current, day,month,year)
                    VALUES (%s,current_timestamp,%s,current_timestamp,
                            %s,'%s',
                            %s,
                            %s, %s, %s, %s);
        '''%(self.env.user.id, self.env.user.id,
             self.id, sequence,
             company_id or 'null',
             number_next, day, month, year))
        return sequence

    # THANH 020123 - inherit odoo
    def _next_do(self):
        if self.implementation != 'reach_sequence':
            return super(IrSequence, self)._next_do()
        else:
            # THANH - reach sequence standard goes this way
            return self.get_next_char('')

    # THANH 020123 - new function
    def generate_barcode(self, barcode_base=None):
        if self.encoding == 'normal':
            raise UserError(_('The encoding do not fitting.'))
        padding = self.padding
        str_base = str(barcode_base).rjust(padding, '0')
        custom_code = self._get_custom_barcode()
        if custom_code:
            custom_code = str_base
            barcode = custom_code + str(self.ean_checksum(custom_code) if self.encoding in ('ean13','upca') else self.ean8_checksum(custom_code))
            if barcode:
                return barcode 
            raise UserError(_('Error! When creating barcode!'))
        return

    # THANH 020123 - new function
    def ean_checksum(self, ean):
        code = list(ean)
        if len(code) != 12:
            raise UserError(_('Custom Barcode not enough 12 character!'))
        oddsum = evensum = 0
        for i in range(len(code)):
            if i % 2 == 0:
                evensum += int(code[i])
            else:
                oddsum += int(code[i])
        total = oddsum * 3 + evensum
        return int((10 - total % 10) % 10)

    # THANH 020123 - new function
    def ean8_checksum(self,ean):
        code = list(ean)
        if len(code) != 7:
            raise UserError(_('Custom Barcode not enough 7 character!'))
        sum1  = int(ean[1]) + int(ean[3]) + int(ean[5])
        sum2  = int(ean[0]) + int(ean[2]) + int(ean[4]) + int(ean[6])
        total = sum1 + 3 * sum2
        return int((10 - total % 10) % 10)

    # THANH 020123 - new function
    def _generate_ean13(self, barcode):
        if barcode is None:
            return None
        if len(barcode) != 12:
            raise UserError(_('Barcode not enough 12 character'))
        total = 0
        chars = str(barcode)
        for i, c in enumerate(chars):
            total += int(c) if i % 2 == 0 else int(c) * 3
        check_sum = (10 - (total % 10)) % 10
        return barcode + str(check_sum)

    # THANH 020123 - new function
    def _get_custom_barcode(self):
        """
            - The N's define where the number's digits are encoded  
            - Floats are also supported with the decimals indicated with D's
            ex: 21.....{NNDDD}
        """
        custom_code = self.prefix
        if custom_code:
            custom_code = custom_code.replace('{', '').replace('}', '')
            custom_code = custom_code.replace(
                'D', self._get_replacement_char('D'))
            return custom_code.replace(
                'N', self._get_replacement_char('N'))
        return

    # THANH 020123 - new function
    @api.model
    def _get_replacement_char(self, char):
        return '0'
    
class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'
     
    # THANH 020123 - extend original function
    def _next(self):
        if self.sequence_id.implementation != 'reach_sequence':
            return super(IrSequenceDateRange, self)._next()
        else:
            # THANH - reach sequence standard goes this way
            return self.sequence_id.get_next_char('')

# THANH - new object
class IrSequenceHis(models.Model):
    _name = 'ir.sequence.his'
    _description = 'Sequence History by Company Analytic Account'
    _order = 'year desc, month desc, day desc, number_current desc'

    seq_id = fields.Many2one('ir.sequence', 'Sequence', required=False, index=True)
    generate_code = fields.Char('Generate Code', size=64, required=True, index=True)
    number_current = fields.Integer('Number Current', required=True, index=True)
    day = fields.Integer('Day', help="Day of a month (1..31)", index=True)
    month = fields.Integer('Month', help="Month of a year (1..12)", index=True)
    year = fields.Integer('Year', index=True)
    company_id = fields.Many2one('res.company', 'Company', required=False, index=True)


