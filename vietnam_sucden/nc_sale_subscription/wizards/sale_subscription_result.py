# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleSubscriptionResult(models.Model):
    _name = 'sale.subscription.result'

    def _get_default_next_approval_user_id(self):
        context = self._context or {}
        print(context)
        return context.get('default_next_approval_user_id', False)
    
    def _get_next_approval_user_id(self):
        context = self._context or {}
        user_ids = context.get('approval_user_ids', False)
        print(user_ids)
        if user_ids:
            return [('id', 'in', user_ids)]
        return [('employee_id.is_manager', '=', True)]

    name = fields.Text(string='Result')
    user_id = fields.Many2one('res.users', string='User')
    rest_uid = fields.Many2many('res.users', 'result_user_rel', 'result_id',\
                                'user_id', string='Need to Approve')
    active = fields.Boolean(string='Active', default=False)
    sub_id = fields.Many2one('sale.subscription', string='Subscription')
    stage_id = fields.Many2one('sale.subscription.stage', string='Stage')
    stage_code = fields.Char(string='stage_code')
    # main_approval_user_id = fields.Many2one('res.users', string='Main Approval')
    # main_revert_user_id = fields.Many2one('res.users', string='Main Revert')
    bypass = fields.Boolean(string='Bypass')
    showing_bypass = fields.Boolean(string=' Showing Bypass')
    next_approval_user_id = fields.Many2one('res.users', string='User', default=_get_default_next_approval_user_id, domain=_get_next_approval_user_id)

    # @api.one
    def reject(self):
        context = self._context or {}
        sub_obj = self.env['sale.subscription']
        history_obj = self.env['sale.subscription.stage.role.history']
        reject_stage_id = self.env['sale.subscription.stage'].search([('code', 'in', \
                                                                 ['Reject', 'reject', 'REJECT'])], limit=1)
        reject_stage_id = reject_stage_id and reject_stage_id.id or 0
        sale_subcription = sub_obj.browse(context['default_sub_id'])
        if context and reject_stage_id:
            history_obj.create({
                'name': self.name,
                'appr_time': fields.Datetime.now(),
                'appr_by': self.env.uid,
                'sub_id': sale_subcription.id,
                'stage_id': sale_subcription.stage_id and sale_subcription.stage_id.id or 0,
                'state': 'reject',
                'version': context.get('version')
            })
            sale_subcription.write({'stage_id': reject_stage_id})
        return {'type': 'ir.actions.act_window_close'}

    # @api.multi
    def approve(self):
        context = self._context or {}
        history_obj = self.env['sale.subscription.stage.role.history']
        sale_subscription_stage_role_obj = self.env['sale.subscription.stage.role']
        if context:
            sub_obj = self.env['sale.subscription']
            stage_id = context.get('stage_id') or False
            # sale_subscription_stage = self.env['sale.subscription.stage'].search([('id', '=', stage_id)])
            # next_role_id = context.get('next_role_id') or False
            next_role = sale_subscription_stage_role_obj.search([('sub_id', '=', context['default_sub_id']), ('stage_id', '=', stage_id)])
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
                            'version': context.get('version'),
                            'is_bypass': sale_subcription_result.bypass,
                        })
                        # need_proval_users = sale_subcription.approve_users.ids
                        # if self.env.uid in sale_subcription.approve_users.ids:
                        #     need_proval_users.remove(self.env.uid)
                        # sale_subcription.write({
                        #     'approve_users': [(6, 0, need_proval_users)]
                        # })
                        
                        # if sale_subcription_result.bypass:
                        #     role_approval_ids = role.approval_ids.ids
                        #     role_approval_ids.remove(self.env.uid)
                        #     role.write({
                        #         'approval_ids': [(6, 0, [self.next_approval_user_id])],
                        #         'appr_num' : role.appr_num - 1  if role.appr_num > 1 else role.appr_num,
                        #         'rev_num' : role.rev_num - 1 if role.rev_num > 1 else role.rev_num,
                        #     })
                        #     revertive_users = sale_subcription.revertive_users.ids
                        #     if self.env.uid in sale_subcription.revertive_users.ids:
                        #         revertive_users.remove(self.env.uid)
                        #     sale_subcription.write({
                        #         'revertive_users': [(6, 0, revertive_users)]
                        #     })
                        break
                    # if sale_subcription.stage_id.code == 'review':
                
                    

            if stage_id:
                
                # stage = self.env['stage.subscription.stage'].search([('id', '=', stage_id)])
                sale_subcription.write({
                    'stage_id': stage_id,
                    # 'assign_user_id': 0,
                    # 'fassign_user_id': 0,
                    # 'rest_appr': context.get('type') == 'revert' and '' or sale_subcription.rest_appr,
                    'appr_time': fields.Datetime.now(),
                    'version': context.get('version'),
                    'approve_users': [(6,0, [self.next_approval_user_id.id])],
                    'revertive_users': [(6,0, [self.next_approval_user_id.id])]
                })
                if sale_subcription.stage_id.code == 'approved':
                    sale_subcription.gm_approver = self.next_approval_user_id.id
                approval_ids = sale_subcription.approval_history and eval(sale_subcription.approval_history) or []
                approval_ids.append(self.env.uid)
                sale_subcription.approval_history = approval_ids
                
                message_follower_ids = []
                for follower in sale_subcription.message_follower_ids:
                    message_follower_ids.append(follower.partner_id.id)
                message_follower_ids.append(self.next_approval_user_id.partner_id.id)
                message_follower_ids = list(set(message_follower_ids))
                sale_subcription.message_subscribe(partner_ids=message_follower_ids)
            sale_subcription.send_email_approve()
                
        return {'type': 'ir.actions.act_window_close'}
