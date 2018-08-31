# coding=utf-8

from openerp import models, fields
from openerp import tools
import openerp.addons.decimal_precision as dp


class ReportLogisticaPedidos(models.Model):
    """Events Analysis"""
    _name = "rpt_pedidos_logistica"
    _order = 'date_order desc'
    _auto = False

    partner_id = fields.Many2one('res.partner', string=u'Cliente', readonly=True)
    order_id = fields.Many2one('sale.order', string=u'Pedido de venta', readonly=True)
    order_exportacion = fields.Boolean(u'Exportación', readonly=True)
    date_order = fields.Datetime(u'Fecha de ped. de vtas', readonly=True)
    invoice_id = fields.Many2one('account.invoice', string=u'Factura relacionada', readonly=True)
    product_id = fields.Many2one('product.product', string=u'Producto / Servicio', readonly=True)
    precio_venta_unitario = fields.Float(string='Precio unit.', readonly=True,
                                         digits=dp.get_precision('Product Price'))
    cantidad_transportada = fields.Float(string='Cantidad transp.',
                                         digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    uom_id = fields.Many2one('product.uom', string=u'Unidad de medida', readonly=True)
    picking_id = fields.Many2one('stock.picking', string=u'Albarán de salida', readonly=True)
    guia_remision_impresa = fields.Char(u'Guía de remisión impresa', readonly=True)
    transportista_id = fields.Many2one('res.partner', string=u'Transportista', readonly=True)
    servicio_id = fields.Many2one('product.product', string=u'Servicio', readonly=True)
    ruta_id = fields.Many2one('logistica.ruta', string=u'Ruta', readonly=True)
    transportista_precio_unitario = fields.Float(string=u'Costo unitario', readonly=True,
                                                 digits=dp.get_precision('Product Price'))
    tarifa_linea_id = fields.Many2one('logistica.transporte.tarifa.linea', readonly=True)
    move_id = fields.Many2one('stock.move', readonly=True)
    purchase_id = fields.Many2one('purchase.order', 'Pedido de compra', related='move_id.purchase_id', readonly=True)
    valor_sin_igv = fields.Float(string=u'Subtotal', readonly=True,
                                 digits=dp.get_precision('Account'))
    promedio = fields.Float(string=u'Promedio', readonly=True,
                            digits=dp.get_precision('Account'))

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'rpt_pedidos_logistica')
        cr.execute(""" 
        CREATE VIEW rpt_pedidos_logistica AS 
SELECT
  sm.id as id,
  so.partner_id as partner_id,
  so.id as order_id,
  so.exportacion as order_exportacion,
  so.date_order as date_order,
  inv.id as invoice_id,
  sl.product_id as product_id,
  sl.price_unit as precio_venta_unitario,
  sm.product_qty as cantidad_transportada,
  sm.product_uom as uom_id,
  sp.id as picking_id,
  sp.guia_remision as guia_remision_impresa,
  sp.transportista_id as transportista_id,
  ll.product_id as servicio_id,
  ll.ruta_id as ruta_id,
  ll.precio_unitario as transportista_precio_unitario,
  ll.precio_unitario * sm.product_qty as valor_sin_igv,
  ((sl.price_unit * sm.product_qty) - (ll.precio_unitario * sm.product_qty)) / sm.product_qty as promedio,
  ll.id as tarifa_linea_id,
  sm.id as move_id

FROM stock_picking sp
  INNER JOIN sale_order so ON sp.origin = so.name
  INNER JOIN account_invoice inv ON inv.origin = so.name
  INNER JOIN stock_move sm ON sp.id = sm.picking_id
  INNER JOIN sale_order_line sl ON sm.product_id = sl.product_id AND so.id = sl.order_id
  INNER JOIN sale_order_transporte_linea tl ON tl.product_id = sl.product_id AND tl.order_id = sl.order_id
  INNER JOIN res_partner partner ON so.partner_id = partner.id
  INNER JOIN logistica_transporte_tarifa tarifa ON tarifa.partner_id = so.partner_id OR tarifa.partner_id = partner.parent_id OR tarifa.invoice_id = so.invoice_id
   INNER JOIN logistica_transporte_tarifa_linea ll
     ON ll.transportista_id = sp.transportista_id
        AND tarifa.id = ll.transporte_tarifa_id
        AND ll.transporte_tipo_id = tl.tipo_transporte_id
         AND ll.ruta_id =tl.ruta_nacional_id
  WHERE
    sp.state in ('done')

UNION
  
SELECT
  sm.id * ll.id as id,
  so.partner_id as partner_id,
  so.id as order_id,
  so.exportacion as order_exportacion,
  so.date_order as date_order,
  inv.id as invoice_id,
  sl.product_id as product_id,
  sl.price_unit as precio_venta_unitario,
  NULL as cantidad_transportada,
  NULL as uom_id,
  sp.id as picking_id,
  NULL as guia_remision_impresa,
  ll.transportista_id as transportista_id,
  ll.product_id as servicio_id,
  ll.ruta_id as ruta_id,
  ll.precio_unitario as transportista_precio_unitario,
  ll.precio_unitario as valor_sin_igv,
  NULL as promedio,
  ll.id as tarifa_linea_id,
  sm.id as move_id
FROM stock_picking sp
  INNER JOIN sale_order so ON sp.origin = so.name
  INNER JOIN account_invoice inv ON inv.origin = so.name
  INNER JOIN stock_move sm ON sp.id = sm.picking_id
  INNER JOIN sale_order_line sl ON sm.product_id = sl.product_id AND so.id = sl.order_id
  INNER JOIN sale_order_transporte_linea tl ON tl.product_id = sl.product_id AND tl.order_id = sl.order_id
  INNER JOIN res_partner partner ON so.partner_id = partner.id
  INNER JOIN logistica_transporte_tarifa tarifa ON tarifa.partner_id = so.partner_id OR tarifa.partner_id = partner.parent_id OR tarifa.invoice_id = so.invoice_id
   INNER JOIN logistica_transporte_tarifa_linea ll
        ON tarifa.id = ll.transporte_tarifa_id
         AND ll.ruta_id =tl.ruta_internacional_id
          AND ll.tipo = 'gasto_exportacion'
  WHERE
    sp.state in ('done')
        """)
