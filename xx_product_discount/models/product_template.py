# coding: utf-8

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    discount_percentage = fields.Float('Discount Percentage', copy=False)

    def _price_compute(self, price_type, uom=None, currency=None, company=None, date=False):
        company = company or self.env.company
        date = date or fields.Date.context_today(self)

        self = self.with_company(company)
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            self = self.sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for template in self:
            price = template[price_type] or 0.0
            price_currency = template.currency_id
            if price_type == 'standard_price':
                if not price and template.product_variant_ids:
                    price = template.product_variant_ids[0].standard_price
                price_currency = template.cost_currency_id
            elif price_type == 'list_price':
                price += template._get_attributes_extra_price()

            if uom:
                price = template.uom_id._compute_price(price, uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                price = price_currency._convert(price, currency, company, date)
            #Price Calculation with Product Template's Discount percentage
            price = price - (price * (template.discount_percentage / 100))
            prices[template.id] = price
        return prices

    def _get_additionnal_combination_info(self, product_or_template, quantity, date, website):
        """ Inherited method for calculating price with product templates's discount percentage """
        res = super(ProductTemplate, self)._get_additionnal_combination_info(product_or_template, quantity, date, website)
        if product_or_template.discount_percentage:
            res['price'] = res['price'] - (res['price'] * (product_or_template.discount_percentage / 100))
        return res

    def _get_sales_prices(self, pricelist, fiscal_position):
        if not self:
            return {}

        pricelist and pricelist.ensure_one()
        pricelist = pricelist or self.env['product.pricelist']
        currency = pricelist.currency_id or self.env.company.currency_id
        date = fields.Date.context_today(self)

        sales_prices = pricelist._get_products_price(self, 1.0)
        show_discount = pricelist and pricelist.discount_policy == 'without_discount'
        show_strike_price = self.env.user.has_group('website_sale.group_product_price_comparison')

        base_sales_prices = self._price_compute('list_price', currency=currency)
        print("\n\n\n\n\nsales price",base_sales_prices)

        res = {}
        for template in self:
            price_reduce = sales_prices[template.id]

            product_taxes = template.sudo().taxes_id._filter_taxes_by_company(self.env.company)
            taxes = fiscal_position.map_tax(product_taxes)

            base_price = None
            price_list_contains_template = currency.compare_amounts(price_reduce, base_sales_prices[template.id]) != 0

            if template.compare_list_price and show_strike_price:
                # The base_price becomes the compare list price and the price_reduce becomes the price
                base_price = template.compare_list_price
                if not price_list_contains_template:
                    price_reduce = base_sales_prices[template.id]

                if template.currency_id != currency:
                    base_price = template.currency_id._convert(
                        base_price,
                        currency,
                        self.env.company,
                        date,
                        round=False
                    )

            elif show_discount and price_list_contains_template:
                base_price = base_sales_prices[template.id]

                # Compare_list_price are never tax included
                base_price = self._apply_taxes_to_price(
                    base_price, currency, product_taxes, taxes, template,
                )

            price_reduce = self._apply_taxes_to_price(
                price_reduce, currency, product_taxes, taxes, template,
            )

            template_price_vals = {
                'price_reduce': price_reduce,
            }
            if base_price:
                template_price_vals['base_price'] = base_price
            #Calculation of price with discount percentage if template has discount percentage
            if template.discount_percentage:
                if not price_list_contains_template:
                    final_price = template.list_price - (template.list_price * (template.discount_percentage / 100))
                else:
                    final_price = price_reduce
                template_price_vals['template_discounted_price'] = final_price
                template_price_vals['template_original_price'] = final_price
            res[template.id] = template_price_vals
        return res
