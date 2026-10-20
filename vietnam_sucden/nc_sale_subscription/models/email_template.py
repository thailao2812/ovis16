# -*- coding: utf-8 -*-
from odoo import api, fields, models

class EmailTemplate(models.Model):
    _inherit = 'mail.template'
    _description = ''
    to_followers = fields.Boolean('Send to Followers', default=False)
    to_assigns = fields.Boolean('Send to Assigns', default=False)

    def generate_recipients(self, results, res_ids):
        self.ensure_one()
        context = self.env.context or {}
        if self.to_followers:
            if context.get('default_model', False):
                cur_obj = self.env[context['default_model']].browse(res_ids[0])
                followers = []
                for follow in  cur_obj.message_follower_ids:
                    followers.append(str(follow.partner_id.id))
                followers = list(set(followers))
            results[res_ids[0]]['partner_to'] = ', '.join(followers)
        if self.to_assigns:
            if context.get('default_model', False):
                cur_obj = self.env[context['default_model']].browse(res_ids[0])
                assigned_users = []
                for follow in  cur_obj.approve_users:
                    assigned_users.append(str(follow.partner_id.id))
                assigned_users = list(set(assigned_users))
            results[res_ids[0]]['partner_to'] = ', '.join(assigned_users)
        
        return super(EmailTemplate, self).generate_recipients(results, res_ids)


class EmailEmail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, vals):
        return super(EmailEmail, self).create(vals)


# class RatingMixin(models.AbstractModel):
#     _inherit = 'rating.mixin'

#     @api.multi
#     def rating_send_request(self, template, lang=False, subtype_id=False, force_send=True, composition_mode='comment', notif_layout=None):
#         if lang:
#             template = template.with_context(lang=lang)
#         if subtype_id is False:
#             subtype_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note')
#         if force_send:
#             self = self.with_context(mail_notify_force_send=True)
        # for record in self:
        #     record.message_post_with_template(
        #         template.id,
        #         composition_mode=composition_mode,
        #         notif_layout=notif_layout if notif_layout is not None else 'mail.mail_notification_light',
        #         subtype_id=subtype_id
        #     )