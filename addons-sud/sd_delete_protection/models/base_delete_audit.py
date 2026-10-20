# -*- coding: utf-8 -*-
"""System-wide deletion audit.

Inheriting ``base`` attaches this to every model in the registry, which is what
makes the log complete: a deletion is recorded no matter which model, menu or
RPC call it came from, and regardless of whether the record was protected.

Two things keep that from becoming unusable. Transient records and a denylist
of technical models are skipped, because logging cron triggers and bus messages
would bury the business events the log exists for. And very large deletions are
recorded without a field snapshot, so a bulk clean-up cannot blow up memory.

Both limits are tunable from Settings > Technical > System Parameters without
touching this file.
"""
import json
import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Models whose deletions are pure technical churn. Logging them would add tens
# of thousands of rows a day and hide the events that matter.
#
# The chatter models matter most here. Deleting one document with a chatter also
# removes its messages, followers, activities and tracking values, so a single
# business deletion would otherwise produce a handful of empty-looking rows --
# no record label, no number, not protected -- each carrying a snapshot of the
# message body. The document's own row already says everything worth keeping.
TECHNICAL_MODELS = {
    'sd.delete.log',            # never audit the audit log -- infinite regress
    # chatter side-effects of deleting a document
    'mail.message',
    'mail.message.reaction',
    'mail.message.schedule',
    'mail.link.preview',
    'mail.activity',
    'mail.notification',
    'mail.mail',
    'mail.tracking.value',
    'mail.followers',
    # transport and housekeeping
    'bus.bus',
    'bus.presence',
    'ir.logging',
    'ir.cron.trigger',
    'ir.attachment.cleanup',
    'ir.model.data',
    'ir.property',
    'ir.sessions',
    'res.users.log',
    'web.tour',
}

# Field types worth snapshotting. Binary and heavy relational fields are left
# out on purpose: the point is to show what the record said, not to clone it.
SNAPSHOT_TYPES = {
    'char', 'text', 'integer', 'float', 'monetary', 'boolean',
    'date', 'datetime', 'selection', 'html',
}

MAX_SNAPSHOT_RECORDS = 200
MAX_SNAPSHOT_CHARS = 8000
# Cascades chain: a line may itself cascade further. Bounded so a pathological
# schema cannot turn one delete into an unbounded walk.
MAX_CASCADE_DEPTH = 5


