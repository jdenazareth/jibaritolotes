# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    @api.constrains('line_ids')
    def _check_lines(self):
        print("djbdjbdbdik")
        payment_term_lines = self.line_ids.sorted()
        if payment_term_lines and payment_term_lines[-1].value not in ['balance', 'instalment']:
            raise UserError(_('A Payment Term should have its last line of type Balance/Instalment.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'balance') or []
        if len(lines) > 1:
            raise UserError(_('A Payment Term should have only one line of type Balance.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'instalment') or []
        if len(lines) > 1:
            raise UserError(_('A Payment Term should have only one line of type Instalment.'))
        lines = self.line_ids.filtered(lambda r: r.value in ['balance', 'instalment']) or []
        if len(lines) > 1:
            raise UserError(_('A Payment Term should have only one of type Balance and Instalment.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'instalment') or []
        for line in lines:
            if line.period_count == 0:
                raise UserError(
                    _('A Payment Term of type Instalment should have number of instalments more than 0.'))



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

    '''def compute(self, value, date_ref=False, currency=None):
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
        count_monthly = 1
        count_advance = 1
        count_payment = 3
        for line in self.line_ids:
            if line.value != 'instalment':
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
                amount = amount - amt


            elif line.value == 'instalment':
                amt = currency.round(amount)
                count = line.period_count
                instalment_amount = currency.round(amt / count)
                next_date1 = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date1 += relativedelta(days=line.days)
                i = 1
                while count > 0:
                    next_date = fields.Date.from_string(next_date1)
                    if line.period_type == 'daily':
                        next_date += relativedelta(days=i)
                    elif line.period_type == 'weekly':
                        next_date += relativedelta(weeks=i)
                    elif line.period_type == 'monthly':
                        next_date += relativedelta(months=i)
                    else:
                        next_date += relativedelta(years=i)
                    result.append((fields.Date.to_string(next_date), instalment_amount,line.id))
                    count -= 1
                    i += 1
                amount -= amt
        amount = sum(amt for _, amt, line_id in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist, False))
        return result '''

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
        next_date = fields.Date.from_string(date_ref)  # 08/04/2020
        day_act = 0
        for line in self.line_ids:

            day = line.days - day_act
            day_act = line.days
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)

            if line.option == 'day_after_invoice_date':
                if(day == 30):
                    next_date += relativedelta(months=1)#04/02/19
                else:
                    next_date += relativedelta(days=day)
                if line.day_of_the_month > 0:
                    months_delta = 0
                    if(float(next_date.day) > line.day_of_the_month):
                        months_delta = 1
                    next_date += relativedelta(day=line.day_of_the_month, months=months_delta)#04/02/19

            elif line.option == 'after_invoice_month':
                next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                next_date = next_first_date + relativedelta(days=line.days - 1)
            elif line.option == 'day_following_month':
                next_date += relativedelta(day=line.days, months=1)
            elif line.option == 'day_current_month':
                next_date += relativedelta(day=line.days, months=0)
            result.append((fields.Date.to_string(next_date), amt, line.id))
            amount = amount - amt
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
    ji_dia = fields.Integer('Dias de anticipo', default=1)
    value = fields.Selection([
        ('balance', 'Balance'),
        ('percent', 'Percent'),
        ('fixed', 'Fixed Amount'),
        ('instalment', 'Parcialidades')
    ], string='Type', required=True, default='balance',
        help="Select here the kind of valuation related to this payment term line.")
    period_type = fields.Selection([
        ('daily', 'Dia(s)'),
        ('weekly', 'Semana(s)'),
        ('monthly', 'Mes(es)'),
        ('yearly', 'Año(s)'),
    ], string='Tipo de periosidad', default='monthly')
    period_count = fields.Integer('Numero de parcialidades', default=1)

# class AccountPayment(models.AbstractModel):
#     _inherit = "account.payment"