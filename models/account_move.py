# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import json
from datetime import datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    ji_partner_contract = fields.Many2one(comodel_name="res.partner", string="Commission Agent")
    ji_order_contract = fields.Many2one(comodel_name="sale.order", string="Order Contract")
    ji_is_moratorium = fields.Boolean(string="Moratorium", default=False)
    ji_json_numbers = fields.Text(string="Json Number", store=True, compute="_compute_ji_json_numbers")
    ji_json_sequences = fields.Text(string="Json Sequences", store=True, compute="_compute_ji_json_numbers")
    x_studio_contrato = fields.Char(string="Contrato", compute="contrato")
    x_studio_vendedor = fields.Many2one(comodel_name="hr.employee", related="partner_id.sale_order_ids.x_studio_vendedor", string="Vendedor")

    @api.depends("partner_id")
    def _compute_ji_contrato(self):
      for res in self:
        res.x_studio_contrato = res.partner_id.sale_order_ids.x_studio_contrato

    def regenerate_correlative(self):
        self.company_id.migrate_old_sequences(self)

    def get_contract_number(self):
        sale = False
        for move in self:
            sale = self.env["sale.order"].search([('name', '=', move.invoice_origin)])
        if sale:
            return sale.x_studio_contrato
        return False

    @api.depends("line_ids")
    def get_reporte_amoritizacion(self):
        for res in self:
            move = []
            account = []

            compaRecords=[]
            compani = res.company_id
            tov = res.amount_untaxed
            for lin in res.line_ids:
                if lin.debit > 0:
                    tov = tov - lin.debit
                    if lin.ji_number.find('A') != 0:
                        account.append({
                            "number": lin.ji_number.replace('/', ' de '),
                            "date_f": lin.date_maturity.strftime('%Y-%m-%d'),
                            "debit": lin.debit,
                            "credit": lin.credit,
                            "total" : tov
                        })

            move.append({
                "name": res.name,
                "cliente": res.partner_id.name,
                "date": res.invoice_date,
                "company": res.invoice_date
            })

            compaRecords.append({
                'name': compani.name,
                'zip': compani.zip,
                'street': compani.street,
                'street2': compani.street2,
                'city': compani.city,
                'state_id': compani.state_id.name,
                'country_id': compani.country_id.name,
                'phone': compani.phone,
                'id': compani.id,
                'website': compani.website,
            })

            data = {
                'move_id': move,
                'acco': account,
                'comapany': compaRecords,
            }
            return self.env.ref('jibaritolotes.report_amortizacion').report_action(self, data=data)
            # raise UserError(_(data))

    @api.model
    def update_computes(self):
        for move in self.search([('id', '=', 19154)]):
            pass
            # move._compute_ji_json_numbers()
            # move.line_ids._compute_ji_sequence_payments()
            # move.line_ids._compute_ji_number()
            # move.line_ids._compute_ji_name()
        pass


    @api.depends("line_ids", "invoice_payment_term_id")
    def _compute_ji_json_numbers(self):
        for move in self:
            jsonobs = {}
            json_numbers = {}
            count_monthly = 1
            count_advance = 1
            count_payment = 3
            for line in move.line_ids:
                sequence = ""
                if line.ji_term_line_id.ji_type == 'money_advance':
                    sequence = "A" + str(count_advance)
                    count_advance += 1
                if line.ji_term_line_id.ji_type == 'monthly_payments':
                    sequence = str(count_monthly) + "/" + str(line.ji_term_line_id.payment_id.ji_numbers_monthly)
                    count_monthly += 1
                jsonobs[str(line.id)] = sequence
                # SET Correlative
                if not line.ji_term_line_id.id:
                    json_numbers[str(line.id)] = -1
                if line.ji_term_line_id.ji_type == 'money_advance':
                    json_numbers[str(line.id)] = 2
                if line.ji_term_line_id.ji_type == 'monthly_payments':
                    json_numbers[str(line.id)] = count_payment
                    count_payment += 1;
            move.ji_json_sequences = json.dumps(json_numbers)
            move.ji_json_numbers = json.dumps(jsonobs)

    def _recompute_payment_terms_lines(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        if not self.company_id.ji_apply_developments:
            return super(AccountMove, self)._recompute_payment_terms_lines()
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_context(force_company=self.journal_id.company_id.id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=',
                     'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date,
                                                                  currency=self.company_id.currency_id)
                if self.currency_id != self.company_id.currency_id:
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date,
                                                                               currency=self.currency_id)
                    return [(b[0], b[1], ac[1], b[2]) for b, ac in zip(to_compute, to_compute_currency)]
                else:
                    # Single-currency.
                    return [(b[0], b[1], 0.0, b[2]) for b in to_compute]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency, False)]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency, term_line_id in to_compute:
                currency = self.journal_id.company_id.currency_id
                if currency and currency.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'ji_term_line_id': term_line_id,
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                        'account.move.line'].create
                    candidate = create_method({
                        'name': self.invoice_payment_ref or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                        'ji_term_line_id': term_line_id,
                    })
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate._onchange_amount_currency()
                    candidate._onchange_balance()
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.invoice_payment_ref = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    ji_number = fields.Char(string="Correlative", store=True, compute="_compute_ji_number")

    ji_name = fields.Char(string="Name", store=True, compute="_compute_ji_name")

    ji_term_line_id = fields.Many2one(comodel_name="account.payment.term.line", string="Payment Term Line Id")

    ji_sequence_payments = fields.Integer(string="Order Payments", store=True, compute="_compute_ji_sequence_payments")

    @api.depends("move_id", "ji_term_line_id")
    def _compute_ji_sequence_payments(self):
        for line in self:
            json_numbers = json.loads(line.move_id.ji_json_sequences)
            line.ji_sequence_payments = json_numbers.get(str(line.id), 0)

    @api.depends("ji_number", "move_id")
    def _compute_ji_name(self):
        for line in self:
            line.ji_name = "{name}-{correlative}".format(name=line.move_id.name, correlative=line.ji_number)

    @api.depends("move_id", "ji_term_line_id")
    def _compute_ji_number(self):
        for line in self:
            json_numbers = json.loads(line.move_id.ji_json_numbers)
            line.ji_number = json_numbers.get(str(line.id), "")



class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.payment"
    x_studio_contrato = fields.Char(string="Contrato", compute="contrato")
    x_studio_tipo_de_pago = fields.Selection( string="Tipo de Pago",
        selection=[("Anticipo", "Anticipo"), ("Cobranza Mensualidades", "Cobranza Mensualidades"), ("Intererses Moratorios + Mensualidades","Intererses Moratorios + Mensualidades")])

    @api.depends("partner_id")
    def _compute_ji_contrato(self):
        for res in self:
            res.x_studio_contrato = res.partner_id.sale_order_ids.x_studio_contrato