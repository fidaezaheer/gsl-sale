# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError
from odoo.tools import ustr
import os
import base64
import tempfile, zipfile
from zipfile import ZipFile, BadZipfile
from io import BytesIO
from PIL import Image
import io
import codecs
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'


class sh_export_product_image_tmpl(models.TransientModel):
    _name = "green.image.import.tmpl"
    _description = "Import Product Image Template"

    product_tmpl_ids = fields.Many2many('product.template', string='Products', copy=False)

    zip_file = fields.Binary(string='Zip File')
    file_name = fields.Char("File Name")

    @api.model
    def default_get(self, fields):
        rec = super(sh_export_product_image_tmpl, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        if not active_ids:
            raise UserError(_("Programming error: wizard action executed without active_ids in context."))

        if not active_ids or active_model != 'product.template':
            return rec

        product_tmpls = self.env['product.template'].browse(active_ids)

        rec.update({
            'product_tmpl_ids': [(6, 0, product_tmpls.ids)],
        })
        return rec

    def action_import(self):
        if self:
            # choose specific model and field name  based on selection.
            model_obj = ""
            field_name = ""
            skipped_images_dic = {}
            model_obj = self.env['product.template']

            if self.zip_file:
                try:
                    base64_data_file = base64.b64decode(self.zip_file)
                    with ZipFile(io.BytesIO(base64_data_file), 'r') as archive:
                        folder_inside_zip_name = ""
                        counter = 0
                        # print("checking zip folder and fie list......................")
                        #_logger.info("checking zip folder and fie list......................")
                        arr = archive.namelist()
                        #_logger.info(arr)
                        for file_name in archive.namelist():
                            try:
                                img_data = archive.read(file_name)
                                if len(img_data) == 0:
                                    folder_inside_zip_name = file_name
                                    _logger.info("...........folder name: " + file_name)
                                    continue
                                if img_data:
                                    _logger.info("file_name: " + file_name)
                                    # img_name_with_ext = ""
                                    img_name_with_ext = file_name.replace(folder_inside_zip_name, "")
                                    #_logger.info("img name " + img_name_with_ext)
                                    # print(img_name_with_ext)
                                    just_img_name = ""
                                    if img_name_with_ext != "":
                                        just_img_name = os.path.splitext(img_name_with_ext)[0]
                                        # print("img name ",img_name_with_ext)
                                        if img_name_with_ext != "" and model_obj != "":
                                            # print(self.product_tmpl_ids)
                                            for product in self.product_tmpl_ids:
                                                # print(product)
                                                if img_name_with_ext == product.photo_id:
                                                    image_base64 = codecs.encode(img_data, 'base64')
                                                    product.sudo().write({
                                                        'image_1920': image_base64,
                                                    })
                                                    counter += 1
                                        else:
                                            skipped_images_dic[
                                                img_name_with_ext] = " - Record not found for this image " + img_name_with_ext
                                    else:
                                        skipped_images_dic[
                                            img_name_with_ext] = " - Image name not resolve for this image " + file_name
                                else:
                                    skipped_images_dic[
                                        img_name_with_ext] = " - Image data not found for this image " + file_name


                            except Exception as e:
                                skipped_images_dic[file_name] = " - Value is not valid. " + ustr(e)
                                continue

                        # show success message here.
                        res = self.show_success_msg(counter, skipped_images_dic)
                        return res

                except Exception as e:
                    msg = "Something went wrong - " + ustr(e)
                    raise UserError(_(msg))

            # ====================================================
            # Return self object of wizard.
            # ====================================================
            return {
                'name': 'Import Images(Wizard)',
                'view_mode': 'form',
                'res_id': self.id,
                'res_model': 'green.image.import.tmpl',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }

    def show_success_msg(self, counter, skipped_images_dic):
        # to close the current active wizard
        # action = self.env.ref('green_image_importer.green_image_import_product_tmpl_action').read()[0]
        # action = {'type': 'ir.actions.act_window_close'}
        # open the new success message box
        view = self.env.ref('green_image_importer.green_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        dic_msg = str(counter) + " Images imported successfully"
        if skipped_images_dic:
            dic_msg = dic_msg + "\nNote:"
        for k, v in skipped_images_dic.items():
            dic_msg = dic_msg + "\nImage name " + k + " " + v + " "
        context['message'] = dic_msg
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'green.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }