# coding : utf - 8

from odoo.addons.sale_product_configurator.controllers.main import ProductConfiguratorController


class ProductConfiguratorControllerXX(ProductConfiguratorController):

    def _get_basic_product_information(self, product_or_template, pricelist, combination, **kwargs):
        """Update discounted price in configurator"""
        basic_information = dict(
            **product_or_template.read(['description_sale', 'display_name'])[0]
        )
        # If the product is a template, check the combination to compute the name to take dynamic
        # and no_variant attributes into account. Also, drop the id which was auto-included by the
        # search but isn't relevant since it is supposed to be the id of a `product.product` record.
        if not product_or_template.is_product_variant:
            basic_information['id'] = False
            combination_name = combination._get_combination_name()
            if combination_name:
                basic_information.update(
                    display_name=f"{basic_information['display_name']} ({combination_name})"
                )
        final_price = pricelist._get_product_price(product_or_template.with_context(
            **product_or_template._get_product_price_context(combination)
        ),
            **kwargs,
        )
        if product_or_template.discount_percentage > 0:
            actual_price = pricelist._get_product_price(
                product_or_template.with_context(
                    **product_or_template._get_product_price_context(combination)
                ),
                **kwargs,
            )
            final_price = actual_price - (actual_price * (product_or_template.discount_percentage / 100))
        return dict(
            **basic_information,
            price=final_price
        )
