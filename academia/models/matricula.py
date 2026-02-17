# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class Matricula(models.Model):
    """
    Modelo para gestionar las matrículas de alumnos.
    
    Flujo de estados: Borrador -> Confirmada -> Pagada
    
    Relaciones:
    - Many2one con Alumno: Una matrícula pertenece a UN alumno
    - Many2one con Curso: Una matrícula es para UN curso
    - Many2one con Clase: Una matrícula puede ser para UNA clase específica
    """
    _name = 'academia.matricula'
    _description = 'Matrícula de Alumno'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_matricula desc, id desc'
    _rec_name = 'name'

    # === CAMPOS BÁSICOS ===
    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo'
    )
    
    fecha_matricula = fields.Date(
        string='Fecha de Matrícula',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    fecha_inicio = fields.Date(
        string='Fecha de Inicio',
        required=True,
        tracking=True
    )
    
    fecha_fin = fields.Date(
        string='Fecha de Fin',
        tracking=True
    )
    
    # === FLUJO DE ESTADOS ===
    # Borrador -> Confirmada -> Pagada
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('confirmed', 'Confirmada'),
            ('paid', 'Pagada'),
            ('cancelled', 'Cancelada'),
        ],
        string='Estado',
        default='draft',
        required=True,
        tracking=True,
        help='Estado de la matrícula:\n'
             '- Borrador: Matrícula en proceso de creación\n'
             '- Confirmada: Matrícula validada, pendiente de pago\n'
             '- Pagada: Matrícula completamente pagada\n'
             '- Cancelada: Matrícula anulada'
    )
    
    # === IMPORTES ===
    importe_curso = fields.Float(
        string='Importe del Curso',
        compute='_compute_importe_curso',
        store=True,
        help='Precio del curso seleccionado'
    )
    
    descuento = fields.Float(
        string='Descuento (%)',
        default=0.0,
        tracking=True
    )
    
    importe_matricula = fields.Float(
        string='Importe Matrícula',
        default=50.0,
        tracking=True
    )
    
    importe_total = fields.Float(
        string='Importe Total',
        compute='_compute_importe_total',
        store=True
    )
    
    importe_pagado = fields.Float(
        string='Importe Pagado',
        default=0.0,
        tracking=True
    )
    
    importe_pendiente = fields.Float(
        string='Importe Pendiente',
        compute='_compute_importe_pendiente',
        store=True
    )
    
    # === RELACIONES ===
    alumno_id = fields.Many2one(
        comodel_name='academia.alumno',
        string='Alumno',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    curso_id = fields.Many2one(
        comodel_name='academia.curso',
        string='Curso',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    
    clase_id = fields.Many2one(
        comodel_name='academia.clase',
        string='Clase/Grupo',
        ondelete='set null',
        tracking=True,
        domain="[('curso_id', '=', curso_id)]"
    )
    
    # Factura generada
    factura_id = fields.Many2one(
        comodel_name='academia.facturacion',
        string='Factura',
        readonly=True,
        copy=False
    )
    
    # === CAMPOS INFORMATIVOS ===
    notes = fields.Text(
        string='Notas'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    # === CAMPOS COMPUTADOS ===
    @api.depends('curso_id', 'curso_id.price')
    def _compute_importe_curso(self):
        """Obtiene el precio del curso seleccionado."""
        for record in self:
            record.importe_curso = record.curso_id.price if record.curso_id else 0.0

    @api.depends('importe_curso', 'descuento', 'importe_matricula')
    def _compute_importe_total(self):
        """Calcula el importe total de la matrícula."""
        for record in self:
            descuento_aplicado = record.importe_curso * (record.descuento / 100)
            record.importe_total = (record.importe_curso - descuento_aplicado) + record.importe_matricula

    @api.depends('importe_total', 'importe_pagado')
    def _compute_importe_pendiente(self):
        """Calcula el importe pendiente de pago."""
        for record in self:
            record.importe_pendiente = record.importe_total - record.importe_pagado

    # === MÉTODOS DE MODELO ===
    @api.model_create_multi
    def create(self, vals_list):
        """Genera secuencia automática al crear."""
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('academia.matricula') or 'Nuevo'
        return super().create(vals_list)

    # === VALIDACIONES ===
    _sql_constraints = [
        ('descuento_range', 'CHECK(descuento >= 0 AND descuento <= 100)',
         'El descuento debe estar entre 0 y 100%.'),
        ('importe_matricula_positive', 'CHECK(importe_matricula >= 0)',
         'El importe de matrícula no puede ser negativo.'),
        ('unique_alumno_curso', 'UNIQUE(alumno_id, curso_id, fecha_inicio)',
         'Ya existe una matrícula para este alumno en este curso con la misma fecha de inicio.'),
    ]

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        """Valida que la fecha de fin sea posterior a la de inicio."""
        for record in self:
            if record.fecha_fin and record.fecha_inicio:
                if record.fecha_fin < record.fecha_inicio:
                    raise ValidationError(
                        'La fecha de fin debe ser posterior a la fecha de inicio.'
                    )

    @api.constrains('importe_pagado', 'importe_total')
    def _check_importe_pagado(self):
        """Valida que el importe pagado no supere el total."""
        for record in self:
            if record.importe_pagado > record.importe_total:
                raise ValidationError(
                    'El importe pagado no puede superar el importe total.'
                )

    # === ACCIONES DE FLUJO ===
    def action_confirm(self):
        """
        Confirma la matrícula.
        Transición: Borrador -> Confirmada
        """
        for record in self:
            if record.state != 'draft':
                raise ValidationError('Solo se pueden confirmar matrículas en borrador.')
            
            # Inscribir alumno en la clase si existe
            if record.clase_id and record.alumno_id:
                record.alumno_id.clase_ids = [(4, record.clase_id.id)]
            
            record.state = 'confirmed'

    def action_pay(self):
        """
        Marca la matrícula como pagada.
        Transición: Confirmada -> Pagada
        Genera factura automáticamente.
        """
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError('Solo se pueden pagar matrículas confirmadas.')
            
            # Marcar importe como pagado completo
            record.importe_pagado = record.importe_total
            
            # Crear factura
            factura = self.env['academia.facturacion'].create({
                'alumno_id': record.alumno_id.id,
                'curso_id': record.curso_id.id,
                'concept': f'Matrícula {record.name} - {record.curso_id.name}',
                'amount': record.importe_total,
                'state': 'paid',
            })
            record.factura_id = factura.id
            
            # Actualizar estado del alumno a matriculado
            if record.alumno_id.state == 'draft':
                record.alumno_id.state = 'enrolled'
            
            record.state = 'paid'

    def action_cancel(self):
        """
        Cancela la matrícula.
        """
        for record in self:
            if record.state == 'paid':
                raise ValidationError(
                    'No se puede cancelar una matrícula ya pagada. '
                    'Debe crear una nota de crédito.'
                )
            record.state = 'cancelled'

    def action_draft(self):
        """
        Vuelve la matrícula a borrador.
        """
        for record in self:
            if record.state not in ['confirmed', 'cancelled']:
                raise ValidationError(
                    'Solo se pueden volver a borrador matrículas confirmadas o canceladas.'
                )
            record.state = 'draft'
