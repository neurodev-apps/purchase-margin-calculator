# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super().button_confirm()
        templates = self.order_line.product_id.product_tmpl_id
        if templates:
            templates._update_last_purchase_cost()
            self._record_price_history(templates)
        return res

    def _record_price_history(self, templates):
        History = self.env['purchase.price.history']
        for order in self:
            for line in order.order_line:
                tmpl = line.product_id.product_tmpl_id
                if not tmpl or tmpl not in templates:
                    continue

                purchase_uom = line.product_uom
                product_uom = tmpl.uom_id
                if purchase_uom and product_uom and purchase_uom != product_uom:
                    try:
                        converted = purchase_uom._compute_price(line.price_unit, product_uom)
                    except Exception:
                        converted = line.price_unit
                else:
                    converted = line.price_unit

                History.create({
                    'product_tmpl_id': tmpl.id,
                    'product_id': line.product_id.id,
                    'date': order.date_order.date() if order.date_order else False,
                    'price_unit': line.price_unit,
                    'uom_id': purchase_uom.id if purchase_uom else False,
                    'converted_price': converted,
                    'vendor_id': order.partner_id.id,
                    'order_id': order.id,
                    'company_id': order.company_id.id,
                })

                old = History.search([
                    ('product_tmpl_id', '=', tmpl.id),
                    ('company_id', '=', order.company_id.id),
                ], order='date desc, id desc', offset=10)
                if old:
                    old.unlink()
