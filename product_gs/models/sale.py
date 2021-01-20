
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from odoo.http import request

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(string='Request Number')
    date_order = fields.Datetime(string='Request Date')    
    parent_partner_id = fields.Many2one(string='Beneficiaries', comodel_name='res.partner', related='partner_id.parent_id')    

    disposition_type_id = fields.Many2one(comodel_name='disposition.type',ondelete='restrict', index=True)

    loading_dock = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No')])
    trailers = fields.Selection(string='Can Accept \'53 Trailers',selection=[('yes', 'Yes'), ('no', 'No')])
    from_phase_id = fields.Many2one(string='Phase',comodel_name='gs.project.phase')
    expected_delivery_date = fields.Text(string='Expected Delivery Date',)
    preferred_delivery_date = fields.Text(string='Preferred Delivery Date',)
    operating_hours = fields.Text(string='Operating Hours',)
    intend = fields.Text(string='Intend to use this furniture for',)
    offload = fields.Text(string='Describe offloading environment',)

    total_requested_qty = fields.Float(string='Requested', digits='Product Unit of Measure', compute='_get_total_requested')
    total_approved_qty = fields.Float(string='Quantity to approve', digits='Product Unit of Measure', compute='_get_total_approved')
    total_delivered_qty = fields.Float(string='Delivered', digits='Product Unit of Measure', compute='_get_total_delivered')

    mailout = fields.Many2one(comodel_name='product.public.category',ondelete='restrict',readonly=True )

    make_approve_qty_zero = fields.Boolean(default=False)
    
    @api.model
    def run_make_approved_quantity_zero(self):
        Orders = self.search([('make_approve_qty_zero','=',True),('state','=','sent')])
        Orders.mapped('order_line').filtered(lambda l: not l.is_delivery).write({
            'product_uom_qty': 0.0,
        })
        Orders.write({
            'make_approve_qty_zero': False
        })
        return True

    def action_reset_approved(self):
        self.filtered(lambda o: o.state != 'sale').mapped('order_line').filtered(lambda l: not l.is_delivery).write({
            'product_uom_qty': 0.0,
        })

    @api.depends('order_line.requested_qty')
    def _get_total_requested(self):
        for order in self:
            order.total_requested_qty = sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('requested_qty'))

    @api.depends('order_line.product_uom_qty')
    def _get_total_approved(self):
        for order in self:
            # if order.state in ('sale', 'done'):
            order.total_approved_qty = sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('product_uom_qty'))
            # else:
            #     order.total_approved_qty = 0

    @api.depends('order_line.qty_delivered')
    def _get_total_delivered(self):
        for order in self:
            order.total_delivered_qty = sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('qty_delivered'))



    def action_print_tot(self, tot_type='Canada'):
        ReportAction = self.env.ref('product_gs.gs_tot_pdf')
        orders = self.filtered(lambda o: o.state not in ('draft','sent','cancel'))
        for order in orders:
            attachment, pdf = ReportAction._render_qweb_pdf(order.ids, data={'tot_type': tot_type})
            print_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            order.message_post(body='TOT %s report printed on %s.'%(tot_type, print_time), attachments = [('%s-%s'%(order.name, print_time), attachment)])
        return ReportAction.report_action(None, data={'tot_type': tot_type, 'docids':orders.ids})

    def action_tot(self):
        return {
            'name': _('Print TOT'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'tot.wizard',
            'context': {
                'default_order_id': self.id
            },
            'target': 'new'
        }
        

    def action_post(self):
        self.filtered(lambda o: o.state == 'draft').write({
            'state': 'sent'
        })

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            phase = order.mapped('order_line').mapped('product_id').mapped('phase_id')
            if len(phase) != 1:
                raise ValidationError('Items must be from same project/phase.')
            else:
                phase.message_post(body='Request approved <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a>'%(order.id, order.name))
        return res

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
        # change lang to get correct name of attributes/values
        product_with_context = self.env['product.product'].with_context(product_context)
        product = product_with_context.browse(int(product_id))

        try:
            if add_qty:
                add_qty = float(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = float(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]

        # Create line if no line with product_id can be located
        if not order_line:
            if not product:
                raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

            no_variant_attribute_values = kwargs.get('no_variant_attribute_values') or []
            received_no_variant_values = product.env['product.template.attribute.value'].browse([int(ptav['value']) for ptav in no_variant_attribute_values])
            received_combination = product.product_template_attribute_value_ids | received_no_variant_values
            product_template = product.product_tmpl_id

            # handle all cases where incorrect or incomplete data are received
            combination = product_template._get_closest_possible_combination(received_combination)

            # get or create (if dynamic) the correct variant
            product = product_template._create_product_variant(combination)

            if not product:
                raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

            product_id = product.id

            values = self._website_product_id_change(self.id, product_id, qty=1)

            # add no_variant attributes that were not received
            for ptav in combination.filtered(lambda ptav: ptav.attribute_id.create_variant == 'no_variant' and ptav not in received_no_variant_values):
                no_variant_attribute_values.append({
                    'value': ptav.id,
                })

            # save no_variant attributes values
            if no_variant_attribute_values:
                values['product_no_variant_attribute_value_ids'] = [
                    (6, 0, [int(attribute['value']) for attribute in no_variant_attribute_values])
                ]

            # add is_custom attribute values that were not received
            custom_values = kwargs.get('product_custom_attribute_values') or []
            received_custom_values = product.env['product.template.attribute.value'].browse([int(ptav['custom_product_template_attribute_value_id']) for ptav in custom_values])

            for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
                custom_values.append({
                    'custom_product_template_attribute_value_id': ptav.id,
                    'custom_value': '',
                })

            # save is_custom attributes values
            if custom_values:
                values['product_custom_attribute_value_ids'] = [(0, 0, {
                    'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value']
                }) for custom_value in custom_values]

            # create the line
            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1

        # compute new quantity
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)

        # Remove zero of negative lines
        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                # update description of the parent
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
        else:
            # update line
            no_variant_attributes_price_extra = [ptav.price_extra for ptav in order_line.product_no_variant_attribute_value_ids]
            values = self.with_context(no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra))._website_product_id_change(self.id, product_id, qty=quantity)
            if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
                order = self.sudo().browse(self.id)
                product_context.update({
                    'partner': order.partner_id,
                    'quantity': quantity,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                })
                product_with_context = self.env['product.product'].with_context(product_context).with_company(order.company_id.id)
                product = product_with_context.browse(product_id)
                values['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                    order_line._get_display_price(product),
                    order_line.product_id.taxes_id,
                    order_line.tax_id,
                    self.company_id
                )
            values.pop('price_unit', None)
            order_line.write(values)

            # link a product to the sales order
            if kwargs.get('linked_line_id'):
                linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
                order_line.write({
                    'linked_line_id': linked_line.id,
                })
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
            # Generate the description with everything. This is done after
            # creating because the following related fields have to be set:
            # - product_no_variant_attribute_value_ids
            # - product_custom_attribute_value_ids
            # - linked_line_id
            order_line.name = order_line.get_sale_order_line_multiline_description_sale(product)

        option_lines = self.order_line.filtered(lambda l: l.linked_line_id.id == order_line.id)

        return {'line_id': order_line.id, 'quantity': quantity, 'option_ids': list(set(option_lines.ids))}

    def _get_delivery_methods(self):
        return super(SaleOrder, self)._get_delivery_methods() & self.mailout.delivery_ids


    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': 'Request',
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        if self.disposition_type_id.code == 'resale':
            template_id = self.env.ref('product_gs.email_template_request_after_offer').id
        elif self.state == 'sale':
            template_id = self.env.ref('product_gs.email_template_request_confirm').id
        else:
            template_id = self.env.ref('product_gs.email_template_request_after_request').id
        return template_id


