# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, test_python_expr

class moratorio_move(models.Model):
    _inherit = "account.move"

    def copy(self, default=None):
        self.ensure_one()
        raise UserError(_("You cannot duplicate this record, please create a new one."))
        return super(moratorio_move, self).copy(default=default)

    def unlink(self):
        if self.state == "invoiced":
            raise UserError(_("You cannot delete a record in invoiced."))
        return super(moratorio_move, self).unlink()

    at_date = fields.Date(string="At Date", default=fields.Date.context_today)
    interest_line = fields.One2many(comodel_name="ji.moratorium.interest.line", string="Interest line",
                                    inverse_name="account_move_id")
    percent_moratorium = fields.Float(related="company_id.ji_percent_moratorium", string="Percent Moratorium")
    ji_condition = fields.Selection(related="partner_id.ji_condition", string="Condicion")
    ji_number_slow_payer = fields.Integer(related="partner_id.ji_number_slow_payer", string="Number Slow Payer")
    amount_total_moratorium = fields.Monetary(string="Amount Total Moratorium",
                                              compute="_compute_amount_total_moratorium")

    def _prapare_invoice(self):
        line_vals = []
        for line in self.interest_line:
            line_vals.append([0, 0, line._prepare_invoice_line()])
        vals = {
            "partner_id": self.partner_id.id,
            "invoice_date": self.at_date,
            "company_id": self.company_id.id,
            "invoice_line_ids": line_vals,
            "type": "out_invoice",
            "ji_is_moratorium": True
        }
        return vals

    def validate_create_invoice(self):
        if len(self.interest_line.ids) == 0:
            raise UserError(_("It does not contain overdue payments."))

    def create_invoice(self):
        self.ensure_one()
        self.validate_create_invoice()
        if not self.invoice_id.id:
            vals = self._prapare_invoice()
            invoice = self.env["account.move"].create(vals)
            self.write({"invoice_id": invoice.id})

        self.write({"state": "invoiced"})

    def action_view_invoice(self):
        self.ensure_one()
        # self.invoice_id.write({"ji_is_moratorium": True})
        return {
            'name': _('Customer Invoice Moratorium'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
        }

    @api.depends("interest_line")
    def _compute_amount_total_moratorium(self):
        # self.action_regenerate_unreconciled_aml_dues()
        for moratorium in self:
            moratorium.amount_total_moratorium = sum(line.amount_total_moratorium for line in self.interest_line)

    def validate_regenerate_aml(self):
        if not self.partner_id.id:
            raise UserError(_("Client not selected"))

    def get_exist_payments(self):
        moratoriums = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('state', 'not in', ['draft', 'cancel'])])
        return moratoriums.interest_line.mapped('unreconciled_aml').ids

    def action_regenerate_unreconciled_aml_dues(self):
        self.validate_regenerate_aml()
        for record in self:
            companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])

            if len(companies.ids) == 0:
                raise UserError(_('No Apply for this companies'))
            partners = []
            for company in companies:
                partners_slow_payer = record.partner_id.get_partners_slow_payer_moratorium(company)

                for p in partners_slow_payer:
                    number_slow_payer, amls = p.get_number_slow_payer_cron(company)
                    partners.append({"partner": p, "amls": amls})
                    # raise UserError(_(amls))
                if len(partners) > 0:
                    record.interest_line.unlink()
                    for partner in partners:
                        notification_lines = []
                        # raise UserError(_(partner["amls"]))
                        for aml in partner["amls"]:
                            if aml.move_id.id == record.id:
                                if aml.id not in record.get_exist_payments():
                                    notification_lines.append([0, 0, {
                                        "name": len(partner["amls"]),
                                        "unreconciled_aml": aml.id,
                                        "moratorium_id": aml.move_id.id
                                    }])

                # raise UserError(_(notification_lines))
                self.write({"interest_line": notification_lines})