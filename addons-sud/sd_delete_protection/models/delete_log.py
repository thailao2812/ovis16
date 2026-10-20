# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError


class DeleteLog(models.Model):
    """An append-only record of every deletion that actually took place.

    Rows are written by the audit hook in ``base_delete_audit.py`` using sudo,
    which is why no group is granted create rights: the only way a row appears
    is through that hook. Rows can never be edited, and can only be removed by
    a system administrator who explicitly asks for a purge -- otherwise the log
    would be as deletable as the data it is meant to account for.
    """
    _name = 'sd.delete.log'
    _description = 'Deletion Audit Log'
    _order = 'deleted_on desc, id desc'
    _rec_name = 'record_label'

    # --- what was deleted -------------------------------------------------
    model_name = fields.Char(string='Model', required=True, index=True, readonly=True)
    model_label = fields.Char(string='Document Type', readonly=True)
    res_id = fields.Integer(string='Record ID', required=True, index=True, readonly=True)
    record_label = fields.Char(string='Record', readonly=True)
    reference = fields.Char(
        string='Number', readonly=True, index=True,
        help='The sequence number the record carried when it was deleted.')
    state_value = fields.Char(string='Status at Deletion', readonly=True)

    # --- who and when -----------------------------------------------------
    deleted_by = fields.Many2one('res.users', string='Deleted By', required=True,
                                 index=True, readonly=True, ondelete='restrict')
    deleted_on = fields.Datetime(string='Deleted On', required=True, index=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    # --- how --------------------------------------------------------------
    was_protected = fields.Boolean(
        string='Protected Model', readonly=True,
        help='The model carries delete protection, so this deletion would '
             'normally have been refused.')
    bypassed_protection = fields.Boolean(
        string='Protection Bypassed', readonly=True, index=True,
        help='Deletion went through only because the user held the force '
             'delete right and asked for it explicitly. These are the rows '
             'worth reviewing.')
    bypass_reason = fields.Text(
        string='Reason Given', readonly=True,
        help='The justification the user typed in the force-delete wizard. '
             'Only present when the protection was bypassed.')
    cascaded_from = fields.Char(
        string='Deleted Together With', readonly=True, index=True,
        help='Set when the record was not deleted directly but removed by the '
             'database along with the parent named here. No unlink() ran on it, '
             'so this entry is the only trace it ever existed.')
    source = fields.Selection(
        [('user', 'User Action'), ('uninstall', 'Module Uninstall')],
        string='Source', readonly=True, default='user')

    # --- the record itself ------------------------------------------------
    record_data = fields.Text(
        string='Record Snapshot', readonly=True,
        help='Stored field values as they were immediately before deletion. '
             'Empty when the deletion was too large to snapshot.')

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------
    def write(self, vals):
        raise UserError(_(
            'Deletion audit records cannot be modified.\n\n'
            'The log would be worthless as evidence if entries could be '
            'edited after the fact.'))

    def unlink(self):
        if not self.env.su and not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Only a system administrator may purge the deletion audit log.'))
        if not self.env.context.get('sd_purge_delete_log'):
            raise UserError(_(
                'Deletion audit records cannot be deleted from the interface.\n\n'
                'A purge has to be run deliberately, with sd_purge_delete_log '
                'set in the context, so that it is always an explicit act.'))
        return super(DeleteLog, self).unlink()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def action_open_record(self):
        """Best-effort jump to the deleted record's model, for context."""
        self.ensure_one()
        if self.model_name not in self.env:
            raise UserError(_('The model %s no longer exists in this database.') % self.model_name)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.model_name,
            'view_mode': 'tree,form',
            'name': self.model_label or self.model_name,
        }
