# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


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
    goal = fields.Float('Goal', required=True)
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

    op = fields.Selection([
        ('=', '='),
        ('>', '>'),
        ('<', '<'),
        ('>=', '>='),
        ('<=', '<=')
        ], 'Operator', required=True, default='>=')
    compliance_rate = fields.Float('Compliance Rate (%)', required=True)
    commission = fields.Float('Commission', required=True)
    item_id = fields.Many2one('sale.commission.scheme.item', 'Item')

    @api.constrains('op', 'compliance_rate')
    def _restrict_compliance_rate_duplicated(self):
        """Restricts that users records compliance rates duplicated"""

        for record in self:

            current_id = record.id
            current_item_id = record.item_id.id
            current_op = record.op
            current_compliance_rate = record.compliance_rate

            compliance_rate_exists = self.search([
                ('id', '!=', current_id),
                ('item_id', '=', current_item_id),
                ('op', '=', current_op),
                ('compliance_rate', '=', current_compliance_rate),
            ])

            if compliance_rate_exists:
                raise ValidationError(_('This compliance rate is duplicated'))
