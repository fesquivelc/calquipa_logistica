# coding=utf-8
from openerp import fields, models, api, _
import logging

from openerp.exceptions import ValidationError


class StockPickingTransporte(models.Model):
    _inherit = 'stock.move'

    purchase_id = fields.Many2one('purchase.order')