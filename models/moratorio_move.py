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
    #interest_line = fields.One2many(comodel_name="ji.moratorium.interest.line", string="Interest line",
    #                                inverse_name="moratorium_id")
    moratorio_line = fields.One2many(comodel_name="ji.moratorium.account.line", string="Interest line",
                                    inverse_name="moratorium_id")
    percent_moratorium = fields.Float(related="company_id.ji_percent_moratorium", string="Percent Moratorium")
    ji_condition = fields.Selection(related="partner_id.ji_condition", string="Condicion")
    ji_number_slow_payer = fields.Integer(related="partner_id.ji_number_slow_payer", string="Number Slow Payer")
    amount_total_moratorium = fields.Monetary(string="Amount Total Moratorium",
                                              compute="_compute_amount_total_moratorium")

    def _prapare_invoice(self):
        line_vals = []
        for line in self.moratorio_line:
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
        if len(self.moratorio_line.ids) == 0:
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

    @api.depends("moratorio_line")
    def _compute_amount_total_moratorium(self):
        # self.action_regenerate_unreconciled_aml_dues()
         for moratorium in self:
             moratorium.amount_total_moratorium = 0
             #sum(line.amount_total_moratorium for line in self.moratorio_line)

    def validate_regenerate_aml(self):
        if not self.partner_id.id:
            raise UserError(_("Client not selected"))

    def get_exist_payments(self):
        moratoriums = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('state', 'not in', ['draft', 'cancel'])])
        return moratoriums.moratorio_line.mapped('unreconciled_aml').ids

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
                    record.moratorio_line.unlink()
                    for partner in partners:
                        notification_lines = []
                        # raise UserError(_(partner["amls"]))
                        for aml in partner["amls"]:
                            if aml.move_id.id == record.id:
                                if aml.id not in record.get_exist_payments():
                                    notification_lines.append([0, 0, {
                                        "name": len(partner["amls"]),
                                        # "moratorium_id": aml.move_id.id,
                                        "unreconciled_aml": aml.id

                                    }])

                # raise UserError(_(notification_lines))
                self.write({"moratorio_line": notification_lines})

class JiMoratoriumaccountLine(models.Model):
    _name = "ji.moratorium.account.line"
    _description = "Details Interest for moratorium"

    moratorium_id = fields.Many2one(comodel_name="account.move", string="Moratorium", ondelete="cascade",
                                    index=True)
    unreconciled_aml = fields.Many2one(comodel_name="account.move.line", string="Unreconciled Due")

    name = fields.Char(string="Name", store=True, compute="_compute_name")
    date = fields.Date(string="Date", compute="_compute_unreconciled_values", store=True)
    date_maturity = fields.Date(string="Due Date", compute="_compute_unreconciled_values", store=True)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", store=True,
                                  compute="_compute_unreconciled_values")
    amount_residual = fields.Monetary(string="Amount", store=True, compute="_compute_unreconciled_values")
    at_date = fields.Date(string="At Date", related="moratorium_id.at_date")
    month_number = fields.Integer(string="Number Month", compute="_compute_month_number")
    amount_unit_moratorium = fields.Monetary(string="Amount Unit Moratorium", compute="_compute_amount_unit_moratorium")
    amount_total_moratorium = fields.Monetary(string="Amount Total Moratorium",
                                              compute="_compute_amount_total_moratorium")
    real_amount_moratorium = fields.Monetary(string="Total Moratorium", store=True,
                                             compute="_compute_real_amount_moratorium")

    moratorium_accumulated = fields.Monetary(string="Accumulated Moratorium", store=True,
                                             compute="_compute_moratorium_accumulated")

    def _prepare_invoice_line(self):
        vals = {
            "name": self.name,
            "quantity": 1,
            "price_unit": self.real_amount_moratorium
        }
        return vals

    @api.depends("unreconciled_aml")
    def _compute_name(self):
        for line in self:
            # raise UserError(_(line.unreconciled_aml.ji_name))
            line.name ="Mora - " + line.unreconciled_aml.ji_name



    @api.depends("month_number", "moratorium_id", "amount_residual")
    def _compute_moratorium_accumulated(self):
        for mora in self:
            amount = mora.amount_residual
            mora_accumulated = 0.0
            for index in range(0, mora.month_number):
                mora_accumulated += amount * (mora.moratorium_id.percent_moratorium / 100)
                amount = amount + (amount * (mora.moratorium_id.percent_moratorium / 100))
            mora.moratorium_accumulated = mora_accumulated

    @api.depends("moratorium_id", "month_number", "amount_residual")
    def _compute_real_amount_moratorium(self):
        for mora in self:
            # raise UserError(_(self.moratorium_id.company_id.name))
            mora.real_amount_moratorium = mora.exec_formula_python()

    def exec_formula_python(self):
        objects = {'o': self}
        python_code = self.get_formula_python()

        if python_code:
            safe_eval(self.get_formula_python(), objects, mode="exec", nocopy=True)
            return objects['result']
        else:
            return 0.00

    def get_formula_python(self):
        return self.moratorium_id.company_id.ji_code

    @api.depends("month_number", "amount_unit_moratorium")
    def _compute_amount_total_moratorium(self):
        for line in self:
            line.amount_total_moratorium = line.month_number * line.amount_unit_moratorium

    @api.depends("date_maturity", "at_date")
    def _compute_month_number(self):
        for line in self:
            r = relativedelta.relativedelta(line.at_date, line.date_maturity)
            line.month_number = r.months + 1

    @api.depends("amount_residual", "moratorium_id")
    def _compute_amount_unit_moratorium(self):
        for line in self:
            line.amount_unit_moratorium = ((line.moratorium_id.percent_moratorium / 100) * line.amount_residual)

    @api.depends("unreconciled_aml", "moratorium_id")
    def _compute_unreconciled_values(self):
        for line in self:
            currency = line.currency_id or line.moratorium_id.company_id.currency_id
            amount = line.unreconciled_aml.amount_residual_currency if line.unreconciled_aml.currency_id else line.unreconciled_aml.amount_residual
            line.amount_residual = amount
            line.date = line.unreconciled_aml.date
            line.date_maturity = line.unreconciled_aml.date_maturity
            line.currency_id = currency.id
            line.name = line.unreconciled_aml.ji_name