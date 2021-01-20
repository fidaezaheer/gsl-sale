odoo.define('product_gs.summary_report', function (require) {
    'use strict';

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var session = require('web.session');
var ReportWidget = require('stock.ReportWidget');
var framework = require('web.framework');

var QWeb = core.qweb;


var Widget = require('web.Widget');
var Dialog = require('web.Dialog');


var _t = core._t;


var summary_report = AbstractAction.extend({
    hasControlPanel: true,

    init: function(parent, action) {
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

    willStart: function() {
        return Promise.all([this._super.apply(this, arguments), this.get_html()]);
    },

    set_html: function() {
        var self = this;
        var def = Promise.resolve();
        if (!this.report_widget) {
            this.report_widget = new ReportWidget(this, this.given_context);
            def = this.report_widget.appendTo(this.$('.o_content'));
        }
        return def.then(function () {
            self.report_widget.$el.html(self.html);
            self.report_widget.$el.find('.o_report_heading').html('<h1>Summary Report</h1>');
        });

        
    },

    start: async function() {
        this.controlPanelProps.cp_content = { $buttons: this.$buttons };
        await this._super(...arguments);
        this.set_html();
    },

    get_html: async function() {
        const { html } = await this._rpc({
            args: [this.given_context],
            method: 'get_html',
            model: 'summary.report',
        });
        this.html = html;
        var proposalOnly =  this.check_proposal();
        if (proposalOnly ==false) {
            this.renderButtons();
        } 
    },



    update_cp: function() {
        if (!this.$buttons) {
            this.renderButtons();
        }
        var proposalOnly =  this.check_proposal();
        if (proposalOnly == true) {
            var status = {}; 
        } else {
            var status = {
                cp_content: {$buttons: this.$buttons},
            };
        }

        this.controlPanelProps.cp_content = { $buttons: this.$buttons };
        return this.updateControlPanel();
    },
    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("publishReport.buttons", {}));
        this.$buttons.bind('click', function () {
            var hRef = window.location.href;
            var arrUrl = hRef.split("&");
            arrUrl.forEach(getActiveId);
            var activeId;
            function getActiveId(value, index, array) {
                if (value.includes('active_id')) {
                    activeId =  value.split("=")[1];
                }
            }
            if (activeId == null) {
                // console.log("Inavlid Active Id");
            }else{
                var url = '/phase_publish_report';
                var xhr = new XMLHttpRequest();
                xhr.open("POST", url, true);
                xhr.setRequestHeader("Content-Type", "application/json");
                xhr.onreadystatechange = function () {
                    if (this.readyState === 4 && this.status === 200) {
                        var resp = JSON.parse(this.responseText);
                        var result =  JSON.parse(resp.result);

                        if(result.error == true){
                            Dialog.alert(self, _t(result.description), {
                                title: _t('Quickbase Connection'),
                            });
                        }else{
                            Dialog.alert(self, _t(result.description), {
                                title: _t('Quickbase Connection'),
                            });                            
                        }
                    }else if ((xhr.readyState === 4 && xhr.status !== 200)) {
                        Dialog.alert(self, _t("Cannot connect."), {
                            title: _t('Quickbase Connection'),
                        });
                    }
                }
                var data = {
                    'params': {
                        'hRef':window.location.href,
                        'activeId':activeId,
                    }
                };
                xhr.send(JSON.stringify(data));
            }
        });
        return this.$buttons;
    },


    do_show: function() {
        this._super();
        this.update_cp();
    },

    check_proposal: function(){
        var proposalOnly;
        var activeId = window.location.href.split("id=")[1].split("&")[0];
        var url1 = '/get_phase_rec';
        var xhr1 = new XMLHttpRequest();
        xhr1.open("POST", url1, false);
        xhr1.setRequestHeader("Content-Type", "application/json");
        xhr1.onreadystatechange = function () {
            if (this.readyState === 4 && this.status === 200) {
                var resp = JSON.parse(this.responseText);
                var result =  JSON.parse(resp.result);
                proposalOnly = result.proposals_only;
            }
        }
        // xhr1.onprogress = function () {
        //     console.log('LOADING', xhr1.readyState);
        // };
        // xhr1.onload = function () {
        //     console.log('DONE', xhr1.readyState);
        // };
        var data = {
            'params': {
                'hRef':window.location.href,
                'activeId':activeId,
            }
        };
        xhr1.send(JSON.stringify(data));
        return proposalOnly;
    },
});

core.action_registry.add("summary_report", summary_report);
return summary_report;
});
    