# coding=utf-8
from openerp import fields, api, models

TIPO_RUTA = (
    ('n', 'Nacional'),
    ('i', 'Internacional')
)


class Rutas(models.Model):
    _name = 'logistica.ruta'

    origen = fields.Char(u'Orígen')
    destino = fields.Char(u'Destino')
    tipo_ruta = fields.Selection(TIPO_RUTA, 'Tipo de ruta')

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['origen', 'destino'], context=context)
        res = []
        for record in reads:
            origen = record['origen']
            destino = record['destino']
            res.append((record['id'], '%s-%s' % (origen, destino)))
        return res

    _sql_constraints = [
        ('ruta_unique', 'UNIQUE(LOWER(origen),LOWER(destino))',
         u'No puede haber mas de una ruta con el mismo orígen y destino')
    ]