class Base(models.AbstractModel):
    _inherit = 'base'

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @api.model
    def _delete_audit_excluded_models(self):
        """Technical denylist plus anything the administrator has added."""
        extra = self.env['ir.config_parameter'].sudo().get_param(
            'sd_delete_log.excluded_models', default='')
        custom = {m.strip() for m in extra.split(',') if m.strip()}
        return TECHNICAL_MODELS | custom

    @api.model
    def _delete_audit_max_snapshot(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'sd_delete_log.max_snapshot_records', default=MAX_SNAPSHOT_RECORDS)
        try:
            return int(value)
        except (TypeError, ValueError):
            return MAX_SNAPSHOT_RECORDS

    def _delete_audit_enabled(self):
        """Whether this particular deletion should be written to the log."""
        if not self.env.registry.ready:
            # During install or upgrade the log table may not exist yet.
            return False
        if self._transient or self._abstract:
            return False
        if self._name in self._delete_audit_excluded_models():
            return False
        if self.env.context.get('module_uninstall') and not self.env['ir.config_parameter'] \
                .sudo().get_param('sd_delete_log.log_uninstall'):
            # Uninstalling a module deletes its whole data set; logging that
            # produces thousands of meaningless rows. Opt in if you want it.
            return False
        return 'sd.delete.log' in self.env

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------
    def _delete_audit_snapshot(self):
        """Readable dump of the record's stored values, or '' if not worth it."""
        values = {}
        for name, field in self._fields.items():
            if not field.store or field.type not in SNAPSHOT_TYPES:
                continue
            try:
                value = self[name]
            except Exception:
                continue
            if value in (False, None, ''):
                continue
            values[name] = value.isoformat() if hasattr(value, 'isoformat') else value
        # Many2one fields are recorded by label, which is what a reader wants.
        for name, field in self._fields.items():
            if field.store and field.type == 'many2one':
                try:
                    related = self[name]
                except Exception:
                    continue
                if related:
                    values[name] = f'{related.display_name} (#{related.id})'
        try:
            dumped = json.dumps(values, ensure_ascii=False, indent=1, default=str)
        except Exception:
            dumped = str(values)
        if len(dumped) > MAX_SNAPSHOT_CHARS:
            dumped = dumped[:MAX_SNAPSHOT_CHARS] + '\n... (truncated)'
        return dumped

    def _delete_audit_values(self, with_snapshot=True):
        """Build one log row for this single record."""
        self.ensure_one()
        protected = hasattr(self, '_protect_check_record')

        # Every read below is guarded: a computed field that raises must not be
        # able to stop a deletion from being recorded.
        reference = False
        if protected:
            try:
                reference = self._protect_sequence_value()
            except Exception:
                reference = False
        if not reference and 'name' in self._fields:
            try:
                reference = self.name if isinstance(self.name, str) else False
            except Exception:
                reference = False

        state_value = False
        for candidate in ('state', 'status'):
            if candidate not in self._fields:
                continue
            try:
                value = self[candidate]
            except Exception:
                continue
            if value:
                state_value = str(value)
                break

        try:
            label = self.display_name
        except Exception:
            label = f'{self._name},{self.id}'

        try:
            company_id = self.company_id.id if (
                'company_id' in self._fields and self.company_id) else False
        except Exception:
            company_id = False

        try:
            model_label = self.env['ir.model'].sudo()._get(self._name).name or self._name
        except Exception:
            model_label = self._name

        bypassed = protected and bool(self.env.context.get('sd_force_delete'))
        reason = self.env.context.get('sd_force_delete_reason') if bypassed else False

        return {
            'model_name': self._name,
            'model_label': model_label,
            'res_id': self.id,
            'record_label': label,
            'reference': reference or False,
            'state_value': state_value,
            'deleted_by': self.env.uid,
            'deleted_on': fields.Datetime.now(),
            'company_id': company_id,
            'was_protected': protected,
            'bypassed_protection': bypassed,
            'bypass_reason': reason or False,
            'source': 'uninstall' if self.env.context.get('module_uninstall') else 'user',
            'record_data': self._delete_audit_snapshot() if with_snapshot else '',
        }

    # ------------------------------------------------------------------
    # Cascade
    # ------------------------------------------------------------------
    # PostgreSQL removes ON DELETE CASCADE children itself. The ORM never calls
    # unlink() on them, so without the code below a deleted contract takes its
    # lines -- and anything else pointing at it with cascade -- out of the
    # database silently: no protection check, no audit entry. The parent's own
    # row would be the only trace, which is exactly the gap this closes.
    @api.model
    @tools.ormcache()
    def _cascade_child_tables(self):
        """parent table -> [(child table, child column)] for ON DELETE CASCADE.

        Read from the catalogue rather than from the field definitions: what
        matters is the constraint the database will actually act on.
        """
        self.env.cr.execute("""
            SELECT tgt.relname, src.relname, att.attname
              FROM pg_constraint c
              JOIN pg_class src ON src.oid = c.conrelid
              JOIN pg_class tgt ON tgt.oid = c.confrelid
              JOIN pg_attribute att ON att.attrelid = c.conrelid
                                   AND att.attnum = c.conkey[1]
             WHERE c.contype = 'f'
               AND c.confdeltype = 'c'
               AND array_length(c.conkey, 1) = 1
        """)
        graph = {}
        for parent_table, child_table, child_column in self.env.cr.fetchall():
            graph.setdefault(parent_table, []).append((child_table, child_column))
        return graph

    @api.model
    @tools.ormcache()
    def _table_to_model(self):
        return {
            model._table: name
            for name, model in self.env.registry.items()
            if not model._abstract and not model._transient and model._table
        }

    def _cascade_deleted_records(self):
        """[(model name, ids)] the database will remove along with ``self``.

        Follows the chain, since a child may cascade further. Tables with no
        model behind them -- many2many link tables -- are skipped: those rows
        are references, not records, and have no identity worth logging.
        """
        graph = self._cascade_child_tables()
        if not graph:
            return []
        table_to_model = self._table_to_model()
        collected = []
        # Seeded with our own rows: a self-referencing cascade (a contract
        # pointing at another contract, say) would otherwise walk back to the
        # records being deleted and log them a second time, once as themselves
        # and once as their own cascade.
        seen = {(self._table, record_id) for record_id in self.ids}
        frontier = [(self._table, list(self.ids))]
        for _depth in range(MAX_CASCADE_DEPTH):
            next_frontier = []
            for table, ids in frontier:
                for child_table, child_column in graph.get(table, ()):
                    model_name = table_to_model.get(child_table)
                    if not model_name:
                        continue
                    try:
                        self.env.cr.execute(
                            'SELECT id FROM "%s" WHERE "%s" IN %%s'
                            % (child_table, child_column), (tuple(ids),))
                        child_ids = [row[0] for row in self.env.cr.fetchall()]
                    except Exception:
                        _logger.exception(
                            'Could not read cascade children in %s', child_table)
                        continue
                    child_ids = [i for i in child_ids if (child_table, i) not in seen]
                    if not child_ids:
                        continue
                    seen.update((child_table, i) for i in child_ids)
                    collected.append((model_name, child_ids))
                    next_frontier.append((child_table, child_ids))
            if not next_frontier:
                break
            frontier = next_frontier
        return collected

    def _cascade_check_protection(self, cascade):
        """Refuse the parent when a cascade would destroy a committed child."""
        for model_name, ids in cascade:
            model = self.env[model_name]
            if not hasattr(model, '_protect_check_record'):
                continue
            for child in model.sudo().browse(ids).exists():
                try:
                    child._protect_check_record()
                except UserError as error:
                    raise UserError(_(
                        'You cannot delete "%(parent)s".\n\n'
                        'Doing so would also delete %(child_type)s "%(child)s", '
                        'which is itself protected:\n\n%(detail)s\n\n'
                        'Deal with that document first.'
                    ) % {
                        'parent': self.display_name,
                        'child_type': self.env['ir.model']._get(model_name).name or model_name,
                        'child': child.display_name,
                        'detail': str(error),
                    }) from error

    def _cascade_audit_rows(self, cascade):
        """Log rows for everything the cascade is about to remove."""
        cap = self._delete_audit_max_snapshot()
        rows = []
        for model_name, ids in cascade:
            model = self.env[model_name].sudo()
            if not model.browse(ids[:1])._delete_audit_enabled():
                continue
            with_snapshot = len(ids) <= cap
            for child in model.browse(ids).exists():
                try:
                    values = child._delete_audit_values(with_snapshot=with_snapshot)
                except Exception:
                    _logger.exception(
                        'Could not build the cascade audit entry for %s,%s',
                        model_name, child.id)
                    continue
                values['cascaded_from'] = '%s,%s' % (self._name, self.ids[0] if self.ids else 0)
                rows.append(values)
        return rows

    # ------------------------------------------------------------------
    # Override
    # ------------------------------------------------------------------
    def unlink(self):
        if self and self._delete_audit_enabled():
            # Everything below happens before the delete, because afterwards
            # there is nothing left to read. Written in the same transaction, so
            # the log reflects deletions that committed rather than attempts.
            cascade = self._cascade_deleted_records()

            # A cascade must not be a way around the protection. The bypass is
            # honoured here as it is anywhere else: forcing the parent forces
            # its children too, and the log says so.
            if cascade and not self.env.context.get('sd_force_delete') \
                    and not self.env.context.get('module_uninstall'):
                self._cascade_check_protection(cascade)

            with_snapshot = len(self) <= self._delete_audit_max_snapshot()
            rows = []
            for record in self:
                try:
                    rows.append(record._delete_audit_values(with_snapshot=with_snapshot))
                except Exception:
                    _logger.exception(
                        'Could not build the deletion audit entry for %s,%s',
                        record._name, record.id)
            if cascade:
                try:
                    rows += self._cascade_audit_rows(cascade)
                except Exception:
                    _logger.exception('Could not build the cascade audit entries for %s', self._name)
            if rows:
                try:
                    self.env['sd.delete.log'].sudo().create(rows)
                except Exception:
                    # A failure to audit must not silently drop the audit: raise
                    # so the deletion rolls back with it.
                    _logger.exception('Could not write the deletion audit log for %s', self._name)
                    raise
        return super(Base, self).unlink()
