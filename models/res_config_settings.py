# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ji_apply_developments = fields.Boolean(string="Apply developments", related="company_id.ji_apply_developments",
                                           readonly=False)
    ji_number_slow_payer = fields.Integer(string="Number to Slow Payer", related="company_id.ji_number_slow_payer",
                                          readonly=False)
    ji_partner_ids = fields.Many2many(related="company_id.ji_partner_ids", string="Partners for Notification",
                                      readonly=False)
    ji_mail_template = fields.Many2one(related="company_id.ji_mail_template", string="Template for Notification",
                                       readonly=False)
    ji_percent_moratorium = fields.Float(related="company_id.ji_percent_moratorium", string="Percent Moratorium",
                                         readonly=False)
