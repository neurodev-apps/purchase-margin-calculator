# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    last_purchase_price = fields.Float(string='Last Purchase Price', digits='Product Price', readonly=True)
    last_purchase_date = fields.Date(string='Last Purchase Date', readonly=True)
    last_purchase_vendor_id = fields.Many2one('res.partner', string='Last Vendor', readonly=True)
    last_purchase_uom_id = fields.Many2one('uom.uom', string='Purchase UoM', readonly=True)
    last_purchase_order_id = fields.Many2one('purchase.order', string='Last Purchase Order', readonly=True)
    last_cost_converted = fields.Float(string='Last Cost (Sale UoM)', digits='Product Price', readonly=True)
    effective_sale_price = fields.Float(string='Effective Sale Price', compute='_compute_effective_sale_price', digits='Product Price')
    margin_percent = fields.Float(string='Margin %', compute='_compute_margin_percent', digits=(5, 4))
    suggested_price = fields.Float(string='Suggested Price', digits='Product Price', readonly=True)
    price_alert = fields.Selection([('ok', 'OK'), ('warning', 'Warning'), ('critical', 'Critical'), ('no_data', 'No Data')], string='Price Alert', readonly=True)
    margin_vs_list = fields.Float(string='Margin vs List', digits=(5, 4), readonly=True)
    purchase_price_history_ids = fields.One2many('purchase.price.history', 'product_tmpl_id', string='Purchase Price History')

    def _compute_effective_sale_price(self):
        pricelist = None
        if 'pos.config' in self.env.registry:
            pos_config = self.env['pos.config'].search([], limit=1, order='id')
            pricelist = pos_config.pricelist_id if pos_config else None
        for product in self:
            price = product.list_price
            if pricelist and product.product_variant_ids:
                variant = product.product_variant_ids[0]
                item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_id', '=', variant.id),
                    ('applied_on', '=', '0_product_variant'),
                ], order='min_quantity', limit=1)
                if item:
                    price = item.fixed_price
                else:
                    item = self.env['product.pricelist.item'].search([
                        ('pricelist_id', '=', pricelist.id),
                        ('product_tmpl_id', '=', product.id),
                        ('applied_on', '=', '1_product'),
                    ], order='min_quantity', limit=1)
                    if item:
                        price = item.fixed_price
            product.effective_sale_price = price

    def _compute_margin_percent(self):
        for product in self:
            cost = product.last_cost_converted
            sale = product.effective_sale_price
            if sale and cost:
                product.margin_percent = (sale - cost) / sale
            else:
                product.margin_percent = 0.0

    def _get_margin_factor(self):
        param = self.env['ir.config_parameter'].sudo().get_param('purchase_margin_calculator.margin_factor', '1.30')
        try:
            return float(param)
        except (ValueError, TypeError):
            return 1.30

    @staticmethod
    def _convert_uom_price(purchase_uom, product_uom, price_unit):
        if purchase_uom and product_uom and purchase_uom != product_uom:
            try:
                return purchase_uom._compute_price(price_unit, product_uom)
            except Exception:
                return price_unit
        return price_unit

    def action_recalculate_purchase_cost(self):
        self._update_last_purchase_cost()

    def _update_last_purchase_cost(self):
        PurchaseLine = self.env['purchase.order.line']
        factor = self._get_margin_factor()
        for product in self:
            variant_ids = product.product_variant_ids.ids
            if not variant_ids:
                product.write({'last_purchase_price': 0, 'last_purchase_date': False, 'last_purchase_vendor_id': False, 'last_purchase_uom_id': False, 'last_purchase_order_id': False, 'last_cost_converted': 0, 'suggested_price': 0, 'price_alert': 'no_data', 'margin_vs_list': 0})
                continue

            line = PurchaseLine.search([('product_id', 'in', variant_ids), ('order_id.state', 'in', ('purchase', 'done'))], order='id desc', limit=1)
            if not line:
                product.write({'last_purchase_price': 0, 'last_purchase_date': False, 'last_purchase_vendor_id': False, 'last_purchase_uom_id': False, 'last_purchase_order_id': False, 'last_cost_converted': 0, 'suggested_price': 0, 'price_alert': 'no_data', 'margin_vs_list': 0})
                continue

            price_unit = line.price_unit
            # CRITICAL: In Odoo 17, the field is product_uom, not product_uom_id
            converted = self._convert_uom_price(line.product_uom, product.uom_id, price_unit)
            suggested = converted * factor
            sale_price = product.effective_sale_price

            if not sale_price or sale_price <= 0:
                alert = 'no_data'
            elif sale_price >= suggested:
                alert = 'ok'
            elif sale_price >= converted * 1.10:
                alert = 'warning'
            else:
                alert = 'critical'

            margin_vs_list = 0.0
            if sale_price and converted and sale_price > 0:
                margin_vs_list = (sale_price - converted) / sale_price

            product.write({
                'last_purchase_price': price_unit,
                'last_purchase_date': line.order_id.date_order.date() if line.order_id.date_order else False,
                'last_purchase_vendor_id': line.order_id.partner_id.id,
                'last_purchase_uom_id': line.product_uom.id if line.product_uom else False,
                'last_purchase_order_id': line.order_id.id,
                'last_cost_converted': converted,
                'suggested_price': suggested,
                'price_alert': alert,
                'margin_vs_list': margin_vs_list,
            })

    @api.model
    def _populate_history_from_existing(self):
        _logger.info('purchase_margin_calculator: Populating history from existing POs...')
        History = self.env['purchase.price.history']
        PurchaseLine = self.env['purchase.order.line']
        templates = self.search([('purchase_ok', '=', True)])
        count = 0
        for tmpl in templates:
            variant_ids = tmpl.product_variant_ids.ids
            if not variant_ids:
                continue
            if History.search_count([('product_tmpl_id', '=', tmpl.id)]):
                continue
            lines = PurchaseLine.search([('product_id', 'in', variant_ids), ('order_id.state', 'in', ('purchase', 'done'))], order='id desc', limit=10)
            for line in lines:
                converted = self._convert_uom_price(line.product_uom, tmpl.uom_id, line.price_unit)
                History.create({
                    'product_tmpl_id': tmpl.id,
                    'product_id': line.product_id.id,
                    'date': line.order_id.date_order.date() if line.order_id.date_order else False,
                    'price_unit': line.price_unit,
                    'uom_id': line.product_uom.id if line.product_uom else False,
                    'converted_price': converted,
                    'vendor_id': line.order_id.partner_id.id,
                    'order_id': line.order_id.id,
                    'company_id': line.order_id.company_id.id,
                })
                count += 1
        batch_size = 100
        for i in range(0, len(templates), batch_size):
            batch = templates[i:i + batch_size]
            batch._update_last_purchase_cost()
        _logger.info('purchase_margin_calculator: Created %d history entries for %d products', count, len(templates))

    @api.model
    def _cron_update_purchase_costs(self):
        _logger.info('purchase_margin_calculator: Starting recalculation...')
        products = self.search([('purchase_ok', '=', True)])
        batch_size = 100
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batch._update_last_purchase_cost()
        _logger.info('purchase_margin_calculator: Done for %d products', len(products))
