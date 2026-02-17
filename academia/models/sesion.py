# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class Sesion(models.Model):
    """
    Modelo para gestionar las sesiones de clase.
    
    Una sesión representa una clase individual en una fecha y hora específica.
    
    Relaciones:
    - Many2one con Curso: Una sesión pertenece a UN curso
    - Many2one con Clase: Una sesión pertenece a UNA clase (opcional)
    - Many2one con Profesor: Una sesión tiene UN profesor
    - Many2many con Alumno: Una sesión tiene MUCHOS asistentes
    """
    _name = 'academia.sesion'
    _description = 'Sesión de Clase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, start_time'

    # === CAMPOS BÁSICOS ===
    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True
    )
    
    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    start_time = fields.Float(
        string='Hora Inicio',
        required=True,
        default=9.0,
        help='Hora en formato decimal (9.5 = 9:30)'
    )
    
    duration = fields.Float(
        string='Duración (horas)',
        required=True,
        default=1.5,
        help='Duración de la sesión en horas'
    )
    
    end_time = fields.Float(
        string='Hora Fin',
        compute='_compute_end_time',
        store=True
    )
    
    seats = fields.Integer(
        string='Número de Asientos',
        default=15,
        help='Capacidad máxima de la sesión'
    )
    
    seats_available = fields.Integer(
        string='Asientos Disponibles',
        compute='_compute_seats',
        store=True
    )
    
    seats_reserved = fields.Integer(
        string='Asientos Reservados',
        compute='_compute_seats',
        store=True
    )
    
    room = fields.Char(
        string='Aula'
    )
    
    topic = fields.Char(
        string='Tema',
        help='Tema específico a tratar en esta sesión'
    )
    
    notes = fields.Text(
        string='Notas'
    )
    
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('confirmed', 'Confirmada'),
            ('done', 'Realizada'),
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
    # Una sesión pertenece a UN curso
    curso_id = fields.Many2one(
        comodel_name='academia.curso',
        string='Curso',
        required=True,
        ondelete='cascade',  # Si se borra el curso, se borran sus sesiones
        tracking=True
    )
    
    # Una sesión puede pertenecer a UNA clase específica
    clase_id = fields.Many2one(
        comodel_name='academia.clase',
        string='Clase/Grupo',
        ondelete='set null',
        tracking=True,
        domain="[('curso_id', '=', curso_id)]",  # Filtrar clases del mismo curso
        help='Clase a la que pertenece esta sesión (opcional)'
    )
    
    # Una sesión tiene UN profesor
    profesor_id = fields.Many2one(
        comodel_name='academia.profesor',
        string='Profesor',
        required=True,
        ondelete='restrict',
        tracking=True
    )

    # === RELACIÓN MANY2MANY ===
    # Una sesión tiene MUCHOS asistentes (alumnos)
    alumno_ids = fields.Many2many(
        comodel_name='academia.alumno',
        relation='academia_alumno_sesion_rel',  # Misma tabla que en alumno.py
        column1='sesion_id',
        column2='alumno_id',
        string='Asistentes'
    )

    # === CAMPOS RELACIONADOS ===
    nivel = fields.Selection(
        related='curso_id.nivel',
        string='Nivel',
        store=True
    )
    
    profesor_name = fields.Char(
        related='profesor_id.display_name',
        string='Nombre Profesor'
    )

    # === CAMPOS CALCULADOS ===
    total_asistentes = fields.Integer(
        string='Total Asistentes',
        compute='_compute_seats',
        store=True
    )
    
    # Porcentaje de ocupación
    occupancy_rate = fields.Float(
        string='% Ocupación',
        compute='_compute_seats',
        store=True
    )
    
    # Campo para indicar si la sesión está llena
    is_full = fields.Boolean(
        string='Sesión Llena',
        compute='_compute_seats',
        store=True,
        help='Indica si la sesión ha alcanzado su capacidad máxima'
    )
    
    # Color para la vista (cambia según ocupación)
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=True
    )

    # === MÉTODOS COMPUTE ===
    @api.depends('curso_id', 'date', 'clase_id')
    def _compute_name(self):
        """Genera el nombre automáticamente."""
        for sesion in self:
            parts = []
            if sesion.curso_id:
                parts.append(sesion.curso_id.name)
            if sesion.clase_id:
                parts.append(f"[{sesion.clase_id.code}]")
            if sesion.date:
                parts.append(str(sesion.date))
            sesion.name = ' - '.join(parts) if parts else 'Nueva Sesión'

    @api.depends('start_time', 'duration')
    def _compute_end_time(self):
        """Calcula la hora de finalización."""
        for sesion in self:
            sesion.end_time = sesion.start_time + sesion.duration

    @api.depends('seats', 'alumno_ids')
    def _compute_seats(self):
        """Calcula estadísticas de asientos."""
        for sesion in self:
            sesion.total_asistentes = len(sesion.alumno_ids)
            sesion.seats_reserved = sesion.total_asistentes
            sesion.seats_available = sesion.seats - sesion.total_asistentes
            if sesion.seats > 0:
                sesion.occupancy_rate = (sesion.total_asistentes / sesion.seats) * 100
            else:
                sesion.occupancy_rate = 0
            # Determinar si está llena
            sesion.is_full = sesion.seats_available <= 0

    @api.depends('occupancy_rate', 'is_full', 'state')
    def _compute_color(self):
        """
        Calcula el color de la sesión según su estado y ocupación.
        Colores:
        - 1 (rojo): Sesión llena o cancelada
        - 2 (naranja): Ocupación >= 80%
        - 3 (amarillo): Ocupación >= 50%
        - 4 (azul claro): Ocupación < 50%
        - 10 (verde): Sesión realizada
        """
        for sesion in self:
            if sesion.state == 'cancelled':
                sesion.color = 1  # Rojo
            elif sesion.state == 'done':
                sesion.color = 10  # Verde
            elif sesion.is_full:
                sesion.color = 1  # Rojo - Llena
            elif sesion.occupancy_rate >= 80:
                sesion.color = 2  # Naranja
            elif sesion.occupancy_rate >= 50:
                sesion.color = 3  # Amarillo
            else:
                sesion.color = 4  # Azul claro

    # === ONCHANGE ===
    @api.onchange('clase_id')
    def _onchange_clase_id(self):
        """Al seleccionar una clase, hereda algunos valores."""
        if self.clase_id:
            self.profesor_id = self.clase_id.profesor_id
            self.room = self.clase_id.room
            self.seats = self.clase_id.max_students

    # === RESTRICCIONES ===
    _sql_constraints = [
        ('duration_positive', 'CHECK(duration > 0)', 
         'La duración debe ser mayor que 0.'),
        ('seats_positive', 'CHECK(seats >= 0)', 
         'El número de asientos no puede ser negativo.'),
    ]

    @api.constrains('alumno_ids', 'seats')
    def _check_seats(self):
        """Valida que no se supere la capacidad."""
        for sesion in self:
            if len(sesion.alumno_ids) > sesion.seats:
                raise ValidationError(
                    f'La sesión solo tiene {sesion.seats} asientos disponibles.'
                )

    @api.constrains('date')
    def _check_date(self):
        """Valida la fecha de la sesión."""
        for sesion in self:
            if sesion.state == 'done' and sesion.date > fields.Date.today():
                raise ValidationError(
                    'No se puede marcar como realizada una sesión con fecha futura.'
                )

    @api.constrains('profesor_id', 'date', 'start_time', 'end_time')
    def _check_profesor_schedule(self):
        """
        Valida que un profesor no tenga dos sesiones a la misma hora.
        No se permite solapamiento de horarios.
        """
        for sesion in self:
            if not sesion.profesor_id or not sesion.date:
                continue
            
            # Buscar otras sesiones del mismo profesor en la misma fecha
            domain = [
                ('id', '!=', sesion.id),
                ('profesor_id', '=', sesion.profesor_id.id),
                ('date', '=', sesion.date),
                ('state', '!=', 'cancelled'),  # Ignorar sesiones canceladas
            ]
            
            conflicting_sessions = self.search(domain)
            
            for other in conflicting_sessions:
                # Verificar solapamiento de horarios
                # Hay solapamiento si: start1 < end2 AND end1 > start2
                if (sesion.start_time < other.end_time and 
                    sesion.end_time > other.start_time):
                    raise ValidationError(
                        f'El profesor {sesion.profesor_id.display_name} ya tiene una sesión '
                        f'programada de {self._format_time(other.start_time)} a '
                        f'{self._format_time(other.end_time)} el día {sesion.date}.\n\n'
                        f'No se puede programar otra sesión que se solape con ese horario.'
                    )

    def _format_time(self, float_time):
        """Convierte hora en formato float a HH:MM."""
        hours = int(float_time)
        minutes = int((float_time - hours) * 60)
        return f'{hours:02d}:{minutes:02d}'

    # === MÉTODOS DE ACCIÓN ===
    def action_confirm(self):
        """Confirma la sesión."""
        self.write({'state': 'confirmed'})
    
    def action_done(self):
        """Marca la sesión como realizada."""
        self.write({'state': 'done'})
    
    def action_cancel(self):
        """Cancela la sesión."""
        self.write({'state': 'cancelled'})
    
    def action_draft(self):
        """Vuelve a borrador."""
        self.write({'state': 'draft'})
