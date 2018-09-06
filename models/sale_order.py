# coding=utf-8
import logging

from openerp import fields, models, api

_logger = logging.getLogger(__name__)


class SaleOrderTransporte(models.Model):
    _inherit = 'sale.order'

    partner_parent_id = fields.Many2one('res.partner', related='partner_id.parent_id')
    utiliza_transporte = fields.Boolean(u'Utiliza transporte')
    exportacion = fields.Boolean(u'Exportación')
    invoice_id = fields.Many2one('account.invoice', u'Factura relacionada')
    tarifa_transporte_id = fields.Many2one('logistica.transporte.tarifa', u'Tarifa')
    tarifa_transporte_ruta_id = fields.Many2one('logistica.ruta', u'Ruta internacional',
                                                related='tarifa_transporte_id.ruta_internacional_id')
    transporte_linea_ids = fields.One2many('sale.order.transporte.linea', 'order_id')

    @api.onchange('tarifa_transporte_id')
    def onchange_tarifa_transporte_id(self):
        if self.exportacion and self.invoice_id:
            tarifa = self.env['logistica.transporte.tarifa'].search([('invoice_id', '=', self.invoice_id.id)], limit=1)
            self.tarifa_transporte_id = tarifa

    @api.onchange('order_line')
    def onchange_order_line(self):
        if self.utiliza_transporte:
            ruta_nacional = self.env['logistica.ruta'].search([('tipo_ruta', '=', 'n')], limit=1)
            tipo_transporte = self.env['logistica.transporte.tipo'].search([], limit=1)
            ruta_internacional_id = False

            if self.exportacion:
                ruta_internacional = self.env['logistica.ruta'].search([('tipo_ruta', '=', 'i')], limit=1)
                ruta_internacional_id = ruta_internacional.exists() and ruta_internacional.id or False

            transporte_linea_ids = [(0, 0, {
                'product_id': line.product_id.id,
                'ruta_nacional_id': ruta_nacional.exists() and ruta_nacional.id or False,
                'tipo_transporte_id': tipo_transporte.exists() and tipo_transporte.id or False,
                'ruta_internacional_id': ruta_internacional_id,
            }) for line in self.order_line]

            self.transporte_linea_ids = transporte_linea_ids

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        sale_order = super(SaleOrderTransporte, self).create(vals)
        lineas = sale_order.mapped('order_line')
        transporte_lineas = sale_order.mapped('transporte_linea_ids')

        for tlinea in transporte_lineas:
            for linea in lineas:
                if tlinea.product_id == linea.product_id:
                    tlinea.write({'line_id': linea.id})
        return sale_order

    @api.onchange('utiliza_transporte')
    def onchange_utiliza_transporte(self):
        if self.utiliza_transporte:
            self.onchange_order_line()


class SaleOrderTransporteLine(models.Model):
    _name = 'sale.order.transporte.linea'

    order_id = fields.Many2one('sale.order')
    line_id = fields.Many2one('sale.order.line')
    order_exportacion = fields.Boolean(related='order_id.exportacion', readonly=True)
    order_partner_id = fields.Many2one('res.partner', related='order_id.partner_id', readonly=True)
    order_inv_id = fields.Many2one('account.invoice', related='order_id.invoice_id', readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    tarifa_id = fields.Many2one('logistica.transporte.tarifa.linea', u'Tarifa')
    ruta_nacional_id = fields.Many2one('logistica.ruta', 'Ruta de transporte local', required=True)
    tipo_transporte_id = fields.Many2one('logistica.transporte.tipo', 'Tipo de transporte', required=True)
    ruta_internacional_id = fields.Many2one('logistica.ruta', 'Ruta de transporte internacional')
    purchase_id = fields.Many2one('purchase.order')
