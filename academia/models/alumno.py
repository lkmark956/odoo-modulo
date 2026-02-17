# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class Alumno(models.Model):
    """
    Modelo para gestionar los alumnos de la academia.
    
    Relaciones:
    - Many2many con Clase: Un alumno puede estar en múltiples clases
    - Many2many con Sesion: Un alumno puede asistir a múltiples sesiones
    - One2many con Facturacion: Un alumno puede tener múltiples facturas
    """
    _name = 'academia.alumno'
    _description = 'Alumno de la Academia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'apellidos, name'

    # === CAMPOS BÁSICOS ===
    name = fields.Char(
        string='Nombre',
        required=True,
        tracking=True
    )
    
    apellidos = fields.Char(
        string='Apellidos',
        required=True,
        tracking=True
    )
    
    # Nombre completo calculado
    display_name = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name',
        store=True
    )
    
    email = fields.Char(
        string='Email',
        required=True,
        tracking=True
    )
    
    phone = fields.Char(
        string='Teléfono'
    )
    
    birthdate = fields.Date(
        string='Fecha de Nacimiento'
    )
    
    age = fields.Integer(
        string='Edad',
        compute='_compute_age',
        store=True
    )
    
    dni = fields.Char(
        string='DNI/NIE',
        help='Documento Nacional de Identidad'
    )
    
    address = fields.Text(
        string='Dirección'
    )
    
    enrollment_date = fields.Date(
        string='Fecha de Inscripción',
        default=fields.Date.today,
        tracking=True
    )
    
    state = fields.Selection(
        selection=[
            ('draft', 'Preinscrito'),
            ('enrolled', 'Matriculado'),
            ('active', 'Activo'),
            ('suspended', 'Suspendido'),
            ('completed', 'Finalizado'),
        ],
        string='Estado',
        default='draft',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    image = fields.Image(
        string='Foto',
        max_width=256,
        max_height=256
    )
    
    notes = fields.Text(
        string='Notas Internas'
    )

    # === RELACIÓN MANY2MANY ===
    # Un alumno puede estar en MUCHAS clases
    clase_ids = fields.Many2many(
        comodel_name='academia.clase',
        relation='academia_alumno_clase_rel',  # Tabla intermedia
        column1='alumno_id',
        column2='clase_id',
        string='Clases Inscritas'
    )
    
    # Un alumno puede asistir a MUCHAS sesiones
    sesion_ids = fields.Many2many(
        comodel_name='academia.sesion',
        relation='academia_alumno_sesion_rel',
        column1='alumno_id',
        column2='sesion_id',
        string='Sesiones'
    )

    # === RELACIÓN ONE2MANY (inversa) ===
    # Un alumno puede tener MUCHAS facturas
    factura_ids = fields.One2many(
        comodel_name='academia.facturacion',
        inverse_name='alumno_id',
        string='Facturas'
    )
    
    # Campos calculados
    total_facturas = fields.Integer(
        string='Total Facturas',
        compute='_compute_facturacion'
    )
    
    saldo_pendiente = fields.Float(
        string='Saldo Pendiente',
        compute='_compute_facturacion',
        help='Total de facturas pendientes de pago'
    )

    # === MÉTODOS COMPUTE ===
    @api.depends('name', 'apellidos')
    def _compute_display_name(self):
        """Calcula el nombre completo."""
        for alumno in self:
            if alumno.name and alumno.apellidos:
                alumno.display_name = f"{alumno.apellidos}, {alumno.name}"
            else:
                alumno.display_name = alumno.name or ''

    @api.depends('birthdate')
    def _compute_age(self):
        """Calcula la edad basándose en la fecha de nacimiento."""
        today = date.today()
        for alumno in self:
            if alumno.birthdate:
                edad = today.year - alumno.birthdate.year
                # Ajustar si aún no ha cumplido años este año
                if (today.month, today.day) < (alumno.birthdate.month, alumno.birthdate.day):
                    edad -= 1
                alumno.age = edad
            else:
                alumno.age = 0

    @api.depends('factura_ids', 'factura_ids.state', 'factura_ids.amount')
    def _compute_facturacion(self):
        """Calcula estadísticas de facturación."""
        for alumno in self:
            alumno.total_facturas = len(alumno.factura_ids)
            # Sumar facturas pendientes
            pendientes = alumno.factura_ids.filtered(lambda f: f.state == 'pending')
            alumno.saldo_pendiente = sum(pendientes.mapped('amount'))

    # === RESTRICCIONES ===
    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)', 'Ya existe un alumno con este email.'),
        ('dni_unique', 'UNIQUE(dni)', 'Ya existe un alumno con este DNI/NIE.'),
    ]

    @api.constrains('email')
    def _check_email(self):
        """Valida el formato del email."""
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError('El email debe contener @')

    @api.constrains('birthdate')
    def _check_birthdate(self):
        """Valida que la fecha de nacimiento sea pasada."""
        for record in self:
            if record.birthdate and record.birthdate > date.today():
                raise ValidationError('La fecha de nacimiento no puede ser futura.')

    # === MÉTODOS DE ACCIÓN ===
    def action_enroll(self):
        """Matricula al alumno."""
        self.write({'state': 'enrolled'})
    
    def action_activate(self):
        """Activa al alumno."""
        self.write({'state': 'active'})
