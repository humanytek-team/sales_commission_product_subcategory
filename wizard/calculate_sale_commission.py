# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime
import operator

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

OPERATORS = {
    '=': operator.eq,
    '<=': operator.le,
    '<': operator.lt,
    '>=': operator.ge,
    '>': operator.gt,
}


class CalculateSaleCommission(models.TransientModel):
    _name = 'calculate.sale.commission'

    def _get_start_date(self):
        """Returns date with first day of the current month"""

        current_date = datetime.today().strftime('%Y-%m-')
        date_first_day_month = '{0}{1}'.format(current_date, '01')
        return date_first_day_month

    def _get_end_date(self):
        """Returns date with first day of the current month"""

        current_date = datetime.today().strftime('%Y-%m-')
        date_first_day_month = '{0}{1}'.format(current_date, '01')
        return date_first_day_month

    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=_get_start_date)

    end_date = fields.Date(
        string='End Date',
        required=True,
        default=lambda self: datetime.today().strftime('%Y-%m-%d'))

    sale_commission_scheme_id = fields.Many2one(
        'sale.commission.scheme', 'Sale commission scheme', required=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Check that end date to be greater than start date"""
        for record in self:
            if record.end_date < record.start_date:
                raise ValidationError(
                    _('End date must be greater than Start Date'))

    @api.onchange('start_date', 'end_date')
    def set_domain_sale_commission_scheme(self):
        """Sets domain for field sale_commission_scheme_id based on values
        of fields start_date and end_date."""

        if self.start_date and self.end_date:
            return {
                'domain': {
                    'sale_commission_scheme_id': [
                        ('start_date', '<=', self.start_date),
                        ('end_date', '>=', self.end_date),
                        ]
                    }}

    @api.multi
    def calculate_sale_commission(self):
        """Calculates sale commissions for sales reps grouped by product
        subcategory"""

        self.ensure_one()
        start_date = self.start_date
        end_date = self.end_date
        scheme = self.sale_commission_scheme_id
        scheme_product_subcategories_ids = scheme.item_ids.mapped(
            'product_subcategory_id.id')

        SaleOrder = self.env['sale.order']
        sale_orders = SaleOrder.search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', '=', 'sale'),
            ])

        sales_by_rep = dict()

        for so in sale_orders:
            if str(so.company_id.id) not in sales_by_rep:

                sales_by_rep[str(so.company_id.id)] = dict()
                sales_by_rep[str(so.company_id.id)][str(so.user_id.id)] = list()

            else:
                if str(so.user_id.id) not in sales_by_rep[str(so.company_id.id)]:

                    sales_by_rep[str(so.company_id.id)][str(so.user_id.id)] = list()

            for line in so.order_line:

                if line.product_id.subcategory_id and \
                    line.product_id.subcategory_id.id in \
                        scheme_product_subcategories_ids and \
                            line.price_total > 0:

                    try:
                        sales_product_subcategory = (
                            sale
                            for sale in sales_by_rep[
                                str(so.company_id.id)][str(so.user_id.id)]
                            if str(line.product_id.subcategory_id.id)
                            in sale).next()

                        if sales_product_subcategory:
                            sales_product_subcategory[
                                str(line.product_id.subcategory_id.id)] += \
                                    line.price_total

                    except StopIteration:
                        sales_by_rep[str(so.company_id.id)][
                            str(so.user_id.id)].append({
                                str(line.product_id.subcategory_id.id): \
                                    line.price_total
                                })

        ops_greater_than = ['>', '>=']
        ops_less_than = ['<', '<=']
        SaleCommissionsCalculated = self.env['sale.commissions.calculated']
        commissions_found = False

        for item in scheme.item_ids:
            subcategory_id = item.product_subcategory_id.id
            goal = item.goal

            for company_id in sales_by_rep:

                for sales_rep_id in sales_by_rep[company_id]:

                    for sales_by_subcat in \
                        sales_by_rep[company_id][sales_rep_id]:

                        if str(subcategory_id) in sales_by_subcat:

                            sales_total = sales_by_subcat[str(subcategory_id)]
                            sales_total_percentage_goal = \
                                (sales_total * 100) / goal

                            commission = 0.0
                            compliance_rate = 0.0
                            for commission_rate in \
                                item.commission_compliance_rate_ids:

                                if OPERATORS[commission_rate.op](
                                    sales_total_percentage_goal,
                                    commission_rate.compliance_rate):

                                    if not commission:
                                        commission = commission_rate.commission
                                        compliance_rate = \
                                            commission_rate.compliance_rate
                                    else:
                                        if commission_rate.op in ops_greater_than:
                                            if commission_rate.compliance_rate \
                                                > compliance_rate:

                                                commission = \
                                                    commission_rate.commission
                                                compliance_rate = \
                                                    commission_rate.compliance_rate

                                        if commission_rate.op in ops_less_than:
                                            if commission_rate.compliance_rate \
                                                < compliance_rate:

                                                commission = \
                                                    commission_rate.commission
                                                compliance_rate = \
                                                    commission_rate.compliance_rate

                            if commission:
                                SaleCommissionsCalculated.create({
                                    'company_id': int(company_id),
                                    'sales_rep_id': int(sales_rep_id),
                                    'product_subcategory_id': subcategory_id,
                                    'commission': commission,
                                    'sales_total': sales_total,
                                    'wizard_id': self.id,
                                })

                                if not commissions_found:
                                    commissions_found = True

        if commissions_found:
            view = self.env.ref(
                'sales_commission_product_subcategory.sale_commissions_calculated_tree')

            context = {
                'search_default_group_by_company': True,
                'search_default_group_by_sales_rep': True,
                }
            context.update(self._context)

            return {
                'name': _('Commissions'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'sale.commissions.calculated',
                'views': [(view.id, 'tree')],
                'type': 'ir.actions.act_window',
                'view_id': False,
                'domain': "[('wizard_id', '=', %s)]" % self.id
            }

        else:

            raise ValidationError(
                _('the calculation not returned commissions for any sales rep.')
                )


class SaleCommissionsCalculated(models.TransientModel):
    _name = 'sale.commissions.calculated'

    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id)
    sales_rep_id = fields.Many2one('res.users', 'Sales rep', required=True)
    product_subcategory_id = fields.Many2one(
        'product.subcategory', 'Product Subcategory', required=True)
    commission = fields.Float('Commission', required=True)
    sales_total = fields.Float('Sales Total', required=True)
    wizard_id = fields.Many2one(
        'calculate.sale.commission',
        'Wizard that calculates the commissions')
