# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    subcategory_id = fields.Many2one('product.subcategory', 'Subcategory')
