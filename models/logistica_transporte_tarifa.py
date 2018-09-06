# coding=utf-8
from openerp import fields, models, api
import openerp.addons.decimal_precision as dp

from openerp.exceptions import ValidationError

TIPO_LINEA = (
    ('transportista', u'Transportista'),
    ('gasto_exportacion', u'Gastos de exportación')
)


class TarifaTransporte(models.Model):
    _name = 'logistica.transporte.tarifa'

    codigo = fields.Char(u'Código')
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
    direccion = fields.Char(u'Dirección', required=True)
    exportacion = fields.Boolean(u'Exportación')
    invoice_id = fields.Many2one('account.invoice', u'Documento de exportación')
    transporte_linea_ids = fields.One2many('logistica.transporte.tarifa.linea', 'transporte_tarifa_id',
                                           domain=[('tipo', '=', 'transportista')])
    exportacion_linea_ids = fields.One2many('logistica.transporte.tarifa.linea', 'transporte_tarifa_id',
                                            domain=[('tipo', '=', 'gasto_exportacion')])
    ruta_nacional_id = fields.Many2one('logistica.ruta', u'Ruta nacional')
    ruta_internacional_id = fields.Many2one('logistica.ruta', u'Ruta internacional')

    # TODO: Revisar la razon por la cual odoo no guarda automaticamente los compute_fields que estan como store=True
    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if vals.get('transporte_linea_ids', False) or vals.get('exportacion_linea_ids', False):
            lineas = []
            operaciones = []
            for (a, b, linea) in vals.get('transporte_linea_ids', []):
                lineas.append((0, 0, self.procesar_precios(linea)))
            for (a, b, linea) in vals.get('exportacion_linea_ids', []):
                linea.update({'ruta_id': vals.get('ruta_internacional_id', False)})
                operaciones.append((0, 0, self.procesar_precios(linea)))
            vals.update({
                'transporte_linea_ids': lineas,
                'exportacion_linea_ids': operaciones
            })

        return super(TarifaTransporte, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('transporte_linea_ids', False) or vals.get('exportacion_linea_ids', False):
            lineas = []
            operaciones = []
            for (a, b, linea) in vals.get('transporte_linea_ids', []):
                lineas.append((0, 0, self.procesar_precios(linea)))
            for (a, b, linea) in vals.get('exportacion_linea_ids', []):
                linea.update({'ruta_id': vals.get('ruta_internacional_id', False)})
                operaciones.append((0, 0, self.procesar_precios(linea)))
            vals.update({
                'transporte_linea_ids': lineas,
                'exportacion_linea_ids': operaciones
            })
        return super(TarifaTransporte, self).write(vals)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.direccion = self.partner_id.street

    @api.constrains('tarifa_linea_ids')
    def check_tarifa_line_ids(self):
        if len(self.transporte_linea_ids) == 0:
            raise ValidationError('Debe existir un detalle de tarifa por lo menos')

    @api.constrains('exportacion_linea_ids')
    def check_exportacion_linea_ids(self):
        if self.exportacion and not self.exportacion_linea_ids:
            raise ValidationError(u'Si ha marcado el check de exportación debe definir gastos de exp.')

    _sql_constraints = [
        ('codigo_uniq', 'unique(codigo)', u'El código ya es utilizado en otra tarifa'),
        ('invoice_id_uniq', 'unique(invoice_id)', u'Esta factura de exportacion ya se encuentra enlazada anteriormente'),
    ]

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['partner_id', 'exportacion'], context=context)
        res = []
        for record in reads:
            partner_id = record['partner_id']
            exportacion = record['exportacion']
            res.append((record['id'], u'TARIFA: %s ¿EXPORT.?: %s' % (partner_id[1], exportacion and 'si' or 'no')))
        return res

    def procesar_precios(self, linea):
        precio = linea['precio_unitario']
        tax_id = self.env['account.tax'].browse(linea['tax_id'])
        product_id = self.env['product.product'].browse(linea['product_id'])
        transportista_id = self.env['res.partner'].browse(linea['transportista_id'])
        currency_id = self.env['res.currency'].browse(linea['currency_id'])
        impuestos = tax_id.compute_all(precio, 1, product=product_id, partner=transportista_id)
        imponible = currency_id.round(impuestos['total'])
        igv = currency_id.round(impuestos['total_included'] - impuestos['total'])
        total_included = impuestos['total_included']
        subtotal = currency_id.round(total_included)

        linea.update({'imponible': imponible, 'igv': igv, 'subtotal': subtotal})
        return linea


class TarifaTransporteLinea(models.Model):
    _name = 'logistica.transporte.tarifa.linea'

    @api.one
    @api.depends('precio_unitario', 'tax_id', 'product_id', 'transportista_id', 'currency_id')
    def _compute_precio(self):
        precio = self.precio_unitario
        impuestos = self.tax_id.compute_all(precio, 1, product=self.product_id, partner=self.transportista_id)
        self.imponible = self.currency_id.round(impuestos['total'])
        self.igv = self.currency_id.round(impuestos['total_included'] - impuestos['total'])
        total_included = impuestos['total_included']
        self.subtotal = self.currency_id.round(total_included)

    def _get_product_id(self):
        product = self.env['product.product'].search([('default_code', '=', '2363')], limit=1)
        if product.exists():
            return product.id
        return False

    def _get_currency(self):
        currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if currency.exists():
            return currency.id
        return False

    tipo = fields.Selection(TIPO_LINEA)
    archivado = fields.Boolean('Archivado', default=False)
    transportista_id = fields.Many2one('res.partner', u'Proveedor', required=True)
    ruta_id = fields.Many2one('logistica.ruta', u'Ruta', required=True)
    transporte_tarifa_id = fields.Many2one('logistica.transporte.tarifa', u'Tarifa de transporte')
    transporte_tarifa_inv_id = fields.Many2one('account.invoice', related='transporte_tarifa_id.invoice_id')
    transporte_tarifa_partner_id = fields.Many2one('res.partner', related='transporte_tarifa_id.partner_id')
    transporte_tipo_id = fields.Many2one('logistica.transporte.tipo', u'Tipo de transporte')
    transporte_tarifa_exportacion = fields.Boolean(related='transporte_tarifa_id.exportacion')
    product_id = fields.Many2one('product.product', u'Servicio', default=_get_product_id)
    descripcion = fields.Char(u'Descripción')
    tax_id = fields.Many2one('account.tax', u'Impuesto')
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                  required=True, default=_get_currency)
    precio_unitario = fields.Float(string='Precio unit.', required=True,
                                   digits=dp.get_precision('Product Price'))

    imponible = fields.Float(string='Base imponible', required=True,
                             digits=dp.get_precision('Account'), store=True,
                             compute='_compute_precio')
    igv = fields.Float(string='Total impuesto', required=True,
                       digits=dp.get_precision('Account'), store=True, compute='_compute_precio')
    subtotal = fields.Float(string='Total', digits=dp.get_precision('Account'),
                            store=True, compute='_compute_precio')

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['transportista_id', 'ruta_id', 'subtotal'], context=context)
        res = []
        for record in reads:
            res.append((record['id'], 'TRANSP: %s - RUTA: %s - PRECIOxTON: %s' % (
                record['transportista_id'][1], record['ruta_id'][1], record['subtotal'])))
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.descripcion = self.product_id.name
        self.precio_unitario = self.precio_unitario or self.product_id.list_price
