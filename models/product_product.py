# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_purchase_price = fields.Float(related='product_tmpl_id.last_purchase_price')
    last_cost_converted = fields.Float(related='product_tmpl_id.last_cost_converted')
    suggested_price = fields.Float(related='product_tmpl_id.suggested_price')
    price_alert = fields.Selection(related='product_tmpl_id.price_alert')
    margin_percent = fields.Float(related='product_tmpl_id.margin_percent')

    def action_recalculate_purchase_cost(self):
        self.product_tmpl_id.action_recalculate_purchase_cost()
