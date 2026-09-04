# -*- coding: utf-8 -*-
"""The controlled way to delete a protected record.

One generic wizard serves every protected model: it reads ``active_model`` and
``active_ids`` from the context rather than knowing anything about the document
in front of it.

What makes it appear in the cog menu of each document is a binding -- an
``ir.actions.act_window`` whose ``binding_model_id`` points at that model. Those
are generated in ``_register_hook`` rather than written by hand, so the list of
entry points is derived from the protection itself and cannot drift away from it.

``_register_hook`` is the right moment for that: it runs once the whole registry
is built, which is the earliest point where every module has had the chance to
mix the protection into its models. An install hook on this module would run too
early -- the modules that carry the protected documents are installed after it.
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

FORCE_GROUP = 'sd_delete_protection.group_sd_force_delete'
BINDING_PREFIX = 'force_delete_binding_'
MODULE = 'sd_delete_protection'


class ForceDeleteWizard(models.TransientModel):
    _name = 'sd.force.delete.wizard'
    _description = 'Force Delete Protected Records'

    reason = fields.Text(
        string='Reason', required=True,
        help='Why this record has to be removed rather than cancelled. '
             'Stored permanently in the deletion audit log.')
    model_label = fields.Char(string='Document Type', readonly=True)
    record_count = fields.Integer(string='Records', readonly=True)
    record_summary = fields.Text(string='About to be deleted', readonly=True)

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        records = self._target_records()
        if not records:
            return result
        result['model_label'] = self.env['ir.model']._get(records._name).name or records._name
        result['record_count'] = len(records)
        lines = []
        for record in records[:20]:
            try:
                label = record.display_name
            except Exception:
                label = '%s,%s' % (record._name, record.id)
            state = ''
            for candidate in ('state', 'status'):
                if candidate in record._fields and record[candidate]:
                    state = ' [%s]' % record[candidate]
                    break
            lines.append('- %s%s' % (label, state))
        if len(records) > 20:
            lines.append(_('... and %s more') % (len(records) - 20))
        result['record_summary'] = '\n'.join(lines)
        return result

    @api.model
    def _target_records(self):
        """The records the cog menu was opened on."""
        model_name = self.env.context.get('active_model')
        if not model_name or model_name not in self.env:
            # An empty recordset of the wizard itself: the callers only test it
            # for truthiness, and borrowing an unrelated model to mean "nothing"
            # reads as a mistake.
            return self.browse()
        ids = self.env.context.get('active_ids')
        if not ids and self.env.context.get('active_id'):
            ids = [self.env.context['active_id']]
        return self.env[model_name].browse(ids or []).exists()

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------
    def action_force_delete(self):
        self.ensure_one()
        # Checked again here on purpose. Hiding the menu entry is presentation;
        # this is the part that actually holds.
        if not self.env.user.has_group(FORCE_GROUP):
            raise AccessError(_('You are not allowed to force the deletion of protected records.'))
        if not (self.reason or '').strip():
            raise UserError(_('A reason is required.'))

        records = self._target_records()
        if not records:
            raise UserError(_('There is nothing left to delete -- the records are already gone.'))

        _logger.warning(
            'Force delete by %s on %s %s: %s',
            self.env.user.login, records._name, records.ids, self.reason.strip())

        records.with_context(
            sd_force_delete=True,
            sd_force_delete_reason=self.reason.strip(),
        ).unlink()
        return {'type': 'ir.actions.act_window_close'}

    # ------------------------------------------------------------------
    # Binding generation
    # ------------------------------------------------------------------
    def _register_hook(self):
        result = super()._register_hook()
        try:
            self.sudo()._sync_force_delete_bindings()
        except Exception:
            # A failure here must never stop the registry from loading.
            _logger.exception('Could not synchronise the force-delete bindings')
        return result

    @api.model
    def _protected_model_names(self):
        """Models that carry the protection and are reachable from the interface.

        A protected model with no window action -- contract lines and other
        sub-records -- is skipped: those are removed inside their parent form,
        never from a cog menu, so a binding there would be dead weight.
        """
        names = []
        for name, model in self.env.registry.items():
            if name == 'sd.delete.protection.mixin':
                continue
            if model._abstract or model._transient:
                continue
            if not hasattr(model, '_protect_check_record'):
                continue
            names.append(name)
        if not names:
            return []
        self.env.cr.execute(
            'SELECT DISTINCT res_model FROM ir_act_window WHERE res_model IN %s',
            (tuple(names),))
        with_action = {row[0] for row in self.env.cr.fetchall()}
        return sorted(n for n in names if n in with_action)

    @api.model
    def _sync_force_delete_bindings(self):
        """Create one binding per protected model, once. Safe to re-run."""
        group = self.env.ref(FORCE_GROUP, raise_if_not_found=False)
        if not group:
            return 0
        model_data = self.env['ir.model.data']
        actions = self.env['ir.actions.act_window']
        created = 0
        for name in self._protected_model_names():
            xml_name = BINDING_PREFIX + name.replace('.', '_')
            if model_data.search_count([('module', '=', MODULE), ('name', '=', xml_name)]):
                continue
            model = self.env['ir.model']._get(name)
            if not model:
                continue
            action = actions.create({
                'name': _('Force Delete'),
                'res_model': self._name,
                'view_mode': 'form',
                'target': 'new',
                'binding_model_id': model.id,
                'binding_type': 'action',
                'binding_view_types': 'list,form',
                'groups_id': [(6, 0, [group.id])],
            })
            model_data.create({
                'module': MODULE,
                'name': xml_name,
                'model': 'ir.actions.act_window',
                'res_id': action.id,
                'noupdate': True,
            })
            created += 1
        if created:
            _logger.info('Created %s force-delete binding(s)', created)
        return created
