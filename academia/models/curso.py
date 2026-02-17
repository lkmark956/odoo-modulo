# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Curso(models.Model):
    """
    Modelo para gestionar los cursos de la academia.
    
    Campos principales:
    - name: Título del curso
    - description: Descripción detallada
    - nivel: Nivel según el Marco Común Europeo (A1-C2)
    - price: Precio del curso
    
    Relaciones:
    - One2many con Sesion: Un curso tiene múltiples sesiones
    - One2many con Clase: Un curso tiene múltiples clases/grupos
    """
    _name = 'academia.curso'
    _description = 'Curso de la Academia'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Añade chatter y actividades
    _order = 'nivel, name'  # Ordenar por nivel y nombre

    # === CAMPOS BÁSICOS ===
    name = fields.Char(
        string='Título del Curso',
        required=True,
        tracking=True,  # Registra cambios en el chatter
        help='Nombre descriptivo del curso'
    )
    
    description = fields.Html(
        string='Descripción',
        help='Descripción detallada del contenido del curso'
    )
    
    nivel = fields.Selection(
        selection=[
            ('a1', 'A1 - Principiante'),
            ('a2', 'A2 - Elemental'),
            ('b1', 'B1 - Intermedio'),
            ('b2', 'B2 - Intermedio Alto'),
            ('c1', 'C1 - Avanzado'),
            ('c2', 'C2 - Maestría'),
        ],
        string='Nivel',
        required=True,
        default='a1',
        tracking=True,
        help='Nivel según el Marco Común Europeo de Referencia'
    )
    
    price = fields.Float(
        string='Precio',
        digits='Product Price',  # Usa la precisión decimal de productos
        required=True,
        tracking=True,
        help='Precio del curso en euros'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, el curso se archiva y no aparece en las búsquedas'
    )
    
    # === CAMPOS RELACIONALES (One2many - relación inversa) ===
    # Un curso puede tener MUCHAS sesiones
    sesion_ids = fields.One2many(
        comodel_name='academia.sesion',
        inverse_name='curso_id',
        string='Sesiones',
        help='Sesiones programadas para este curso'
    )
    
    # Un curso puede tener MUCHAS clases/grupos
    clase_ids = fields.One2many(
        comodel_name='academia.clase',
        inverse_name='curso_id',
        string='Clases',
        help='Clases o grupos de este curso'
    )
    
    # === CAMPOS CALCULADOS ===
    total_sesiones = fields.Integer(
        string='Total Sesiones',
        compute='_compute_estadisticas',
        store=True,  # Guardar en BD para mejor rendimiento
        help='Número total de sesiones del curso'
    )
    
    total_alumnos = fields.Integer(
        string='Total Alumnos',
        compute='_compute_estadisticas',
        store=True,
        help='Número total de alumnos inscritos'
    )

    # === MÉTODOS COMPUTE ===
    @api.depends('sesion_ids', 'clase_ids.alumno_ids')
    def _compute_estadisticas(self):
        """Calcula estadísticas del curso."""
        for curso in self:
            curso.total_sesiones = len(curso.sesion_ids)
            # Obtener alumnos únicos de todas las clases
            alumnos = curso.clase_ids.mapped('alumno_ids')
            curso.total_alumnos = len(alumnos)

    # === RESTRICCIONES SQL ===
    _sql_constraints = [
        ('price_positive', 'CHECK(price >= 0)', 'El precio debe ser positivo o cero.'),
        ('name_unique', 'UNIQUE(name, nivel)', 'Ya existe un curso con este nombre y nivel.'),
    ]

    # === MÉTODOS DE VALIDACIÓN ===
    @api.constrains('price')
    def _check_price(self):
        """Valida que el precio no sea negativo."""
        for record in self:
            if record.price < 0:
                raise ValidationError('El precio del curso no puede ser negativo.')

    # === MÉTODOS DE ACCIÓN ===
    def action_view_sesiones(self):
        """Abre la vista de sesiones filtradas por este curso."""
        self.ensure_one()
        return {
            'name': f'Sesiones de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'academia.sesion',
            'view_mode': 'list,form,calendar',
            'domain': [('curso_id', '=', self.id)],
            'context': {'default_curso_id': self.id},
        }

    def action_view_clases(self):
        """Abre la vista de clases filtradas por este curso."""
        self.ensure_one()
        return {
            'name': f'Clases de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'academia.clase',
            'view_mode': 'list,form',
            'domain': [('curso_id', '=', self.id)],
            'context': {'default_curso_id': self.id},
        }
