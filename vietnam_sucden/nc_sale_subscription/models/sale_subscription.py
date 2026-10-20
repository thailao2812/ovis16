# -*- coding: utf-8 -*-
import logging, datetime, timeit
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo import SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)

SALE_SUBSCRIPTION_STATE_STAGE_CODE = {
    'submit': 'submit',
    'review': 'review',
    'comment': 'comment',
}
SALE_SUBSCRIPTION_STATE_STRING = {
    'submit': 'Submit',
    'review': 'Review',
    'comment': 'Comment'
}

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'
    _description = "Proposal"

    def _compute_stage_ids(self):
        stage_ids = self.env['sale.subscription.stage']
        for r in self.role_ids:
            stage_ids += r.stage_id
        self.stage_ids = stage_ids

    def update_version(self, old_version):
        if old_version:
            return str(eval(old_version) + 1)
        return '1'

    @api.depends('recurring_advance_invoice_line_ids', 'recurring_advance_invoice_line_ids.quantity', 'recurring_advance_invoice_line_ids.price_subtotal')
    def _compute_recurring_total(self):
        for account in self:
            account.recurring_total = sum(line.price_subtotal for line in account.recurring_invoice_line_ids)
            account.recurring_advance_total = sum(line.price_subtotal for line in account.recurring_advance_invoice_line_ids)

    def _amount_line_tax(self):
        self.ensure_one()
        val = 0.0
        product = self.product_id
        product_tmp = product.sudo().product_tmpl_id
        for tax in product_tmp.taxes_id.filtered(lambda t: t.company_id == self.analytic_account_id.company_id):
            fpos_obj = self.env['account.fiscal.position']
            partner = self.analytic_account_id.partner_id
            fpos_id = fpos_obj.with_context(force_company=self.analytic_account_id.company_id.id).get_fiscal_position(partner.id)
            fpos = fpos_obj.browse(fpos_id)
            if fpos:
                tax = fpos.map_tax(tax, product, partner)
            compute_vals = tax.compute_all(self.price_unit * (1 - (self.discount or 0.0) / 100.0), self.analytic_account_id.currency_id, self.quantity, product, partner)['taxes']
            if compute_vals:
                val += compute_vals[0].get('amount', 0)
        return val

    @api.depends('recurring_invoice_line_ids', 'recurring_total', 'recurring_advance_invoice_line_ids')
    def _amount_all(self):
        for account in self:
            account_sudo = account.sudo()
            val = val1 = 0.0
            cur = account_sudo.pricelist_id.currency_id
            for line in account_sudo.recurring_invoice_line_ids:
                val1 += line.price_subtotal
                val += line._smn_amount_line_tax()
            account.acutual_cost_recurring_amount_tax = cur.round(val)
            account.actual_cost_recurring_amount_total = account.acutual_cost_recurring_amount_tax + account.recurring_total
            val = val1 = 0.0
            cur = account_sudo.pricelist_id.currency_id
            for line in account_sudo.recurring_advance_invoice_line_ids:
                val1 += line.price_subtotal
                val += line._smn_amount_line_tax()
            if not account.x_update_advance_amount:
                account.advance_recurring_amount_tax = cur.round(val)
                account.advance_recurring_amount_total = account.advance_recurring_amount_tax + account.recurring_advance_total
                account.recurring_amount_total = account.actual_cost_recurring_amount_total - account.advance_recurring_amount_total
            else:
                account.advance_recurring_amount_total = account.advance_recurring_amount_tax + account.recurring_advance_total
                account.recurring_amount_total = account.actual_cost_recurring_amount_total - account.advance_recurring_amount_total
            if not account.update_amount:
                account.amount_total = account.actual_cost_recurring_amount_total - account.advance_recurring_amount_total
                account.amount_tax = cur.round(val)

    @api.onchange('template_id')
    def onchange_filter_stage(self):
        role_obj = self.env['sale.subscription.stage.role']
        inv_line = []
        if self.template_id:
            for prod in self.template_id.product_ids:
                inv_line.append((0, 0, {
                    'quantity': prod.quantity or 1,
                    'product_id': prod.product_id and prod.product_id.id or 0,
                    'name': prod.name or '',
                    'uom_id': prod.uom_id.id,
                    'price_unit': prod.price_unit or 1,
                    'price_subtotal': prod.price_subtotal or 1,
                }))
            return {
                'value': {
                    'recurring_invoice_line_ids': inv_line,
                },
                'domain': {
                    'stage_id': [('id', 'in', [role_obj.browse(r.id).stage_id.id \
                                              for r in self.template_id.role_ids])]
                }
            }
        else:
            return {
                'value': {
                    'recurring_invoice_line_ids': [(5, [])],
                },
                'domain': {
                    'stage_id': [('id', 'in', [-1])]
                }
            }
        return {}
    @api.onchange('beneficiary')
    def _onchange_beneficiary(self):
        res_partner_bank = self.beneficiary.bank_ids and self.beneficiary.bank_ids[0] or False
        if res_partner_bank:
            self.beneficiary_account = res_partner_bank.acc_number
            self.beneficiary_bank = res_partner_bank.bank_id.id
        else:
            self.beneficiary_account = False
            self.beneficiary_bank = False

    @api.model
    def get_request_user(self):
        return self.env.uid

    @api.model
    def get_roles(self):
        sub_ids = self.search([('role_ids', '=', False)])
        if sub_ids:
            for sub in sub_ids:
                sub_info = self.browse(sub.id)
                for role in sub_info.template_id.role_ids:
                    role.copy(default={'sub_id': sub.id})
        role_obj = self.env['sale.subscription.stage.role']
        del_role_id = role_obj.search(['|', ('state', '!=', 'done'), 
                                       ('state', '=', False)])
        if del_role_id:
            for del_role in del_role_id:
                del_role.write({'name': ''})
        return True
    
    def get_stage_name(self):
        for record in self:
            if record.stage_id:
                record.stage_name = record.stage_id.name or ''

    def get_admin_debug(self):
        if self.env.uid == 2 and request.session.debug:
            self.admin_debug = True
        else:
            self.admin_debug = False

    def check_show_hide(self):
        user_obj = self.env['res.users']
        self.cur_user_id = False
        if not self.approve_users:        
            if self.env.ref("nc_sale_subscription.group_sale_subscription_approve").id \
                in [idd.id for idd in user_obj.browse(self.env.uid).sudo().groups_id] \
                and self.stage_id.code not in ['draft', 'Draft', 'DRAFT', 'paid', 'Done', 'DONE', 'reject', 'Reject', 'REJECT']:
                self.cur_user_id = True
        elif self.env.uid not in self.approve_users.ids or self.env.uid not in self.revertive_users.ids \
                or self.stage_id.code in ['draft', 'Draft', 'DRAFT', 'paid', 'Done', 'DONE', 'reject', 'Reject', 'REJECT']:
            self.cur_user_id = False
        else:
            self.cur_user_id = True

    def check_revert_cancel(self):
        for record in self:
            if record.stage_id.on_reject and record.cur_user_id:
                record.accept_recan = True
            else:
                record.accept_recan = False
    def _get_short_regarding_vn(self):
        for record in self:
            if record.regarding_vn:
                if len(record.regarding_vn) > 80:
                    record.short_regarding_vn = record.regarding_vn[:80] + '...'
                else:
                    record.short_regarding_vn = record.regarding_vn
            else:
                record.short_regarding_vn = ''
 
    # @api.depends('stage_id', 'sapprove_users')
    def get_approve_users(self):
        user_obj = self.env['res.users']
        # for record in self:
        #     approval_ids = []
        #     lst_email = []
        #     for re in record.sapprove_users:
        #         email = user_obj.browse(re.id).partner_id.email or ''
        #         if email:
        #             lst_email.append(email)
        #     record.approve_emails = '; '.join(lst_email)

    exp_date = fields.Date('Expired Date Approve')
    code = fields.Char(string='Proposal Code', size=256)
    date_start = fields.Date(string='Proposal Start Date')
    template_id = fields.Many2one('sale.subscription.template', string='Proposal Type')
    history_ids = fields.One2many('sale.subscription.result', 'sub_id', string='Activities')
    rhistory_id = fields.One2many('sale.subscription.stage.role.history', 'sub_id', string='History')
    content = fields.Html(string='Program Scheme')
    content_vn = fields.Html(string=u'Nội dung chương trình')
    definition = fields.Text(string='Definition')
    definition_vn = fields.Text(string=u'Định nghĩa')
    target_au = fields.Text(string='Target Audience')
    target_au_vn = fields.Text(string='Đối tượng mục tiêu')
    off_launch_from = fields.Date(string='Office Launch From')
    off_launch_to = fields.Date(string='Office Launch To')
    term = fields.Html(string='Term and Conditions')
    term_vn = fields.Html(string='Thể lệ và điều kiện')
    rol_resp = fields.Html(string='Role and Respond')
    rol_resp_vn = fields.Html(string='Vai trò và nhiệm vụ')
    benifit = fields.Html(string='Benefit')
    benifit_vn = fields.Html(string=u'Lợi ích mang lại')
    create_uid = fields.Many2one('res.users', string='Requested By', default=get_request_user)
    create_email = fields.Char(related='create_uid.partner_id.email', string='Email')
    approve_users = fields.Many2many(comodel_name='res.users', string='Approve By')
    revertive_users = fields.Many2many('res.users','sale_subscription_revert_user_rel', \
                                    'sale_subscription_id', 'res_users_id', string='Revert By')
    # sapprove_users = fields.Many2many(comodel_name='res.users', string='Approve By')
    rest_appr = fields.Char(string='Rest Approve', size=64)
    stage_name = fields.Char(string='Stage', compute=get_stage_name, size=256)
    # approve_emails = fields.Char(compute=get_approve_users, string='Email', size=256)
    # assign_user_id = fields.Many2one('res.users', string='Assigned To')
    # fassign_user_id = fields.Many2one('res.users', string='Assigned From')
    role_ids = fields.One2many('sale.subscription.stage.role', 'sub_id', string='Workflow')
    regarding = fields.Text(string='Regarding')
    regarding_vn = fields.Text(string=u'Về việc')
    admin_debug = fields.Boolean(string='Admin Debug', compute=get_admin_debug)
    version = fields.Char(string='Version', size=16, default='1')
    appr_time = fields.Datetime(string='Approved On')
    cur_user_id = fields.Boolean(string='Show Approve', compute=check_show_hide)
    stage_ids = fields.One2many('sale.subscription.stage', string = "Stage Ids", \
                                compute='_compute_stage_ids')
    accept_recan = fields.Boolean(string='Show Revert / Cancel', compute=check_revert_cancel)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, auto_join=True, default=1)
    stage_code = fields.Char(related='stage_id.code', string='Stage Code')
    auto_approval = fields.Boolean(string='Auto Approval')
    beneficiary = fields.Many2one('res.partner', string='Beneficiary')
    beneficiary_bank = fields.Many2one('res.bank', string='Beneficiary Bank')
    beneficiary_account = fields.Char(string='Beneficiary Account')
    transfer_method = fields.Selection([('cash', 'Cash'), ('transfer', 'Transfer')], string='Transfer Method')
    acutual_cost_recurring_amount_tax = fields.Float('Taxes', compute="_amount_all")
    actual_cost_recurring_amount_total = fields.Float('Total', compute="_amount_all")
    advance_recurring_amount_tax = fields.Float('Taxes') #, compute="_amount_all")
    advance_recurring_amount_total = fields.Float('Total', compute="_amount_all")
    budget_type = fields.Selection([('in_budget', 'in budget'), ('out_of_budget', 'Out Of Budget'), ('over_budget', 'Over Budget')], string='Budget Type')
    recurring_advance_invoice_line_ids = fields.One2many('advance.sale.subscription.line', 'analytic_account_id', string='Subscription Lines', copy=True)
    recurring_amount_total = fields.Float('Total', compute="_amount_all")
    recurring_advance_total = fields.Float(compute='_compute_recurring_total', string="Recurring Price", store=True, tracking=True)
    template_code = fields.Char(related='template_id.code', string="Proposal Code", store=True)
    gm_approver = fields.Many2one('res.users', string='GM Approver')
    approval_history = fields.Char('Approval History', default='[]')
    short_regarding_vn = fields.Char(string='Short Regarding VN', compute='_get_short_regarding_vn')
    update_amount = fields.Boolean('Update Amount', default=False)
    x_update_advance_amount  = fields.Boolean('Update Amount', default=False)
    amount_total = fields.Float('Amount Total')
    amount_tax = fields.Float('Amount Tax')
    x_paid_time = fields.Datetime('Paid on')

    @api.model
    def process_auto_reminder(self):
        subscript_obj = self.env['sale.subscription']
        pass_stage_ids = self.env['sale.subscription.stage'].search([\
                         ('code', 'in', ['Done', 'done', 'DONE', 'cancel', 'CANCEL', 'Cancel'])])
        pass_stage_ids = pass_stage_ids.ids
        domain = [('exp_date', '<', fields.Date.today())]
        if pass_stage_ids:
            domain.append(('stage_id', 'not in', pass_stage_ids))
        sub_ids = subscript_obj.search(domain)
        for idd in sub_ids:
            stage_obj = subscript_obj.browse(idd.id).stage_id
            template_obj = stage_obj.rating_template_id
            #   Auto change stage when expired date by cron job
            seq_stage_id = {}
            record = subscript_obj.browse(idd.id).sudo()
            role_obj = False
            for s in record.role_ids:
                if s.stage_id.sequence > record.stage_id.sequence:
                    seq_stage_id.update({s.stage_id.sequence: [s.stage_id.id, s]})

            for t in record.role_ids:
                if t.stage_id.id == record.stage_id.id:
                    role_obj = t
                
            if role_obj.alert_time and seq_stage_id:
                index = sorted(seq_stage_id.keys())
                record.sudo().write({'stage_id': seq_stage_id.get(index[0])[0]})
                role_obj.write({
                    'state': 'done', 
                    'name': 'Escalated by System', 
                    'appr_by': self.env.uid, 
                    'appr_time': fields.Datetime.now()
                })

            if template_obj:
                template_id = template_obj.id
                ctx = {
                    'force_email': True,
                    'default_res_id': idd.id,
                    'default_template_id': template_id,
                    'default_model': 'sale.subscription',                    
                    'default_composition_mode': 'comment',
                    'default_use_template': bool(template_id),                    
                }
                email_to = ''
                num_seq = 0
                for x in role_obj.approval_ids:
                    if x.partner_id.email:
                        if not num_seq:
                            email_to = x.partner_id.email
                        else:
                            email_to += ', ' + x.partner_id.email
                        num_seq += 1

                stage_obj.rating_template_id.write({'email_to': email_to})
                template_obj.with_context(ctx).send_mail(res_id=idd.id)
        return True


    def submit(self):
        previous_role, cur_role, next_role = self.get_related_role()
        stage_id = next_role and next_role.stage_id and next_role.stage_id.id or False
        accountant_id = self.env['ir.config_parameter'].sudo().get_param('nc_sale_subscription.accountant_id')
        accountant_id = safe_eval(accountant_id)
        default_next_approval_user_id = False
        if next_role and next_role.stage_id and next_role and next_role.stage_id.code == 'done':
            default_next_approval_user_id = accountant_id

        return {
                'name': 'Send Proposal',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.subscription.result',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref("nc_sale_subscription.sale_sub_box_view_form").id,
                'target': 'new',
                'context': {
                    'approve_type': 'previous', 
                    'stage_id': stage_id,
                    'type': 'send',
                    'default_sub_id': self.id, 
                    'default_user_id': self.env.uid,
                    'default_next_approval_user_id': default_next_approval_user_id,
                    'version': self.version,
                    'next_role_id': next_role and next_role.id or False
                },
            }

    def str2date(self, strdate):
        if strdate:
            strdate = str(strdate).split('-')
            return datetime.datetime(int(strdate[0]), int(strdate[1]), int(strdate[2]), 23, 59, 59)
        return fields.Datetime.now()

    # @api.multi
    def write(self, vals):
        vals.pop('payment_mode', False)
        vals.pop('recurring_rule_boundary', False)
        
        stage_done = self.env['sale.subscription.stage'].search([('code', 'in', \
                                                                 ['Done', 'done', 'DONE'])], limit=1)
        stage_draft = self.env['sale.subscription.stage'].search([('code', 'in', \
                                                                 ['Draft', 'draft', 'DRAFT'])], limit=1)
        stage_done = stage_done and stage_done.id or 0
        stage_draft = stage_draft and stage_draft.id or 0
        user_obj = self.env['res.users']
        tmp_obj = self.env['sale.subscription.template']
        for rr in self:
            cur_partner = user_obj.browse(self.env.uid).sudo().partner_id.id
            if rr.stage_id.id == stage_draft and not vals.get('stage_id', False):
                # for flower in rr.message_follower_ids:
                #     if flower.partner_id.id != cur_partner:
                #         rr.sudo().message_unsubscribe([flower.partner_id.id])
                for nr in rr.template_id.role_ids:
                    rr.sudo().message_subscribe(partner_ids=[l.partner_id.id for l in nr.approval_ids \
                                                if nr.approval_ids] + [rr.partner_id.id])
            if vals.get('template_id', False):
                for r1 in rr.role_ids:
                    r1.sudo().unlink()
                for nr in rr.template_id.role_ids:
                    nr.sudo().copy(default={'sub_id': rr.id})                    
        if vals.get('stage_id', False):
            message = _('''You can not change into this stage. Please contact to manager to do it!''')
            for record in self:
                if record.role_ids:
                    for role_info in record.role_ids:
                        if record.stage_id.id == role_info.stage_id.id:
                            # if role_info.approval_ids and self.env.uid not in [x.id  \
                            #                           for x in record.approve_users] \
                            #                           and self.env.uid != 1:                                
                            #     raise ValidationError(message)

                            for nrole_info in record.role_ids:
                                if vals['stage_id'] == nrole_info.stage_id.id:
                                    exp_date = self.date_by_adding_business_days(fields.Date.today(), nrole_info.alert_time)
                                    print("exp_date", exp_date)
                                    vals.update({'exp_date': str(exp_date)})
                                    # vals.update({'exp_date': str(fields.Date.today() \
                                    #                 + timedelta(days=nrole_info.alert_time))})
                                    if nrole_info.amount_limit > record.recurring_total:
                                        vals['stage_id'] = stage_done
                            break
        # if vals.get('off_launch_from', False):
        #     cur_date = fields.Datetime.now()
        #     off_launch_from = self.str2date(vals['off_launch_from'])
        #     if cur_date - off_launch_from >= timedelta(seconds=1):
        #         raise ValidationError('Please choose other date on office launch from!')
        if vals.get('off_launch_to', False) and vals.get('off_launch_from', False):
            off_launch_from = self.str2date(vals['off_launch_from'])
            off_launch_to = self.str2date(vals['off_launch_to'])
            if off_launch_from - off_launch_to >= timedelta(seconds=1) and off_launch_from - off_launch_to != timedelta(seconds=0):
                raise ValidationError('Launch date to must greater than launch date from!')
        for record in self:
            off_launch_from = False
            off_launch_to = False
            if vals.get('off_launch_to', False) and record.off_launch_from and 'off_launch_from' not in vals:
                off_launch_from = self.str2date(record.off_launch_from)
                off_launch_to = self.str2date(vals['off_launch_to'])
            elif vals.get('off_launch_from', False) and record.off_launch_to and 'off_launch_to' not in vals:
                off_launch_to = self.str2date(record.off_launch_to)
                off_launch_from = self.str2date(vals['off_launch_from'])
            if off_launch_from and off_launch_from:
                if off_launch_from - off_launch_to >= timedelta(seconds=1) and off_launch_from - off_launch_to != timedelta(seconds=0):
                    raise ValidationError('Launch date to must greater than launch date from!')
        return super(SaleSubscription, self).write(vals)
    
    def get_related_role(self):
        seq_stage_id = {}
        previous_stage_ids = {}
        for s in self.role_ids:
            if s.stage_id.id == self.stage_id.id:
                cur_role = s
            if s.stage_id.sequence > self.stage_id.sequence:
                seq_stage_id.update({s.stage_id.sequence: s})
            if s.stage_id.sequence < self.stage_id.sequence:
                previous_stage_ids.update({s.stage_id.sequence: s})
        index = sorted(seq_stage_id.keys())
        previous_stage_index = sorted(previous_stage_ids.keys(), reverse=True)
        next_role = index and seq_stage_id.get(index[0]) or False
        previous_role = previous_stage_index and previous_stage_ids[previous_stage_index[0]] or False
        return (previous_role, cur_role, next_role)

    # @api.multi
    def approve_next_stage(self):
        stage_id = False
        sale_subscription_stage_model = self.env['sale.subscription.stage']
        for record in self:
            previous_role, cur_role, next_role = record.get_related_role()
            # appr_users = [n.appr_by.id for n in cur_role.history_id if n.appr_by and n.state == 'appr']
            next_stage = False
            approved_users_number = len(cur_role.approval_ids) - len(record.approve_users)

            accountant_id = self.env['ir.config_parameter'].sudo().get_param('nc_sale_subscription.accountant_id')
            accountant_id = safe_eval(accountant_id)
            default_next_approval_user_id = False
            if next_role and next_role.stage_id and next_role and next_role.stage_id.code == 'done':
                default_next_approval_user_id = accountant_id
            # if record.stage_id.code == 'submit':
            #     if record.version == '1':
            #         next_stage = sale_subscription_stage_model.search([('code', '=', 'comment')])
            #     else:
            #         next_stage = sale_subscription_stage_model.search([('code', '=', 'review')])
                
            #     if approved_users_number >= (cur_role.appr_num - 1):
            #         if cur_role.appr_man.id not in record.approve_users.ids \
            #             or cur_role.appr_man.id == self.env.uid \
            #             or not cur_role.appr_man:
            #             stage_id = next_stage and next_stage.id or False
            #     if not cur_role.appr_num or not cur_role.approval_ids:
            #         stage_id = next_stage and next_stage.id or False
            # else: 
            stage_id = next_role and next_role.stage_id.id or False
            stage = next_role and next_role.stage_id or False
            # if approved_users_number >= (cur_role.appr_num - 1):
            #     if cur_role.appr_man.id not in record.approve_users.ids \
            #         or cur_role.appr_man.id == self.env.uid \
            #         or not cur_role.appr_man:
            #         stage_id = next_role and next_role.stage_id.id or False
            # if not cur_role.appr_num or not cur_role.approval_ids:
            #     stage_id = next_role and next_role.stage_id.id or False
            showing_bypass = False
            # appr_man = cur_role.appr_man and cur_role.appr_man.id or False
            # rev_man = cur_role.rev_man and cur_role.rev_man.id or False
            # if self.env.uid not in [appr_man, rev_man] and  self.stage_id.code == 'review':
            #     showing_bypass = True
            approval_user_ids = stage and stage.approval_ids.ids or False
            return {
                'name': SALE_SUBSCRIPTION_STATE_STRING.get(record.stage_id.code, 'Approve ') + ' Proposal',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.subscription.result',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref("nc_sale_subscription.sale_app_box_view_form").id,
                'target': 'new',
                'context': {
                    'stage_id': stage_id,
                    'type': SALE_SUBSCRIPTION_STATE_STAGE_CODE.get(record.stage_id.code, 'appr'),
                    'default_sub_id': record.id, 
                    'default_user_id': self.env.uid,
                    'version': record.version,
                    'default_next_approval_user_id': default_next_approval_user_id,
                    # 'next_role_id': next_role and next_role.id or False,
                    'default_showing_bypass': showing_bypass,
                    'approval_user_ids': approval_user_ids
                },
            }
    
    # @api.multi
    def reject(self):
        for record in self:
            return {
                'name': 'Reject',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.subscription.result',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref("nc_sale_subscription.sale_reject_box_view_form").id,
                'target': 'new',
                'context': {
                    'type': 'reject',
                    'default_sub_id': record.id, 
                    'default_user_id': self.env.uid,
                    'version': record.version
                },
            }

    def refuse_previous_stage(self):
        stage_id = 1
        for record in self:
            previous_role, cur_role, next_role = record.get_related_role()
            reverted_users_number = len(cur_role.approval_ids) - len(record.revertive_users)
            stage_id = previous_role.stage_id.id
            # draft_stage = self.env['sale.subscription.stage'].search([('code', '=', 'draft')])
            # print("draft_stage", draft_stage)
            # if reverted_users_number >= (cur_role.rev_num - 1):
            #     if not cur_role.rev_man \
            #         or cur_role.rev_man.id not in record.approve_users.ids \
            #         or cur_role.rev_man.id == self.env.uid:
            #         stage_id = draft_stage and draft_stage.id or False
            # if not stage_id and (not cur_role.appr_num or not cur_role.approval_ids):
            #     stage_id = draft_stage and draft_stage.id or False
            return {
                'name': 'Revert',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref("nc_sale_subscription.sale_subscription_revert").id,
                'res_model': 'sale.subscription.revert',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'approve_type': 'previous', 
                    'stage_id': stage_id,
                    'type': 'revert',
                    'default_sub_id': record.id, 
                    'default_user_id': self.env.uid,
                    # 'version': record.update_version(record.version),
                    'previous_role_id': previous_role and previous_role.id or False
                },
            }
    
    def assign_user(self):
        return {
            'name': 'Assign User',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.subscription.assign',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'approve_type': 'Assign', 
                    'type': 'assign',
                    'default_sub_id': self.id, 
                    'default_user_id': self.env.uid,
                },
        }

    @api.model
    def create(self, vals):
        vals.update({'code':self.env['ir.sequence'].next_by_code('sale.subscription') or
            'New'})
        vals.pop('payment_mode', False)
        vals.pop('recurring_rule_boundary', False)
        # if vals.get('off_launch_from', False):
        #     cur_date = fields.Datetime.now()
        #     off_launch_from = self.str2date(vals['off_launch_from'])
        #     if cur_date - off_launch_from >= timedelta(seconds=1):
        #         raise ValidationError('Please choose other date on office launch from!')
        if vals.get('off_launch_to', False) and vals.get('off_launch_from', False):
            off_launch_from = self.str2date(vals['off_launch_from'])
            off_launch_to = self.str2date(vals['off_launch_to'])
            if off_launch_from - off_launch_to >= timedelta(seconds=1) and off_launch_from - off_launch_to != timedelta(seconds=0):
                raise ValidationError('Launch date to must greater than launch date from!')
        result = super(SaleSubscription, self).create(vals)
        # body_html = self.env['mail.template']._render_template(result.stage_id.rating_template_id.body_html, 'sale.subscription', result.id)
        # body2 = result.stage_id.rating_template_id._render_template(result.stage_id.rating_template_id.lang, 'sale.subscription', result.id)
        if vals.get('template_id'):
            approval_ids = []
            template_obj = self.env['sale.subscription.template'].browse(vals['template_id'])
            for follower in template_obj.message_follower_ids:
                approval_ids.append(follower.partner_id.id)
            approval_ids = list(set(approval_ids))
            result.message_subscribe(partner_ids=approval_ids)
            for role in template_obj.role_ids:
                role.copy(default={'sub_id': result.id})
        return result

    @api.model
    def default_get(self, fields):
        if 'code' in fields:
            fields.remove('code')
        return super(SaleSubscription, self).default_get(fields)

    def date_by_adding_business_days(self, from_date, add_days):
        days_off = self.env['ir.config_parameter'].sudo().get_param('nc_sale_subscription.days_off')
        holidays = self.env['ir.config_parameter'].sudo().get_param('nc_sale_subscription.holidays')
        days_off = safe_eval(days_off)
        holidays = safe_eval(holidays)
        business_days_to_add = add_days
        current_date = from_date
        while business_days_to_add > 0:
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday in  days_off or current_date.strftime("%d/%m") in holidays: # sunday = 6
                continue
            business_days_to_add -= 1
        return current_date
    
    def get_role_by_stage_code(self, stage_code):
        for role in self.role_ids:
            if role.stage_id and role.stage_id.code == stage_code:
                return role
        return False
    
    def send_email_approve(self):
        template = self.env.ref('nc_sale_subscription.sale_subscription_reivew_email')
        if template:
            template_id = template and template.id or False
            email_to = self.create_uid.partner_id.email
            submit_role = self.get_role_by_stage_code(self.stage_id.code)
            # if submit_role:
            for x in self.approve_users:
                if x.partner_id.email:
                    email_to += ', ' + x.partner_id.email
            web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = f"{web_base_url}/web#id={self.id}&action=537&model=sale.subscription&view_type=form"
            if self.stage_id.code == 'done':
                email_to += ', accounting.vietnam@sucden.com'
            email_values = {
                    'force_email': True,
                    'default_res_id': self.id,
                    'default_template_id': template_id,
                    'default_model': 'sale.subscription',                    
                    'default_composition_mode': 'comment',
                    'default_use_template': bool(template_id),
                    'nc_email_to': email_to,           
                    'nc_url': url,           
            }
            # template.write({'email_to': email_to})
            template.with_context(email_values).send_mail(res_id=self.id, force_send=True)
    
    def send_email_revert(self):
        template = self.env.ref('nc_sale_subscription.sale_subscription_revert_email')
        if template:
            template_id = template and template.id or False
            email_to = self.create_uid.partner_id.email
            submit_role = self.get_role_by_stage_code('submit')
            # if submit_role:
            for x in self.approve_users:
                if x.partner_id.email:
                    email_to += ', ' + x.partner_id.email
            ctx = {
                    'force_email': True,
                    'default_res_id': self.id,
                    'default_template_id': template_id,
                    'default_model': 'sale.subscription',                    
                    'default_composition_mode': 'comment',
                    'default_use_template': bool(template_id),
                    'nc_email_to': email_to                   
                }
            template.with_context(ctx).send_mail(res_id=self.id)

    def send_email_assign(self, email_to):
        template = self.env.ref('nc_sale_subscription.sale_subscription_assign_email')
        if template:
            template_id = template and template.id or False
            ctx = {
                    'force_email': True,
                    'default_res_id': self.id,
                    'default_template_id': template_id,
                    'default_model': 'sale.subscription',                    
                    'default_composition_mode': 'comment',
                    'default_use_template': bool(template_id),
                    'nc_email_to': email_to              
                }
            template.with_context(ctx).send_mail(res_id=self.id)

    @api.model
    def schedule_auto_approval(self):
        sale_subscript_obj = self.env['sale.subscription']
        ignored_stages = self.env['sale.subscription.stage'].search([\
                         ('code', 'in', ['draft', 'approve', 'reject', 'cancel'])])
        ignored_stages_ids = ignored_stages.ids
        domain = [('exp_date', '<', fields.Date.today())]
        # if pass_stage_ids:
        #     domain.append(('stage_id', 'not in', pass_stage_ids))
        # sale_subscriptions = sale_subscript_obj.search(domain)
        # for idd in sub_ids:
        #     stage_obj = subscript_obj.browse(idd.id).stage_id
        #     template_obj = stage_obj.rating_template_id
        #     #   Auto change stage when expired date by cron job
        #     seq_stage_id = {}
        #     record = subscript_obj.browse(idd.id).sudo()
        #     role_obj = False
        #     for s in record.role_ids:
        #         if s.stage_id.sequence > record.stage_id.sequence:
        #             seq_stage_id.update({s.stage_id.sequence: [s.stage_id.id, s]})

        #     for t in record.role_ids:
        #         if t.stage_id.id == record.stage_id.id:
        #             role_obj = t
                
        #     if role_obj.alert_time and seq_stage_id:
        #         index = sorted(seq_stage_id.keys())
        #         record.sudo().write({'stage_id': seq_stage_id.get(index[0])[0]})
        #         role_obj.write({
        #             'state': 'done', 
        #             'name': 'Escalated by System', 
        #             'appr_by': self.env.uid, 
        #             'appr_time': fields.Datetime.now()
        #         })

        #     if template_obj:
        #         template_id = template_obj.id
        #         ctx = {
        #             'force_email': True,
        #             'default_res_id': idd.id,
        #             'default_template_id': template_id,
        #             'default_model': 'sale.subscription',                    
        #             'default_composition_mode': 'comment',
        #             'default_use_template': bool(template_id),                    
        #         }
        #         email_to = ''
        #         num_seq = 0
        #         for x in role_obj.approval_ids:
        #             if x.partner_id.email:
        #                 if not num_seq:
        #                     email_to = x.partner_id.email
        #                 else:
        #                     email_to += ', ' + x.partner_id.email
        #                 num_seq += 1

        #         stage_obj.rating_template_id.write({'email_to': email_to})
        #         template_obj.with_context(ctx).send_mail(res_id=idd.id)
        # return True
