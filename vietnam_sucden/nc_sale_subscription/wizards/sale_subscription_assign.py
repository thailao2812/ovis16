# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleSubscriptionAssign(models.Model):
    _name = 'sale.subscription.assign'

    name = fields.Text(string='Result')
    sub_id = fields.Many2one('sale.subscription', string='Subscription')
    user_id = fields.Many2one('res.users', string='User')
    approval_id = fields.Many2one('res.users', string='Assign To')
    active = fields.Boolean(string='Active', default=False)

    def approve(self):
        context = self._context or {}
        history_obj = self.env['sale.subscription.stage.role.history']
        cur_user = self.env['res.users'].browse(self.env.uid).partner_id.name
        if context:
            sub_obj = self.env['sale.subscription']
            sale_subcription = sub_obj.browse(context['default_sub_id'])
            previous_role, current_role, next_role = sale_subcription.get_related_role()
            need_proval_users = sale_subcription.approve_users.ids
            
            if self.env.uid in sale_subcription.approve_users.ids:
                need_proval_users.remove(self.env.uid)
            need_proval_users.append(self.approval_id.id)

            revertive_users = sale_subcription.revertive_users.ids
            if self.env.uid in sale_subcription.revertive_users.ids:
                revertive_users.remove(self.env.uid)
            revertive_users.append(self.approval_id.id)
            sale_subcription.write({
                'approve_users': [(6, 0, need_proval_users)],
                'revertive_users': [(6, 0, revertive_users)]
            })

            role_vals = {}
            if current_role.appr_man and current_role.appr_man.id == self.env.uid:
                current_role.appr_man = self.approval_id.id
            if current_role.rev_man and current_role.rev_man.id == self.env.uid:
                current_role.rev_man = self.approval_id.id
            
            history_obj.create({
                        'name': 'Assigned %s -> %s : %s' % (cur_user, self.approval_id.partner_id.name, self.name),
                        'appr_time': fields.Datetime.now(),
                        'appr_by': self.env.uid,
                        'sub_id': sale_subcription.id,
                        'stage_id': sale_subcription.stage_id and sale_subcription.stage_id.id or 0,
                        'state': context.get('type')
                    })
            sale_subcription.sudo().message_subscribe(partner_ids=[self.approval_id.partner_id.id])
            sale_subcription.send_email_assign(self.approval_id.partner_id.email)
        return {'type': 'ir.actions.act_window_close'}
