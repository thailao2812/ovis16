/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SearchModel } from "@web/search/search_model";
import { deepCopy } from "@web/core/utils/objects";
import { Domain } from "@web/core/domain";
//use custom "execute" function which export dateTimeDomain to new search_model in breadcrumbs
import { execute, mapToArray, arraytoMap } from "../src/utils";

patch(SearchModel.prototype, "web_datetime_panel.SearchModel", {
    get domain() {
        if (!this._domain || this.dateTimeSetting?.isSearchingByDateTimePanel) {
            this._domain = this._getDomain();
            if(this.dateTimeSetting?.isSearchingByDateTimePanel) {
                this.dateTimeSetting.isSearchingByDateTimePanel = false;
            }
        }

        return deepCopy(this._domain);
    },

    _getDomain(params = {}) {
        const withSearchPanel = "withSearchPanel" in params ? params.withSearchPanel : true;
        const withGlobal = "withGlobal" in params ? params.withGlobal : true;

        const groups = this._getGroups();
        const domains = [];
        if (withGlobal) {
            domains.push(this.globalDomain);
        }

        if (this.dateTimeSetting?.dateTimeDomain.length) {
            domains.push(this.dateTimeSetting.dateTimeDomain);
        }

        for (const group of groups) {
            const groupActiveItemDomains = [];
            for (const activeItem of group.activeItems) {
                const domain = this._getSearchItemDomain(activeItem);
                if (domain) {
                    groupActiveItemDomains.push(domain);
                }
            }
            const groupDomain = Domain.or(groupActiveItemDomains);
            domains.push(groupDomain);
        }

        for (const { domain } of this.getDomainParts()) {
            domains.push(domain);
        }
        // we need to manage (optional) facets, deactivateGroup, clearQuery,...

        if (this.display.searchPanel && withSearchPanel) {
            domains.push(this._getSearchPanelDomain());
        }

        let domain;
        try {
            domain = Domain.and(domains);
            return params.raw
                ? domain
                : domain.toList(Object.assign({}, this.globalContext, this.userService.context));
        } catch (error) {
            throw new Error(
                `${this.env._t("Failed to evaluate the domain")} ${domain.toString()}.\n${
                    error.message
                }`
            );
        }
    },

    exportState() {
        const state = {};
        execute(mapToArray, this, state);
        return state;
    },

    _importState(state) {
        execute(arraytoMap, state, this);
    },
});
