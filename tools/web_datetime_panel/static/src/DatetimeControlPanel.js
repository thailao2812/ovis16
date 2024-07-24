/** @odoo-module **/

import { DatetimeFilterItem } from "./DatetimeFilterItem";
import { ControlPanel } from "@web/search/control_panel/control_panel";

// THINH - insert DatetimeFilterItem into ControlPanel's components
ControlPanel.components = { ...ControlPanel.components, DatetimeFilterItem };
