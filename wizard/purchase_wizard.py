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
        purchase_line_ids = []
        for linea in logistica_pedidos:
            if not linea.purchase_id:
                pricelist_id = self.env['product.pricelist'].search(
                    [('currency_id', '=', linea.tarifa_linea_id.currency_id.id)],
                    limit=1)
                purchase_line_ids.append((0, False, {
                    'product_id': linea.servicio_id.id,
                    'partner_id': linea.transportista_id.id,
                    'origen': linea.picking_id.name,
                    'name': linea.servicio_id.name,
                    'product_qty': linea.cantidad_transportada or 1,
                    'precio_unitario': linea.transportista_precio_unitario,
                    'tax_id': linea.tarifa_linea_id.tax_id.id,
                    'valor_sin_igv': linea.valor_sin_igv,
                    'sale_id': linea.order_id,
                    'picking_id': linea.picking_id,
                    'currency_id': linea.tarifa_linea_id.currency_id.id,
                    'move_id': linea.move_id,
                    'pricelist_id': pricelist_id.exists() and pricelist_id.id or False,
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

    product_id = fields.Many2one('product.product', u'Producto o Servicio')
    partner_id = fields.Many2one('res.partner', u'Proveedor')
    name = fields.Char(u'Descripción')
    product_qty = fields.Float('Cantidad', digits=dp.get_precision('Product Unit of Measure'))
    precio_unitario = fields.Float('Precio unit.')
    tax_id = fields.Many2one('account.tax', 'Impuesto')
    valor_sin_igv = fields.Float('Valor sin IGV', digits=dp.get_precision('Account'))
    sale_id = fields.Many2one('sale.order')
    picking_id = fields.Many2one('stock.picking')
    origen = fields.Char(u'Orígen')
    currency_id = fields.Many2one('res.currency')
    move_id = fields.Many2one('stock.move')
    location_id = fields.Many2one('stock.location', u'Ubicación de destino', required=True)
    pricelist_id = fields.Many2one('product.pricelist', u'Lista de precios', required=True)

    @api.multi
    def crear_pc(self):
        for linea in self:
            vals = {
                u'date_planned': linea.sale_id and linea.sale_id.date_order or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                u'currency_id': linea.currency_id.id,
                u'partner_id': linea.partner_id.id,
                u'origin': linea.origen,
                u'location_id': linea.location_id.id,
                u'pricelist_id': linea.pricelist_id.id,
                u'order_line': [(0, False, {
                    u'sequence': 10,
                    u'date_planned': linea.sale_id and linea.sale_id.date_order or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    u'price_unit': linea.precio_unitario,
                    u'product_uom': 1,
                    u'taxes_id': [(6, False, [linea.tax_id.id])],
                    u'product_qty': linea.product_qty,
                    u'name': linea.product_id.name,
                    u'product_id': linea.product_id.id
                })]
            }
            purchase = self.env['purchase.order'].create(vals)
            linea.move_id.write({'purchase_id': purchase.id})
