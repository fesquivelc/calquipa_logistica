from openerp import fields, models


class TipoTransporte(models.Model):
    _name = 'logistica.transporte.tipo'

    name = fields.Char(u'Tipo de transporte')
