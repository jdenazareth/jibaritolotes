# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import json


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ji_percent_commission = fields.Float(string="Percent Commission", default=6.0)

    ji_partner_id = fields.Many2one(comodel_name="res.partner", string="Contact Related")
