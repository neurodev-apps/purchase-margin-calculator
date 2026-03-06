from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_margin_factor = fields.Float(
        string="Target Margin Factor",
        help="Minimum multiplier over purchase cost to consider the sale price healthy. "
             "Example: 1.30 means the sale price should be at least 130% of cost.",
        config_parameter='purchase_margin_calculator.margin_factor',
        default=1.30,
    )
