# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models


class SaleCommissionScheme(models.Model):
    """records sale commissions schemes"""

    _name = 'sale.commission.scheme'

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    active = fields.Boolean('Active', default=True)
    item_ids = fields.One2many(
        'sale.commission.scheme.item',
        'scheme_id',
        'Items')


class SaleCommissionSchemeItem(models.Model):
    """Records items of sale commissions schemes"""

    _name = "sale.commission.scheme.item"
    _rec_name = 'product_subcategory_id'

    product_subcategory_id = fields.Many2one(
        'product.subcategory', 'Product Subcategory')
    commission_compliance_rate_ids = fields.One2many(
        'sale.commission.compliance.rate',
        'item_id',
        'Commissions per compliance rate')
    scheme_id = fields.Many2one(
        'sale.commission.scheme', 'Sale commissions scheme')


class SaleCommissionComplianceRate(models.Model):
    """Records compliance rates and asociates to items of a sale commission
    scheme. """

    _name = 'sale.commission.compliance.rate'
    _rec_name = 'compliance_rate'

    compliance_rate = fields.Float('Compliance Rate (%)', required=True)
    commission = fields.Float('Commission', required=True)
    item_id = fields.Many2one('sale.commission.scheme.item', 'Item')
