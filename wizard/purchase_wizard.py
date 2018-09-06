# -*- coding: utf-8 -*-
import logging
import openerp.addons.decimal_precision as dp
from datetime import datetime

from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)


class LogisticaPurchaseWizard(models.TransientModel):
    _name = 'logistica.purchase.wizard'

    def _get_default_purchase_line(self):
        logistica_pedidos = self.env['rpt_pedidos_logistica'].browse(self._context.get('active_ids', []))
        transportistas = logistica_pedidos.mapped('transportista_id')
        transportistas = set(transportistas)

        purchase_line_ids = []

        currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        pricelist_id = self.env['product.pricelist'].search(
            [('currency_id', '=', currency_id.id)],
            limit=1)

        for transportista in transportistas:
            detalles = []
            for linea in logistica_pedidos:
                if (not linea.move_id.purchase_id and not linea.exportacion_line_id.purchase_id) and transportista.id == linea.transportista_id.id:
                    detalles.append((0, False, {
                        'sequence': detalles and detalles[-1][2]['sequence'] + 10 or 10,
                        'name': linea.servicio_id.name,
                        'product_qty': linea.cantidad_transportada or 1,
                        'price_unit': linea.transportista_precio_unitario,
                        'tax_id': linea.tarifa_linea_id.tax_id.id,
                        'valor_sin_igv': linea.valor_sin_igv,
                        'product_id': linea.servicio_id.id,
                        'move_id': linea.move_id,
                        'exportacion_line_id': linea.exportacion_line_id,
                    }))
            if detalles:
                purchase_line_ids.append((0, False, {
                    'partner_id': transportista.id,
                    'location_id': transportista.property_stock_customer.id,
                    'pricelist_id': pricelist_id.exists() and pricelist_id.id or False,
                    'currency_id': currency_id.id,
                    'detalle_ids': detalles,
                    'detalle_count': len(detalles),
                }))
        return purchase_line_ids

    purchase_line_ids = fields.Many2many('logistica.purchase.line', 'marcar_hecho_mrp_production',
                                         default=_get_default_purchase_line)

    @api.multi
    def generar_pedido_compra(self):
        for wizard in self:
            wizard.purchase_line_ids.crear_pc()


class LogisticaPurchaseLineWizard(models.TransientModel):
    _name = 'logistica.purchase.line'

    partner_id = fields.Many2one('res.partner', u'Proveedor')
    currency_id = fields.Many2one('res.currency')
    location_id = fields.Many2one('stock.location', u'Ubicación de destino', required=True)
    pricelist_id = fields.Many2one('product.pricelist', u'Lista de precios', required=True)
    detalle_ids = fields.One2many('logistica.purchase.line.detalle', 'line_id', 'Detalles')
    detalle_count = fields.Integer(u'Líneas de pedido')

    @api.multi
    def crear_pc(self):
        for linea in self:
            order_line = [(0, False, {
                u'sequence': detalle.sequence,
                u'date_planned': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                u'price_unit': detalle.price_unit,
                u'product_uom': 1,
                u'taxes_id': [(6, False, [detalle.tax_id.id])],
                u'product_qty': detalle.product_qty,
                u'name': detalle.product_id.name,
                u'product_id': detalle.product_id.id
            }) for detalle in linea.detalle_ids]
            vals = {
                u'date_planned': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                u'currency_id': linea.currency_id.id,
                u'partner_id': linea.partner_id.id,
                # u'origin': linea.origen,
                u'location_id': linea.location_id.id,
                u'pricelist_id': linea.pricelist_id.id,
                u'order_line': order_line,
            }
            purchase = self.env['purchase.order'].create(vals)
            for detalle in linea.detalle_ids:
                if detalle.move_id:
                    detalle.move_id.write({'purchase_id': purchase.id})
                elif detalle.exportacion_line_id:
                    detalle.exportacion_line_id.write({'purchase_id': purchase.id})


class LogisticaPurchaseLineDetalleWizard(models.TransientModel):
    _name = 'logistica.purchase.line.detalle'

    line_id = fields.Many2one('logistica.purchase.line')
    sequence = fields.Integer()
    price_unit = fields.Float()
    product_id = fields.Many2one('product.product')
    name = fields.Char(u'Nombre')
    product_uom = fields.Many2one('product.uom')
    tax_id = fields.Many2one('account.tax')
    product_qty = fields.Float()
    move_id = fields.Many2one('stock.move')
    exportacion_line_id = fields.Many2one('sale.order.transporte.linea')
