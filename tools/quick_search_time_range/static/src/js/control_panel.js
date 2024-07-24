

/** @odoo-module */

// import { device } from "web.config";
// import * as LegacyControlPanel from "web.ControlPanel";
// import { useBackButton } from "web_mobile.hooks";
import { patch } from "@web/core/utils/patch";
import { ControlPanel } from "@web/search/control_panel/control_panel";


odoo.define('quick_search_time_range.control_panel', function (require) {
    "use strict";

    const DateRangeGM = require('quick_search_time_range.DateRangeGM');

    patch(ControlPanel.prototype, "quick_search_time_range", {
        get SearchMenuCustom(){
            return { Component: DateRangeGM, key: 'daterange' }
        }
    });
});

