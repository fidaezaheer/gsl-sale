odoo.define('product_gs.los_report', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require('web.session');
    var framework = require('web.framework');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;

    var los_report = AbstractAction.extend({
        hasControlPanel: true,

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.actionManager = parent;
            this.given_context = _.extend({}, session.user_context);
            this.controller_url = action.context.url;
            if (action.context.context) {
                this.given_context = action.context.context;
            }
            this.given_context.active_id = action.context.active_id || action.params.active_id;
            this.given_context.model = action.context.active_model || false;
        },

        willStart: function () {
            return Promise.all([this._super.apply(this, arguments), this.get_html()]);
        },

        set_html: function () {
            var self = this;
            var def = Promise.resolve();
            if (!this.report_widget) {
                this.report_widget = new Widget(this, this.given_context);
                def = this.report_widget.appendTo(this.$('.o_content'));
            }
            return def.then(function () {
                self.report_widget.$el.html(self.html);
                self.report_widget.$el.find('.o_report_heading').html('<h1>LOS Report</h1>');
            });
        },

        start: function () {
            this.controlPanelProps.cp_content = { $buttons: this.$buttons };
            this._super(...arguments);
            this.set_html();
        },
        // Fetches the html and is previous report.context if any, else create it
        get_html: function () {
            var self = this;
            var defs = [];
            return this._rpc({
                model: 'los.report',
                method: 'get_html',
                args: [self.given_context],
            })
                .then(function (result) {
                    self.html = result.html;
                    self.renderButtons();
                    return Promise.all(defs);
                });
        },

        do_show: function () {
            this._super();
            this.update_cp();
        },
        renderButtons: function () {
            var self = this;
            this.$buttons = $(QWeb.render("losReport.buttons", {}));
            $(this.$buttons, '.los-download-excel').bind('click', function () {
                var data = {'phase_id': self.given_context.active_id};
                session.get_file({
                    url: '/gs/export/export_xls',
                    data: { data: JSON.stringify(data) },
                    complete: framework.unblockUI,
                });
            });
            return this.$buttons;
        },
        update_cp: function () {
            if (!this.$buttons) {
                this.renderButtons();
            }
            this.controlPanelProps.cp_content = { $buttons: this.$buttons };
            return this.updateControlPanel();
        },

    });

    core.action_registry.add("los_report", los_report);
    return los_report;
});
