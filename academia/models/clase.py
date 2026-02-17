# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Clase(models.Model):
    """
    Modelo para gestionar las clases/grupos de la academia.
    
    Una clase representa un grupo de alumnos con un horario específico.
    
    Relaciones:
    - Many2one con Curso: Una clase pertenece a UN curso
    - Many2one con Profesor: Una clase tiene UN profesor asignado
    - Many2many con Alumno: Una clase tiene MUCHOS alumnos
    - One2many con Sesion: Una clase tiene MUCHAS sesiones
    """
    _name = 'academia.clase'
    _description = 'Clase/Grupo de la Academia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'curso_id, name'

    # === CAMPOS BÁSICOS ===
    name = fields.Char(
        string='Nombre del Grupo',
        required=True,
        tracking=True,
        help='Ej: Inglés B1 - Mañanas, Francés A2 - Tardes'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        help='Código único de la clase. Ej: ING-B1-M01'
    )
    
    # Horario
    schedule = fields.Selection(
        selection=[
            ('morning', 'Mañana (9:00 - 14:00)'),
            ('afternoon', 'Tarde (15:00 - 20:00)'),
            ('evening', 'Noche (20:00 - 22:00)'),
            ('weekend', 'Fin de Semana'),
        ],
        string='Horario',
        required=True,
        default='morning'
    )
    
    # Días de la semana (campo de selección múltiple simulado)
    monday = fields.Boolean(string='Lunes', default=True)
    tuesday = fields.Boolean(string='Martes')
    wednesday = fields.Boolean(string='Miércoles', default=True)
    thursday = fields.Boolean(string='Jueves')
    friday = fields.Boolean(string='Viernes', default=True)
    saturday = fields.Boolean(string='Sábado')
    sunday = fields.Boolean(string='Domingo')
    
    start_time = fields.Float(
        string='Hora Inicio',
        default=9.0,
        help='Hora de inicio en formato decimal (9.5 = 9:30)'
    )
    
    end_time = fields.Float(
        string='Hora Fin',
        default=11.0
    )
    
    start_date = fields.Date(
        string='Fecha Inicio',
        required=True,
        default=fields.Date.today
    )
    
    end_date = fields.Date(
        string='Fecha Fin'
    )
    
    max_students = fields.Integer(
        string='Capacidad Máxima',
        default=15,
        help='Número máximo de alumnos permitidos'
    )
    
    room = fields.Char(
        string='Aula',
        help='Aula o sala donde se imparte la clase'
    )
    
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('confirmed', 'Confirmada'),
            ('in_progress', 'En Curso'),
            ('done', 'Finalizada'),
            ('cancelled', 'Cancelada'),
        ],
        string='Estado',
        default='draft',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    # === RELACIÓN MANY2ONE ===
    # Una clase pertenece a UN curso
    curso_id = fields.Many2one(
        comodel_name='academia.curso',
        string='Curso',
        required=True,
        ondelete='restrict',  # No permite borrar el curso si tiene clases
        tracking=True,
        help='Curso al que pertenece esta clase'
    )
    
    # Una clase tiene UN profesor asignado
    profesor_id = fields.Many2one(
        comodel_name='academia.profesor',
        string='Profesor',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Profesor que imparte esta clase'
    )

    # === RELACIÓN MANY2MANY ===
    # Una clase tiene MUCHOS alumnos
    alumno_ids = fields.Many2many(
        comodel_name='academia.alumno',
        relation='academia_alumno_clase_rel',  # Misma tabla que en alumno.py
        column1='clase_id',
        column2='alumno_id',
        string='Alumnos Inscritos'
    )

    # === RELACIÓN ONE2MANY ===
    # Una clase tiene MUCHAS sesiones
    sesion_ids = fields.One2many(
        comodel_name='academia.sesion',
        inverse_name='clase_id',
        string='Sesiones'
    )

    # === CAMPOS CALCULADOS ===
    # Campos relacionados (obtienen valor del modelo relacionado)
    nivel = fields.Selection(
        related='curso_id.nivel',
        string='Nivel',
        store=True,
        help='Nivel del curso (heredado)'
    )
    
    precio_curso = fields.Float(
        related='curso_id.price',
        string='Precio del Curso'
    )
    
    total_alumnos = fields.Integer(
        string='Total Alumnos',
        compute='_compute_totals',
        store=True
    )
    
    plazas_disponibles = fields.Integer(
        string='Plazas Disponibles',
        compute='_compute_totals',
        store=True
    )
    
    total_sesiones = fields.Integer(
        string='Total Sesiones',
        compute='_compute_totals',
        store=True
    )
    
    # Mostrar días como texto
    dias_semana = fields.Char(
        string='Días',
        compute='_compute_dias_semana'
    )

    # === MÉTODOS COMPUTE ===
    @api.depends('alumno_ids', 'max_students', 'sesion_ids')
    def _compute_totals(self):
        """Calcula totales de alumnos y plazas."""
        for clase in self:
            clase.total_alumnos = len(clase.alumno_ids)
            clase.plazas_disponibles = clase.max_students - clase.total_alumnos
            clase.total_sesiones = len(clase.sesion_ids)

    @api.depends('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    def _compute_dias_semana(self):
        """Genera texto con los días de clase."""
        dias_map = {
            'monday': 'L',
            'tuesday': 'M',
            'wednesday': 'X',
            'thursday': 'J',
            'friday': 'V',
            'saturday': 'S',
            'sunday': 'D',
        }
        for clase in self:
            dias = []
            for field, letra in dias_map.items():
                if getattr(clase, field):
                    dias.append(letra)
            clase.dias_semana = '-'.join(dias) if dias else ''

    # === RESTRICCIONES ===
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Ya existe una clase con este código.'),
        ('max_students_positive', 'CHECK(max_students > 0)', 
         'La capacidad máxima debe ser mayor que 0.'),
    ]

    @api.constrains('alumno_ids', 'max_students')
    def _check_capacidad(self):
        """Valida que no se supere la capacidad máxima."""
        for clase in self:
            if len(clase.alumno_ids) > clase.max_students:
                raise ValidationError(
                    f'La clase {clase.name} ha superado su capacidad máxima '
                    f'({clase.max_students} alumnos).'
                )

    @api.constrains('start_date', 'end_date')
    def _check_fechas(self):
        """Valida que la fecha fin sea posterior a la de inicio."""
        for clase in self:
            if clase.end_date and clase.start_date > clase.end_date:
                raise ValidationError('La fecha de fin debe ser posterior a la de inicio.')

    @api.constrains('start_time', 'end_time')
    def _check_horario(self):
        """Valida el horario."""
        for clase in self:
            if clase.end_time <= clase.start_time:
                raise ValidationError('La hora de fin debe ser posterior a la de inicio.')

    # === MÉTODOS DE ACCIÓN ===
    def action_confirm(self):
        """Confirma la clase."""
        self.write({'state': 'confirmed'})
    
    def action_start(self):
        """Inicia la clase."""
        self.write({'state': 'in_progress'})
    
    def action_done(self):
        """Finaliza la clase."""
        self.write({'state': 'done'})
    
    def action_cancel(self):
        """Cancela la clase."""
        self.write({'state': 'cancelled'})

    def action_view_sesiones(self):
        """Abre la vista de sesiones filtradas por esta clase."""
        self.ensure_one()
        return {
            'name': f'Sesiones de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'academia.sesion',
            'view_mode': 'list,form,calendar',
            'domain': [('clase_id', '=', self.id)],
            'context': {'default_clase_id': self.id, 'default_curso_id': self.curso_id.id},
        }
