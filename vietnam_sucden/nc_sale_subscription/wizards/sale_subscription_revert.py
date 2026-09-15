# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleSubscriptionRevert(models.Model):
    _name = 'sale.subscription.revert'

    name = fields.Text(string='Revert')
    user_id = fields.Many2one('res.users', string='User')
    active = fields.Boolean(string='Active', default=False)
    sub_id = fields.Many2one('sale.subscription', string='Subscription')
    stage_id = fields.Many2one('sale.subscription.stage', string='Stage')    
    # revert_user_id = fields.Many2one('res.users', string='User')
    # @api.multi
    def approve(self):
        context = self._context or {}
        history_obj = self.env['sale.subscription.stage.role.history']
        sale_subscription_stage_role_obj = self.env['sale.subscription.stage.role']
        if context:
            sub_obj = self.env['sale.subscription']
            stage_id = context.get('stage_id') or False
            previous_role_id = context.get('previous_role_id') or False
            previous_role = sale_subscription_stage_role_obj.search([('id', '=', previous_role_id)])
            role_state = 'done' if stage_id else 'open'
            comment = ''
            sale_subcription = sub_obj.browse(context['default_sub_id'])
            # self.write({'active': True})
            flag = False
            # if context.get('stage_id'):
            #     state = 'done'                
            for sale_subcription_result in self:
                comment = sale_subcription_result.name
                for role in sale_subcription.role_ids:
                    if role.stage_id.id == sale_subcription.stage_id.id:
                        flag = 1
                        role.write({
                            'state': role_state, 
                            'name': comment, 
                            'appr_time': fields.Datetime.now(),
                            'appr_by': self.env.uid
                        })
                        history_obj.create({
                            'name': comment,
                            'appr_time': fields.Datetime.now(),
                            'appr_by': self.env.uid,
                            'sub_id': sale_subcription.id,
                            'stage_id': sale_subcription.stage_id and sale_subcription.stage_id.id or 0,
                            'role_id': role.id,
                            'amount_limit': role.amount_limit,
                            'state': context.get('type'),
                            'version': context.get('version')
                        })
                        revertive_users = sale_subcription.revertive_users.ids
                        if self.env.uid in sale_subcription.revertive_users.ids:
                            revertive_users.remove(self.env.uid)
                        sale_subcription.write({
                            'revertive_users': [(6, 0, revertive_users)]
                        })
                        break
                
            if stage_id:
                approval_ids = sale_subcription.approval_history and eval(sale_subcription.approval_history) or []
                revert_user_id = approval_ids.pop()
                revert_user = self.env['res.users'].search([('id', '=', revert_user_id)])
                sale_subcription.approval_history = approval_ids
                sale_subcription.write({
                    'stage_id': stage_id,
                    # 'assign_user_id': 0,
                    # 'fassign_user_id': 0,
                    # 'rest_appr': context.get('type') == 'revert' and '' or sale_subcription.rest_appr,
                    'appr_time': fields.Datetime.now(),
                    'version': context.get('version'),
                    'approve_users': [(6,0, [revert_user.id])],
                    'revertive_users': [(6,0, [revert_user.id])] 
                })
            message_follower_ids = []
            for follower in sale_subcription.message_follower_ids:
                message_follower_ids.append(follower.partner_id.id)
            message_follower_ids.append(revert_user.partner_id.id)
            message_follower_ids = list(set(message_follower_ids))
            sale_subcription.message_subscribe(partner_ids=message_follower_ids)
            sale_subcription.send_email_revert()
                
        return {'type': 'ir.actions.act_window_close'}
