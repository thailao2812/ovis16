# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError


class DeleteProtectionMixin(models.AbstractModel):
    """Blocks deletion of records that are already committed transactions.

    A record may not be deleted once either condition is true:

      1. it carries a real sequence number (the sequence field no longer
         holds one of the placeholder values), or
      2. its state / status has moved past the draft stage.

    Add the protection to a model by mixing this in::

        class PurchaseContract(models.Model):
            _name = 'purchase.contract'
            _inherit = ['purchase.contract', 'sd.delete.protection.mixin']

            _protect_sequence_field = 'name'
            _protect_state_fields = ('state',)
            _protect_draft_states = ('draft',)

    Every attribute below can be overridden per model. Fields that do not
    exist on the model are skipped, so an over-broad declaration is safe.
    """
    _name = 'sd.delete.protection.mixin'
    _description = 'Delete Protection Mixin'

    # Field holding the generated sequence. Set to None for models that never
    # generate one -- otherwise a plain label stored in ``name`` would be
    # mistaken for a sequence and block every deletion.
    _protect_sequence_field = 'name'

    # Values that mean "no sequence has been generated yet".
    _protect_sequence_placeholders = ('New', 'NEW', 'new', '/', '-', '')

    # Workflow fields to inspect, in order. Both 'state' and 'status' are used
    # across OVIS; some models carry both, in which case list only the one that
    # actually drives the workflow.
    _protect_state_fields = ('state',)

    # States from which deletion is still allowed.
    _protect_draft_states = ('draft',)

    # For line models: the many2one pointing at the parent document. The parent
    # is checked as well, so a line cannot be removed from a committed document
    # even when the line itself looks untouched.
    _protect_parent_field = None

    # Set on documents that must never be deleted, whatever their state. Use it
    # rather than leaning on the number: how a draft document is named is not
    # dependable -- draft journal entries here are variously called "Draft",
    # "INV-00019" or "BYP/93/2026-27" -- so a rule built on the number would
    # block them for a reason that is not true and would read as nonsense to
    # whoever hit it. This states the actual policy instead.
    # Note this does not reach the lines: `_protect_committed_state` is what the
    # parent rule consults, so a draft document is still editable line by line.
    _protect_never_delete = False

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def _protect_bypass_allowed(self):
        """Deletion is only forced through by a member of the dedicated group.

        The context flag alone is not enough: context is supplied by the client
        and must never be able to lift the protection on its own.
        """
        if self.env.context.get('module_uninstall'):
            # Odoo removes records as part of uninstalling a module; refusing
            # here would make modules impossible to uninstall.
            return True
        return bool(
            self.env.context.get('sd_force_delete')
            and self.env.user.has_group('sd_delete_protection.group_sd_force_delete')
        )

    def _protect_sequence_value(self):
        """Return the generated sequence, or False when none was issued yet."""
        field_name = self._protect_sequence_field
        if not field_name or field_name not in self._fields:
            return False
        value = self[field_name]
        if not isinstance(value, str):
            return False
        value = value.strip()
        if not value or value in self._protect_sequence_placeholders:
            return False
        return value

    def _protect_committed_state(self):
        """Return (field_name, value) for the first state past draft."""
        for field_name in self._protect_state_fields:
            if field_name not in self._fields:
                continue
            value = self[field_name]
            # An unset state means the record never entered the workflow.
            if value and value not in self._protect_draft_states:
                return field_name, value
        return None

    def _protect_state_label(self, field_name, value):
        """Human-readable state label, falling back to the raw value."""
        field = self._fields.get(field_name)
        try:
            selection = dict(field._description_selection(self.env))
        except Exception:
            return value
        return selection.get(value, value)

    def _protect_check_record(self):
        """Raise UserError when this single record may not be deleted."""
        self.ensure_one()
        label = self.display_name or _('this record')

        if self._protect_never_delete:
            raise UserError(_(
                'You cannot delete "%(name)s".\n\n'
                'This kind of document is never deleted, in any state, because '
                'the rest of the system refers back to it. Cancel it instead.'
            ) % {'name': label})

        sequence = self._protect_sequence_value()
        if sequence:
            raise UserError(_(
                'You cannot delete "%(name)s".\n\n'
                'This document has already been issued the number %(sequence)s. '
                'Records with a generated number must be cancelled instead of '
                'deleted, so that the numbering stays complete and auditable.'
            ) % {'name': label, 'sequence': sequence})

        committed = self._protect_committed_state()
        if committed:
            field_name, value = committed
            raise UserError(_(
                'You cannot delete "%(name)s".\n\n'
                'Its status is "%(state)s". Only records still in draft may be '
                'deleted; anything further along must be cancelled instead.'
            ) % {'name': label, 'state': self._protect_state_label(field_name, value)})

        self._protect_check_parent()

    def _protect_check_parent(self):
        """Block removing a line only once its parent has left draft.

        Deliberately looks at the parent's *state* alone and not at its whole
        protection. A parent that already carries a document number is still
        being drafted -- a stock picking is numbered the moment it is created,
        and a sale contract likewise -- and while it is in draft its lines have
        to stay editable, which includes removing them. Running the parent's
        full check here would refuse that and make ordinary editing impossible.
        """
        field_name = self._protect_parent_field
        if not field_name or field_name not in self._fields:
            return
        parent = self[field_name]
        # A parent that does not carry the mixin has nothing to enforce.
        if not parent or not hasattr(parent, '_protect_committed_state'):
            return
        parent = parent.sudo()
        committed = parent._protect_committed_state()
        if not committed:
            return
        field, value = committed
        raise UserError(_(
            'You cannot delete this line.\n\n'
            'It belongs to "%(parent)s", whose status is "%(state)s". '
            'Only lines of a draft document may be removed; put the document '
            'back to draft first, or cancel it.'
        ) % {
            'parent': parent.display_name,
            'state': parent._protect_state_label(field, value),
        })

    # ------------------------------------------------------------------
    # Override
    # ------------------------------------------------------------------
    def unlink(self):
        if not self._protect_bypass_allowed():
            for record in self:
                record._protect_check_record()
        return super(DeleteProtectionMixin, self).unlink()
