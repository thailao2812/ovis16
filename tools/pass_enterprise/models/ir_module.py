from odoo import api, fields, models, modules, tools, _
from odoo.http import request
import threading
from odoo.exceptions import AccessDenied, UserError, ValidationError
import psycopg2


class Module(models.Model):
    _inherit = "ir.module.module"
    
    def _button_immediate_function(self, function):
        if not self.env.registry.ready or self.env.registry._init:
            raise UserError(_('The method _button_immediate_install cannot be called on init or non loaded registries. Please use button_install instead.'))

        if getattr(threading.current_thread(), 'testing', False):
            raise RuntimeError(
                "Module operations inside tests are not transactional and thus forbidden.\n"
                "If you really need to perform module operations to test a specific behavior, it "
                "is best to write it as a standalone script, and ask the runbot/metastorm team "
                "for help."
            )
        # try:
            # This is done because the installation/uninstallation/upgrade can modify a currently
            # running cron job and prevent it from finishing, and since the ir_cron table is locked
            # during execution, the lock won't be released until timeout.
            # self._cr.execute("SELECT * FROM ir_cron FOR UPDATE NOWAIT")
        # except psycopg2.OperationalError:
        #     raise UserError(_("Odoo is currently processing a scheduled action.\n"
        #                       "Module operations are not possible at this time, "
        #                       "please try again later or contact your system administrator."))
        function(self)

        self._cr.commit()
        registry = modules.registry.Registry.new(self._cr.dbname, update_module=True)
        self._cr.commit()
        if request and request.registry is self.env.registry:
            request.env.cr.reset()
            request.registry = request.env.registry
            assert request.env.registry is registry
        self._cr.reset()
        assert self.env.registry is registry

        # pylint: disable=next-method-called
        config = self.env['ir.module.module'].next() or {}
        if config.get('type') not in ('ir.actions.act_window_close',):
            return config

        # reload the client; open the first available root menu
        menu = self.env['ir.ui.menu'].search([('parent_id', '=', False)])[:1]
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': menu.id},
        }