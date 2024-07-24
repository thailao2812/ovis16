/** @odoo-module **/

import { registry } from "@web/core/registry";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { NoDeleteListRenderer } from "./no_delete_list_renderer";

export class NoDeleteOne2Many extends X2ManyField {}
NoDeleteOne2Many.components = { ...X2ManyField.components, ListRenderer: NoDeleteListRenderer };

registry.category("fields").add("no_delete_one2many", NoDeleteOne2Many);
