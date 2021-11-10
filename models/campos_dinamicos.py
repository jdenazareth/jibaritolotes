# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class Lotesji(models.Model):
    _name = "lotes.ji"
    _inherit = ['mail.thread']
    
    name = fields.Char(String = "Lote", track_visibility='onchange')

class Manzanaji(models.Model):
    _name = "manzana.ji"
    _inherit = ['mail.thread']
    
    name = fields.Char(String = "Manzana", track_visibility='onchange')
