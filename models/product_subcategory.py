# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models


class ProductSubcategory(models.Model):
    """Record product subcategories"""

    _name = 'product.subcategory'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    product_ids = fields.One2many(
        'product.template', 'subcategory_id', 'Products')
    product_variant_ids = fields.One2many(
        'product.product', 'subcategory_id', 'Products (variants)')
