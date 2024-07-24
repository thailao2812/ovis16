

/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ControlPanel } from "@web/search/control_panel/control_panel";


odoo.define('mns_date_search.control_panel', function (require) {
    "use strict";

    const DateRangeGM = require('mns_date_search.DateRangeGM');

    patch(ControlPanel.prototype, "mns_date_search", {
        get SearchMenuCustom(){
            return { Component: DateRangeGM, key: 'daterange' }
        }
    });
});

