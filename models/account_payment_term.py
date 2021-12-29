# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    # def regenerate_lines(self):
    #     anticipos = self.line_ids.filtered(lambda l: l.ji_type == 'money_advance')
    #     anticipo = anticipos.sorted(lambda a: a.days, True)[0]
    #     mensualidades = self.line_ids.filtered(
    #         lambda l: l.ji_type == 'monthly_payments' and l.option != "day_following_month")
    #     primer_dia = 0
    #     for a in self.line_ids.filtered(lambda l:l.ji_type == 'monthly_payments' and l.option == "day_following_month"):
    #         primer_dia = primer_dia + a.days
    #
    #     sum_dias = anticipo.days + primer_dia + 30
    #     meses = self.ji_numbers_monthly
    #     anipor = self.ji_advance_payment
    #     val_mount= (100 - anipor) / meses
    #
    #     print("sum_dias", sum_dias)
    #     sum_dias = 34
    #     montp_lines = []
    #     montp_lines.append([0, 0, {
    #         "days": 0,
    #         "option": "after_invoice_month",
    #         "ji_type": "balance",
    #         "value": "balance",
    #         "day_of_the_month": 0
    #     }])
    #     for f in range(1,meses):
    #         montp_lines.append([0, 0, {
    #             "days": sum_dias,
    #             "option": "after_invoice_month",
    #             "ji_type": "monthly_payments",
    #             "value": "percent",
    #             "value_amount": val_mount,
    #             "day_of_the_month": 4
    #         }])
    #         # day_after_invoice_date
    #         # day_following_month
    #         # after_invoice_month
    #         # day_current_month
    #         #  "day_of_the_month": sum_dias,
    #
    #         sum_dias += 30
    #
    #     # raise UserError(_(montp_lines))
    #     self.write({"line_ids": montp_lines})


    ji_advance_payment = fields.Float(string="% Advance Payment")
    ji_number_quotation = fields.Integer(string="Number Advance Payment", store=False,
                                         compute="_compute_ji_number_quotation")

    ji_numbers_monthly = fields.Integer(string="Number Monthly Payments", default=96)

    @api.depends("line_ids")
    def _compute_ji_number_quotation(self):
        for term in self:
            term.ji_number_quotation = len(term.line_ids.filtered(lambda l: l.ji_type == 'money_advance').ids)
            # term.ji_numbers_monthly = len(term.line_ids.filtered(lambda l: l.ji_type == 'monthly_payments').ids)

    def get_number_payments_advance_now(self):
        line_ids = self.line_ids.filtered(lambda l: l.ji_type == 'money_advance' and l.days == 0).ids
        return len(line_ids)

    def get_percent_month_payments(self):
        line_ids = self.line_ids.filtered(lambda l: l.ji_type == 'monthly_payments')
        if not line_ids.ids:
            return 0.00
        return line_ids[0].value_amount

    def compute(self, value, date_ref=False, currency=None):
        if not self.env.company.ji_apply_developments:
            return super(AccountPaymentTerm, self).compute(value, date_ref, currency)
        self.ensure_one()
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if not currency and self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        elif not currency:
            currency = self.env.company.currency_id
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            next_date = fields.Date.from_string(date_ref)
            if line.option == 'day_after_invoice_date':
                next_date += relativedelta(days=line.days)
                if line.day_of_the_month > 0:
                    months_delta = (line.day_of_the_month < next_date.day) and 1 or 0
                    next_date += relativedelta(day=line.day_of_the_month, months=months_delta)
            elif line.option == 'after_invoice_month':
                next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                next_date = next_first_date + relativedelta(days=line.days - 1)
            elif line.option == 'day_following_month':
                next_date += relativedelta(day=line.days, months=1)
            elif line.option == 'day_current_month':
                next_date += relativedelta(day=line.days, months=0)
            result.append((fields.Date.to_string(next_date), amt, line.id))
            amount -= amt
        amount = sum(amt for _, amt, line_id in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist, False))
        return result


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    ji_type = fields.Selection([('money_advance', 'Money Advance'), ('monthly_payments', 'Monthly Payments'),
                                ('balance', 'Balance')], string="Type Payment", default="monthly_payments")



# class AccountPayment(models.AbstractModel):
#     _inherit = "account.payment"