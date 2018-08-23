# -*- coding: utf-8 -*-
import logging

from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)


class LogisticaPurchaseWizard(models.TransientModel):
    _name = 'logistica.purchase.wizard'

    def _get_default_mrp_order(self):
        logistica_pedidos = d
        return [(6, False, self._context.get('active_ids', []))]

    mrp_production_ids = fields.Many2many('mrp.production', 'marcar_hecho_mrp_production',
                                          default=_get_default_mrp_order)

    @api.multi
    def generar_pedido_compra(self):
        for wizard in self:
            for sale_order in wizard.mrp_production_ids:
                sale_order.button_mark_done()


class LogisticaPurchaseWizard(models.TransientModel):
    _name = 'logistica.purchase.wizard'
