# coding=utf-8
from openerp import fields, models, api, _
import logging

from openerp.exceptions import ValidationError


class StockPickingTransporte(models.Model):
    _inherit = 'stock.picking'

    order_transporte = fields.Boolean(related='sale_id.utiliza_transporte')
    order_transporte_line_ids = fields.One2many(related='sale_id.transporte_linea_ids')
    transportista_id = fields.Many2one('res.partner', u'Transportista')
    guia_remision = fields.Char(u'Guía de remisión')
    sale_invoice_id = fields.Many2one('account.invoice', related='sale_id.invoice_id')

    @api.constrains('transportista_id')
    def check_transportista_id(self):
        validado = True
        if self.transportista_id:
            mensaje = ''
            for tline in self.order_transporte_line_ids:
                for mline in self.move_lines:
                    if tline.product_id == mline.product_id:
                        # partner_id = self.partner_id
                        partner_id = self.partner_id.parent_id and self.partner_id.parent_id or self.partner_id
                        conteo = self.env['logistica.transporte.tarifa.linea'].search_count(
                            [('transporte_tarifa_partner_id', '=', partner_id.id),
                             ('transporte_tipo_id', '=', tline.tipo_transporte_id.id),
                             ('ruta_id', '=', tline.ruta_nacional_id.id),
                             ('transportista_id', '=', self.transportista_id.id)])
                        if conteo == 0:
                            mensaje = mensaje + 'partner_id: {}, tranporte_tipo_id: {}, ruta_id: {}-{}, transportista_id: {} \n'.format(
                                partner_id.name, tline.tipo_transporte_id.name, tline.ruta_nacional_id.origen,tline.ruta_nacional_id.destino,
                                self.transportista_id.name)

                            validado = False
        if not validado:
            raise ValidationError(_('El transportista seleccionado tiene el siguiente error {}'.format(mensaje)))
