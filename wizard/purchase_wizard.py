# -*- coding: utf-8 -*-
import logging
import openerp.addons.decimal_precision as dp

from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)


class LogisticaPurchaseWizard(models.TransientModel):
    _name = 'logistica.purchase.wizard'

    def _get_default_purchase_line(self):
        logistica_pedidos = self.env['rpt_pedidos_logistica'].browse(self._context.get('active_ids', []))
        purchase_line_ids = []
        for linea in logistica_pedidos:
            purchase_line_ids.append((0,False,{
                'product_id': linea.servicio_id.id,
                'partner_id': linea.transportista_id.id,
                'origen': linea.order_id.name,
                'name': linea.servicio_id.name,
                'product_qty':  linea.cantidad_transportada or 1,
                'precio_unitario': linea.transportista_precio_unitario,
                'tax_id': linea.tarifa_linea_id.tax_id.id,
                'valor_sin_igv': linea.valor_sin_igv,

            }))
        return purchase_line_ids

    purchase_line_ids = fields.Many2many('logistica.purchase.line', 'marcar_hecho_mrp_production',
                                         default=_get_default_purchase_line)



class LogisticaPurchaseLineWizard(models.TransientModel):
    _name = 'logistica.purchase.line'

    product_id = fields.Many2one('product.product', u'Producto o Servicio')
    partner_id = fields.Many2one('res.partner', u'Proveedor')
    name = fields.Char(u'Descripción')
    product_qty = fields.Float('Cantidad', digits=dp.get_precision('Product Unit of Measure'))
    precio_unitario = fields.Float('Precio unit.')
    tax_id = fields.Many2one('account.tax','Impuesto')
    valor_sin_igv = fields.Float('Valor sin IGV', digits=dp.get_precision('Account'))
    origen = fields.Char(u'Orígen')