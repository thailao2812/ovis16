/** @odoo-module **/

"use strict";

export function mapToArray(map) {
    const result = [];
    for (const [key, val] of map) {
        const valCopy = Object.assign({}, val);
        result.push([key, valCopy]);
    }
    return result;
}

export function arraytoMap(array) {
    return new Map(array);
}
// THINH: add dateTimeSetting to execute function
export function execute(op, source, target) {
    const {
        query,
        nextId,
        nextGroupId,
        nextGroupNumber,
        searchItems,
        searchPanelInfo,
        sections,
        dateTimeSetting
    } = source;

    target.nextGroupId = nextGroupId;
    target.nextGroupNumber = nextGroupNumber;
    target.nextId = nextId;

    target.query = query;
    target.searchItems = searchItems;
    target.searchPanelInfo = searchPanelInfo;

    target.sections = op(sections);
    target.dateTimeSetting = dateTimeSetting;
    for (const [, section] of target.sections) {
        section.values = op(section.values);
        if (section.groups) {
            section.groups = op(section.groups);
            for (const [, group] of section.groups) {
                group.values = op(group.values);
            }
        }
    }
}