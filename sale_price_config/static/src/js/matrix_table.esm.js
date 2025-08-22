/** @odoo-module */

import {Component, useEffect} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

function parseMatrix(matrix) {
    if (matrix) {
        const lines = matrix.split(/\r?\n/);
        const linesAndElement = lines.map((l) => l.split(";"));
        return {
            header: linesAndElement[0],
            lines: linesAndElement.slice(-(linesAndElement.length - 1)),
        };
    }
    return {header: false, lines: false};
}

export class MatrixTableField extends Component {
    static template =  "sale_mrp_bom_configurable.matrix";
    static props = {...standardFieldProps};
    static supportedTypes = ["text"]
    setup() {
        const {header, lines} = parseMatrix(this.props.record.data[this.props.name]);
        this.headerElements = header;
        this.lines = lines;
        useEffect(() => {
            const {header_eff, lines_eff} = parseMatrix(this.props.record.data[this.props.name]);
            this.headerElements = header_eff;
            this.lines = lines_eff;
        });
    }
}

export const matrixTableField = {
    component: MatrixTableField,
}

registry.category("fields").add("matrix_table", matrixTableField);
