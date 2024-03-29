# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, test_python_expr


class JiMoratoriumInterest(models.Model):
    _name = "ji.moratorium.interest"
    _description = "Interest for moratorium"
    _order = "at_date"

    def copy(self, default=None):
        self.ensure_one()
        raise UserError(_("You cannot duplicate this record, please create a new one."))
        return super(JiMoratoriumInterest, self).copy(default=default)

    def unlink(self):
        if self.state == "invoiced":
            raise UserError(_("You cannot delete a record in invoiced."))
        return super(JiMoratoriumInterest, self).unlink()

    invoice_id = fields.Many2one(comodel_name="account.move", string="Invoice")

    state_invoice = fields.Selection(related="invoice_id.state", string="State of Invoice")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", store=True,
                                  compute="_compute_currency_id")

    line_count = fields.Integer(compute="_compute_line_count")

    @api.depends("interest_line")
    def _compute_line_count(self):
        for moratorium in self:
            moratorium.line_count = len(moratorium.interest_line.ids)

    @api.depends("partner_id")
    def _compute_currency_id(self):
        for moratorium in self:
            moratorium.currency_id = moratorium.partner_id.property_product_pricelist.currency_id.id

    amount_total_moratorium = fields.Monetary(string="Amount Total Moratorium",
                                              compute="_compute_amount_total_moratorium")

    @api.depends("interest_line")
    def _compute_amount_total_moratorium(self):
        for moratorium in self:
            moratorium.amount_total_moratorium = sum(line.amount_total_moratorium for line in self.interest_line)

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

    def name_get(self):
        res = []
        for moratorium in self:
            res.append((moratorium.id, moratorium.partner_id.name))
        return res

    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)
    interest_line = fields.One2many(comodel_name="ji.moratorium.interest.line", string="Interest line",
                                    inverse_name="moratorium_id")
    state = fields.Selection(selection=[('in_progress', 'In Progress'), ('invoiced', 'Invoiced')], string="State",
                             default="in_progress")
    at_date = fields.Date(string="At Date", default=fields.Date.context_today, required=True)

    percent_moratorium = fields.Float(related="company_id.ji_percent_moratorium", string="Percent Moratorium")

    def validate_regenerate_aml(self):
        if not self.partner_id.id:
            raise UserError(_("Client not selected"))

    def get_exist_payments(self):
        moratoriums = self.env['ji.moratorium.interest'].search(
            [('partner_id', '=', self.partner_id.id), ('state_invoice', 'not in', ['draft', 'cancel'])])
        return moratoriums.interest_line.mapped('unreconciled_aml').ids

    def action_regenerate_unreconciled_aml_dues(self):
        self.validate_regenerate_aml()
        companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])
        if len(companies.ids) == 0:
            raise UserError(_('No Apply for this companies'))
        partners = []
        for company in companies:
            partners_slow_payer = self.partner_id.get_partners_slow_payer_moratorium(company)
            for p in partners_slow_payer:
                number_slow_payer, amls = p.get_number_slow_payer_cron(company)
                partners.append({"partner": p, "amls": amls})
            if len(partners) > 0:
                self.interest_line.unlink()
                for partner in partners:
                    notification_lines = []
                    for aml in partner["amls"]:
                        if aml.id not in self.get_exist_payments():
                            notification_lines.append([0, 0, {
                                "name": len(partner["amls"]),
                                "unreconciled_aml": aml.id
                            }])
                self.write({"interest_line": notification_lines})


class JiMoratoriumInterestLine(models.Model):
    _name = "ji.moratorium.interest.line"
    _description = "Details Interest for moratorium"

    def _prepare_invoice_line(self):
        vals = {
            "name": self.name,
            "quantity": 1,
            "price_unit": self.real_amount_moratorium
        }
        return vals

    name = fields.Char(string="Name", compute="_compute_name", store=True)

    @api.depends("unreconciled_aml")
    def _compute_name(self):
        for line in self:
            line.name = line.unreconciled_aml.ji_name

    moratorium_id = fields.Many2one(comodel_name="ji.moratorium.interest", string="Moratorium", ondelete="cascade",
                                    index=True)
    unreconciled_aml = fields.Many2one(comodel_name="account.move.line", string="Unreconciled Due")
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
            num = 0
            if r.months < 0:
                num = r.months * -1
            else:
                num = r.months
            line.month_number = num



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
