from openerp import fields, models, api


class DatosTransportista(models.Model):
    _inherit = 'res.partner'

    transportista = fields.Boolean('Realiza servicios de transporte')