class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    phase_id = fields.Many2one(string='Phase',comodel_name='gs.project.phase', related='product_id.phase_id')
    requested_qty = fields.Float(string='Requested', digits='Product Unit of Measure', readonly=True)
    virtual_available = fields.Float('Available', related='product_id.virtual_available')
    disposition_type_id = fields.Many2one(comodel_name='disposition.type', related='order_id.disposition_type_id', readonly=False, store=True, index=True)
    product_uom_qty = fields.Float(string="Quantity to approve")
    tag_ids = fields.Many2many(related='order_id.tag_ids', string="Tags")

    # def _compute_qty_to_deliver(self):
    #     """Compute the visibility of the inventory widget."""
    #     for line in self:
    #         line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
    #         if line.state in ('draft', 'sent') and line.product_type == 'product' and line.qty_to_deliver > 0:
    #             line.display_qty_widget = True
    #         else:
    #             line.display_qty_widget = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_qty = vals.get('product_uom_qty', 1)
            vals.update({'requested_qty': product_qty})
        return super(SaleLine, self).create(vals_list)

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        ##onchange product_uom_qty dont change price_unit
        # if self.order_id.pricelist_id and self.order_id.partner_id:
        #     product = self.product_id.with_context(
        #         lang=self.order_id.partner_id.lang,
        #         partner=self.order_id.partner_id,
        #         quantity=self.product_uom_qty,
        #         date=self.order_id.date_order,
        #         pricelist=self.order_id.pricelist_id.id,
        #         uom=self.product_uom.id,
        #         fiscal_position=self.env.context.get('fiscal_position')
        #     )
        #     self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        ##end

    def action_reset_approved(self):
        self.filtered(lambda l: l.state != 'sale').write({
            'product_uom_qty': 0.0,
        })

class DispositionType(models.Model):
    _name = 'disposition.type'
    _description = 'Disposition Type'

    _rec_name = 'name'
    _order = 'sequence ASC'

    name = fields.Char(string='Name', required=True, default=lambda self: _('New Disposition Type'), copy=False)
    code = fields.Char(string='Code', required=True, copy=False)
    manual_create = fields.Boolean(default=False)
    sequence = fields.Integer(default=10)
    