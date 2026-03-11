from odoo import fields, models


class PurchasePriceHistory(models.Model):
    _name = 'purchase.price.history'
    _description = 'Purchase Price History'
    _order = 'date desc, id desc'
    _rec_name = 'product_tmpl_id'

    product_tmpl_id = fields.Many2one(
        'product.template', string="Product Template",
        required=True, ondelete='cascade', index=True,
    )
    product_id = fields.Many2one(
        'product.product', string="Product Variant",
        ondelete='cascade', index=True,
    )
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    price_unit = fields.Float(string="Unit Price", digits='Product Price')
    uom_id = fields.Many2one('uom.uom', string="Purchase UoM")
    converted_price = fields.Float(
        string="Converted Price",
        digits='Product Price',
        help="Price converted to the product's sale UoM.",
    )
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    order_id = fields.Many2one('purchase.order', string="Purchase Order", ondelete='set null')
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company,
    )
