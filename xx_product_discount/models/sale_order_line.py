# coding : utf-8

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_pricelist_price(self):
    	""" Inherited method for calculating price with discount_percentage """
    	price = super(SaleOrderLine, self)._get_pricelist_price()
    	if self.product_id.discount_percentage:
    		price = price - (price * (self.product_id.discount_percentage / 100))
    	return price
