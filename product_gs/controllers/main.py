
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.tools.misc import xlwt

import logging
_logger = logging.getLogger(__name__)


class MailOut(WebsiteSale):
    # @http.route(['''/mailout/<model("product.public.category"):category>'''], type='http', auth="public", website=True)
    # def mailout(self, page=0, category=None, search='', ppg=False, **post):
    #     return super(MailOut, self).shop(page, category, search, ppg, **post)
    
    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        response = super(MailOut, self).shop(spage=page, category=category, search=search, ppg=ppg, **post)
        if category and isinstance(category, str):
            request.session['mailout_visited'] = int(category)
        elif category:
            request.session['mailout_visited'] = category.id
        else:
            pass
        return response


    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        mailout = False
        if 'mailout_visited' in request.session:
            mailout = request.env['product.public.category'].browse(request.session.get('mailout_visited'))
            if sale_order.mailout and sale_order.mailout != mailout:
                sale_order.message_post(body='Mailout mismatch.')
                sale_order.action_cancel()
                request.session['sale_order_id'] = None
                sale_order = request.website.sale_get_order(force_create=True)
            if not sale_order.mailout:
                sale_order.write({
                    'mailout': mailout.id,
                    'disposition_type_id': request.env['disposition.type'].sudo().search([('code','=',mailout.request_type)], limit=1).id
                })

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        res = sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        line_id = request.env['sale.order.line'].sudo().browse(res.get('line_id'))
        # request_type = kw.get('type', False)
        # if request_type:
        #     price_unit = kw.get('resale_donation')
        #     line_id.write({
        #         'price_unit': float(price_unit),
        #     })

        if kw.get('express'):
            return request.redirect("/shop/checkout?express=1")
        ##return to mailout page from add to cart
        if mailout:
            return request.redirect("/shop/category/%s"%slug(mailout))
        ##end
        return request.redirect("/shop/cart")

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.website.viewref('website_sale.extra_info_option')
        if extra_step.active:
            return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment")
    
    def _prepare_product_values(self, product, category, search, **kwargs):
        res = super(MailOut, self)._prepare_product_values(product, category, search, **kwargs)
        request_type = kwargs.get('request_type', False)
        return dict(res, request_type=request_type)
    
    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if order and not order.amount_total and not tx:
            order.write({'state': 'sent'})
            request.website.sale_reset()
            return request.redirect('/shop/confirmation')

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        PaymentProcessing.remove_payment_transaction(tx)
        return request.redirect('/shop/confirmation')

    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def checkout(self, **post):
        order = request.website.sale_get_order()
        ##########start custom code
        for line in order.order_line:
            line.write({
                'requested_qty': line.product_uom_qty
            })
        order.make_approve_qty_zero = True
        ##########end
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            return request.redirect('/shop/address')

        for f in self._get_mandatory_billing_fields():
            if not order.partner_id[f]:
                return request.redirect('/shop/address?partner_id=%d' % order.partner_id.id)

        values = self.checkout_values(**post)

        if post.get('express'):
            return request.redirect('/shop/confirm_order')

        values.update({'website_sale_order': order})

        # Avoid useless rendering if called in ajax
        if post.get('xhr'):
            return 'ok'
        return request.render("website_sale.checkout", values)
    
    # ------------------------------------------------------
    # Extra step
    # ------------------------------------------------------
    @http.route(['/shop/extra_info'], type='http', auth="public", website=True, sitemap=False)
    def extra_info(self, **post):
        order = request.website.sale_get_order()
        if order.disposition_type_id.code != 'donation':
            return request.redirect("/shop/payment")
        return super(MailOut, self).extra_info(**post)

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            # partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
            email = checkout.get('email')
            vat = checkout.get('vat')
            email_partner = Partner.sudo().search([('email','=',email)],limit=1)
            parent_email = email_partner.parent_id or email_partner
            order = request.website.sale_get_order()
            if email_partner:
                order.partner_shipping_id = self._match_or_create_address(parent_email, checkout)
                partner_id = email_partner.id
            else:
                vat_partner = Partner.sudo().search([('vat','=',vat),('vat','not in', ('', False))],limit=1)
                if vat_partner:
                    partner_id = Partner.sudo().with_context(tracking_disable=True).create({
                        'name': checkout.get('name', None),
                        'function': checkout.get('function', None),
                        'mobile': checkout.get('mobile', None),
                        'email': email,
                        'parent_id': vat_partner.id,
                        'type': 'contact',
                        'street': checkout.get('street'),
                        'street2': checkout.get('street2'),
                        'zip': checkout.get('zip'),
                        'city': checkout.get('city', None),
                        'country_id': checkout.get('country_id', None),
                        'state_id': checkout.get('state_id', None),
                        'phone': checkout.get('phone',None),
                    }).id
                    order.partner_shipping_id = self._match_or_create_address(vat_partner, checkout)
                else:
                    company = Partner.sudo().with_context(tracking_disable=True).create({
                        'name': checkout.get('company_name',None),
                        'website': checkout.get('website',None),
                        'phone': checkout.get('phone',None),
                        'is_company': True,
                        'vat': vat,
                        'child_ids': [(0, 0, {
                            'name': checkout.get('name', None),
                            'function': checkout.get('function', None),
                            'mobile': checkout.get('mobile', None),
                            'email': email,
                            'type': 'contact',
                            'street': checkout.get('street'),
                            'street2': checkout.get('street2'),
                            'zip': checkout.get('zip'),
                            'city': checkout.get('city', None),
                            'country_id': checkout.get('country_id', None),
                            'state_id': checkout.get('state_id', None)})],
                            'phone': checkout.get('phone',None),
                    })
                    partner_id = company.child_ids[0].id
                    order.partner_shipping_id = self._match_or_create_address(company, checkout)
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
                    return Forbidden()
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    def _match_or_create_address(self, partner, checkout):
        Partner = request.env['res.partner']
        street = checkout.get('street')
        street2 = checkout.get('street2')
        azip = checkout.get('zip')
        delivery = partner.child_ids.filtered(lambda c: c.street == street or c.street2 == street2 or c.zip == azip)
        if not delivery:
            delivery = Partner.sudo().with_context(tracking_disable=True).create({
                'name': checkout.get('name', None),
                'street': street,
                'street2': street2,
                'zip': azip,
                'country_id': checkout.get('country_id', None),
                'state_id': checkout.get('state_id', None),
                'city': checkout.get('city', None),
                'parent_id': partner.id,
                'type': 'delivery'
            })
        return delivery[0]


class ExportReport(http.Controller):

    @http.route('/gs/export/check_xlwt', type='json', auth='none')
    def check_xlwt(self):
        return xlwt is not None

    @http.route('/gs/export/export_xls', type='http', auth="user")
    def export_xls(self, data, token):
        data = json.loads(data)
        phase_id = int(data.get('phase_id', False))
        if not phase_id:
            return
        phase = request.env['gs.project.phase'].browse(phase_id)
        los_data = phase._get_los_data()
        header = ['Item','Open','Closed','Present'] + los_data['dispositions'].mapped('name') + los_data['partners'].mapped('name')
        line_data = [[line['item'].display_name]+line['data'] for line in los_data['lines']]
        xdata = [header] +line_data
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(phase.name)
        for row,row_data in enumerate(xdata):
            for cell, cell_data in enumerate(row_data):
                worksheet.write(row, cell, cell_data)
        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=%s.xls'%phase.name.replace(' ', '_'))],)
        workbook.save(response.stream)

        return response
