# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Profesor(models.Model):
    """
    Modelo para gestionar los profesores de la academia.
    
    Relaciones:
    - Many2one con res.users: Relación ONE2ONE simulada (un profesor = un usuario)
    - One2many con Clase: Un profesor puede impartir múltiples clases
    - Many2many con Curso: Un profesor puede impartir múltiples cursos
    """
    _name = 'academia.profesor'
    _description = 'Profesor de la Academia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

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
    
    # Campo calculado para nombre completo
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
    
    titulacion = fields.Text(
        string='Titulación',
        required=True,
        help='Títulos y certificaciones del profesor'
    )
    
    specialization = fields.Selection(
        selection=[
            ('ingles', 'Inglés'),
            ('frances', 'Francés'),
            ('aleman', 'Alemán'),
            ('italiano', 'Italiano'),
            ('portugues', 'Portugués'),
            ('chino', 'Chino'),
            ('japones', 'Japonés'),
            ('otros', 'Otros'),
        ],
        string='Especialización',
        default='ingles'
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

    # === RELACIÓN ONE2ONE (simulada con Many2one + unique constraint) ===
    # Cada profesor puede estar vinculado a UN usuario del sistema
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Usuario del Sistema',
        ondelete='set null',  # Si se borra el usuario, el campo queda vacío
        help='Usuario de Odoo asociado a este profesor (relación 1:1)'
    )

    # === RELACIÓN MANY2MANY ===
    # Un profesor puede impartir MUCHOS cursos y un curso puede tener MUCHOS profesores
    curso_ids = fields.Many2many(
        comodel_name='academia.curso',
        relation='academia_profesor_curso_rel',  # Nombre de la tabla intermedia
        column1='profesor_id',  # Columna que referencia a este modelo
        column2='curso_id',  # Columna que referencia al otro modelo
        string='Cursos que Imparte',
        help='Cursos que este profesor está capacitado para impartir'
    )

    # === RELACIÓN ONE2MANY (inversa) ===
    # Un profesor puede tener MUCHAS clases asignadas
    clase_ids = fields.One2many(
        comodel_name='academia.clase',
        inverse_name='profesor_id',
        string='Clases Asignadas'
    )
    
    # Campo calculado: número de clases
    total_clases = fields.Integer(
        string='Total Clases',
        compute='_compute_total_clases',
        store=True
    )

    # === MÉTODOS COMPUTE ===
    @api.depends('name', 'apellidos')
    def _compute_display_name(self):
        """Calcula el nombre completo del profesor."""
        for profesor in self:
            if profesor.name and profesor.apellidos:
                profesor.display_name = f"{profesor.name} {profesor.apellidos}"
            else:
                profesor.display_name = profesor.name or ''
    
    @api.depends('clase_ids')
    def _compute_total_clases(self):
        """Cuenta el número de clases asignadas."""
        for profesor in self:
            profesor.total_clases = len(profesor.clase_ids)

    # === RESTRICCIONES ===
    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)', 'Ya existe un profesor con este email.'),
        # ONE2ONE: Un usuario solo puede ser un profesor
        ('user_unique', 'UNIQUE(user_id)', 'Este usuario ya está asignado a otro profesor.'),
    ]

    @api.constrains('email')
    def _check_email(self):
        """Valida el formato del email."""
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError('El email debe contener @')
