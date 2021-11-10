# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ResCountry(models.Model):
    _inherit = 'res.country'

    def name_get(self):
        if self._context.get('show_demonym', False):
            res = []
            for country in self:
                name = country.demonym or country.name
                res.append((country.id, name))
            return res
        else:
            return super(ResCountry, self).name_get()


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _default_ji_nationality(self):
        return self.env.ref('base.mx').id

    
    def is_curp(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids)
        pattern ="^[A-Z][A,E,I,O,U,X][A-Z]{2}[0-9]{2}[0-1][0-9][0-3][0-9][M,H][A-Z]{2}[B,C,D,F,G,H,J,K,L,M,N,Ñ,P,Q,R,S,T,V,W,X,Y,Z]{3}[0-9,A-Z][0-9]$"
        for data in record:
            if re.match(pattern, data.curp):
                return True
            else:
                return False
        return {}
    _constraints = [(is_curp, 'Error: Invalid curp', ['curp']), ]

    ji_civil_status = fields.Char(string="Civil Status")
    ji_occupation = fields.Char(string="Occupation")
    ji_spouse = fields.Char(string="Spouse")
    ji_date_of_birth = fields.Date(string="Date Of Birth")
    ji_place_of_birth = fields.Char(string="Place Of Birth")
    ji_nationality = fields.Many2one(comodel_name="res.country", string="Nacionalidad", default=_default_ji_nationality)
    curp = fields.Char(string="Curp",size = 18)
    unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id', string="Aml no reconciliado")

    def get_ji_date_of_birth(self):
        if self.ji_date_of_birth:
            _month_name = self.env["sale.order"].get_name_month(self.ji_date_of_birth.month)
            return "" + str(self.ji_date_of_birth.day) + " DE " + str(_month_name.upper()) + " DE " + str(
                self.ji_date_of_birth.year)
        return ""

    ji_condition = fields.Selection(
        selection=[("no_apply", "No Apply for this company"), ("punctual", "Punctual"), ("slow_payer", "Slow Payer")],
        string="Is Slow Payer", search="_search_ji_condition")

    def _search_ji_condition(self, operator, value):
        if not self.env.company.ji_apply_developments:
            raise UserError(_('No Apply for this company'))
        partner_ids = self.search([('company_id', '=', self.env.company.id)]).get_partners_slow_payer()
        return [('id', 'in', [p.id for p in partner_ids])]

    ji_commercial = fields.Many2one(comodel_name="hr.employee", store=True, string="Comercial"
                                    )

    @api.depends("sale_order_ids")
    def _compute_ji_commercial(self):
        for partner in self:
            _comercial = False
            if partner.sale_order_ids.filtered(lambda l: l.company_id.ji_apply_developments):
                _comercial = partner.sale_order_ids[0].x_studio_vendedor
            partner.ji_commercial = _comercial

    @api.depends('unreconciled_aml_ids')
    def _compute_ji_condition(self):
        for record in self:
            if record.company_id.ji_apply_developments:
                number_slow_payer, aml = record.get_number_slow_payer()
                if self.env.company.ji_number_slow_payer > 0:
                    if number_slow_payer >= self.env.company.ji_number_slow_payer:
                        record.ji_condition = 'slow_payer'
                    else:
                        record.ji_condition = 'punctual'
                else:
                    record.ji_condition = 'punctual'
            else:
                record.ji_condition = 'no_apply'

    ji_number_slow_payer = fields.Integer(string="Number Slow Payer")

    def get_partners_slow_payer_cron(self, company):
        partner_ids = []
        for record in self:
            if record.company_id.ji_apply_developments:
                number_slow_payer, aml = record.get_number_slow_payer_cron(company)
                if company.ji_number_slow_payer > 0:
                    if number_slow_payer >= company.ji_number_slow_payer:
                        partner_ids.append(record)
        return partner_ids

    def get_partners_slow_payer_moratorium(self, company):
        partner_ids = []
        for record in self:
            if record.company_id.ji_apply_developments:
                number_slow_payer, aml = record.get_number_slow_payer_cron(company)
                if company.ji_number_slow_payer > 0:
                    if number_slow_payer > 0:
                        partner_ids.append(record)
        return partner_ids

    def get_partners_slow_payer(self):
        partner_ids = []
        for record in self:
            if record.company_id.ji_apply_developments:
                number_slow_payer, aml = record.get_number_slow_payer()
                if self.env.company.ji_number_slow_payer > 0:
                    if number_slow_payer >= self.env.company.ji_number_slow_payer:
                        partner_ids.append(record)
        return partner_ids

    def get_number_slow_payer_cron(self, company):
        number_slow_payer = 0
        today = fields.Date.context_today(company.partner_id)
        aml_ids = []
        # for aml in self.unreconciled_aml_ids:
        #     if aml.company_id == company:
        #         is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
        #         if is_overdue and not aml.blocked and not aml.move_id.ji_is_moratorium:
        #             number_slow_payer += 1
        #             aml_ids.append(aml)
        return number_slow_payer, aml_ids

    def get_number_slow_payer(self):
        number_slow_payer = 0
        today = fields.Date.context_today(self)
        aml_ids = []
        # for aml in self.unreconciled_aml_ids:
        #     if aml.company_id == self.env.company:
        #         is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
        #         if is_overdue and not aml.blocked:
        #             number_slow_payer += 1
        #             aml_ids.append(aml)
        return number_slow_payer, aml_ids

    # @api.depends('unreconciled_aml_ids')
    # def _ji_compute_for_followup(self):
    #     for record in self:
    #         if record.company_id.ji_apply_developments:
    #             number_slow_payer, aml = record.get_number_slow_payer()
    #             record.ji_number_slow_payer = number_slow_payer
    #         else:
    #             record.ji_number_slow_payer = 0

    # @api.model
    # def compute_total_define_slow_payer(self):
    #     for partner in self.search([]):
          #  partner._ji_compute_for_followup()
          #  partner._compute_ji_condition()

    # def cron_notification_slow_payer(self):
    #     pass
