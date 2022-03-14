odoo.define('jibaritolotes.hide_buton', function (require) {
"use strict";

var ListController = require("web.ListController");
var FormController = require('web.FormController');
var GraphController = require('web.GraphController');
var KanbanController = require('web.KanbanController');
var PivotController = require('web.PivotController');
var rpc = require('web.rpc');
var Sidebar = require('web.Sidebar');
var core = require('web.core');
var _t = core._t;


var FormView = require('web.FormView');

var session = require('web.session');

var QWeb = core.qweb;
console.log("entro jsv3");

  FormController = FormController.include({

  	renderButtons: async function (mode) {
            this._super.apply(this, arguments);
            console.log(this);

            //console.log(mode);
            var alldata  =  this
            var fiels = alldata.initialState.fieldsInfo.form
            var data = alldata.initialState.data
            // console.log(fiels.curp);
            console.log(alldata.$el.find('[name="action_draft"]'));
            console.log(alldata.$el.find('.o_statusbar_buttons .btn-secondary'));
            var display = {}


            if (alldata.modelName=='res.partner'){




            		session.user_has_group('jibaritolotes.group_jj_contact').then(function(has_group) {

		            	if(has_group) {

					       	display = {"display":""}
					       	alldata.$buttons.find('.o_form_button_edit').css(display);


					    } else {
		            		if(data.count_doct >= 3){
								display = {"display":""}
								alldata.$buttons.find('.o_form_button_edit').css(display);

								if(data.ji_documents){
									display ={"display":""}
									alldata.$buttons.find('.o_form_button_edit').css(display);
								}
								if(data.curp != ""  & data.street != "" & data.city != "" & data.zip != "" & data.country_id != ""){
									display ={"display":"none"}
									 alldata.$buttons.find('.o_form_button_edit').css(display);
								}
							}else {

								display = {"display": "none"}
								alldata.$buttons.find('.o_form_button_edit').css(display);
							}
					    }
		            });

        	}
        }

 });


});

