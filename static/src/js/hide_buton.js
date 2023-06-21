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

  FormController.include({

  	renderButtons: async function (mode) {
            this._super.apply(this, arguments);
            console.log(this);

            //console.log(mode);
            var alldata  =  this
            var fiels = alldata.initialState.fieldsInfo.form
            var data = alldata.initialState.data
            // console.log(fiels.curp);

            var display = {}

			/* session.user_has_group('yee_odoo_studio.group_dynamic').then(function(has_group) {
                if(has_group) {
					       	display = {"display":""}
					       	alldata.$el.find('._iMoreView').css(display);
				} else {
                	display ={"display":"none"}
					alldata.$el.find('._iMoreView').css(display);
				}
            });*/



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
								if(data.curp != ""  & data.street != "" & data.city != "" & data.zip != "" & data.country_id != "" & data.ji_civil_status !="" & data.ji_occupation !="" & data.ji_date_of_birth !="" ){
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
  /*
  ListController.include({
        renderButtons: async function (mode) {
            this._super(mode)
            var alldata  =  this
            var display = {}

            session.user_has_group('yee_odoo_studio.group_dynamic').then(function(has_group) {
                if(has_group) {
					       	display = {"display":""}
					       	alldata.$el.find('._iMoreView').css(display);
				} else {
                	display ={"display":"none"}
					alldata.$el.find('._iMoreView').css(display);

				}
            });


        }
    });
  GraphController.include({
        renderButtons: async function (mode) {
            this._super(mode)
            var alldata  =  this
            var display = {}

            session.user_has_group('yee_odoo_studio.group_dynamic').then(function(has_group) {
                if(has_group) {
					       	display = {"display":""}
					       	alldata.$el.find('._iMoreView').css(display);
				} else {
                	display ={"display":"none"}
					alldata.$el.find('._iMoreView').css(display);

				}
            });


        }
    });
   KanbanController.include({
        renderButtons: async function (mode) {
            this._super(mode)
            var alldata  =  this
            var display = {}

            session.user_has_group('yee_odoo_studio.group_dynamic').then(function(has_group) {
                if(has_group) {
					       	display = {"display":""}
					       	alldata.$el.find('._iMoreView').css(display);
				} else {
                	display ={"display":"none"}
					alldata.$el.find('._iMoreView').css(display);

				}
            });


        }
    });
   PivotController.include({
        renderButtons: async function (mode) {
            this._super(mode)
            var alldata  =  this
            var display = {}

            session.user_has_group('yee_odoo_studio.group_dynamic').then(function(has_group) {
                if(has_group) {
					       	display = {"display":""}
					       	alldata.$el.find('._iMoreView').css(display);
				} else {
                	display ={"display":"none"}
					alldata.$el.find('._iMoreView').css(display);

				}
            });


        }
    });
    */

});

