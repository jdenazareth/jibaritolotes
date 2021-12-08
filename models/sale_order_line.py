# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ji_area = fields.Float(string="Area", compute="_compute_ji_product_information", store=True)
    ji_street = fields.Char(string="Street", compute="_compute_ji_product_information", store=True)
    ji_corner_with = fields.Char(string="Corner With", compute="_compute_ji_product_information", store=True)
    #ji_manzana = fields.Char(string="Manzana", compute="_compute_ji_product_information", store=True)
    #ji_lote = fields.Char(string="Lote", compute="_compute_ji_product_information", store=True)

    # @api.depends("product_id")
    # def _compute_ji_product_information(self):
    #     try:
    #         for line in self:
    #
    #             if(line.product_id.estado_producto.name == "Nuevo" or line.product_id.estado_producto.name == "Recuperado"):
    #                 line.ji_area = line.product_id.ji_area
    #                 line.ji_street = line.product_id.ji_street
    #                 line.ji_corner_with = line.product_id.ji_corner_with
    #                 line.product_uom_qty = line.product_id.ji_area
    #                 line.price_subtotal = line.product_uom_qty * line.price_unit
    #             else:
    #                 if(line.product_id.id > 0):
    #                     raise UserError("No es posible agregar producto este no es nuevo o recuperado")
    #     except Exception as e:
    #         raise UserError("No es posible agregar producto, este no es nuevo o recuperado")
           # line.ji_manzana = line.product_id.x_studio_manzana.name
           # line.ji_lote = line.product_id.x_studio_lote.name

    @api.depends("product_id")
    def _compute_ji_product_information(self):
            for line in self:
                    line.ji_area = line.product_id.ji_area
                    line.ji_street = line.product_id.ji_street
                    line.ji_corner_with = line.product_id.ji_corner_with
                    line.product_uom_qty = line.product_id.ji_area
                    line.price_subtotal = line.product_uom_qty * line.price_unit

