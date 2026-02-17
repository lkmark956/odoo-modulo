# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class Facturacion(models.Model):
    """
    Modelo para gestionar la facturación de la academia.
    
    Relaciones:
    - Many2one con Alumno: Una factura pertenece a UN alumno
    - Many2one con Curso: Una factura puede estar asociada a UN curso
    - Many2one con Clase: Una factura puede estar asociada a UNA clase
    """
    _name = 'academia.facturacion'
    _description = 'Facturación de la Academia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'
    _rec_name = 'name'

    # === CAMPOS BÁSICOS ===
    name = fields.Char(
        string='Número de Factura',
        required=True,
        copy=False,  # No se copia al duplicar
        readonly=True,
        default='Nuevo'
    )
    
    date = fields.Date(
        string='Fecha de Factura',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    due_date = fields.Date(
        string='Fecha de Vencimiento',
        tracking=True,
        help='Fecha límite de pago'
    )
    
    payment_date = fields.Date(
        string='Fecha de Pago',
        tracking=True,
        help='Fecha en que se realizó el pago'
    )
    
    amount = fields.Float(
        string='Cantidad',
        digits='Product Price',
        required=True,
        tracking=True
    )
    
    concept = fields.Char(
        string='Concepto',
        required=True,
        tracking=True,
        help='Descripción del concepto facturado'
    )
    
    description = fields.Text(
        string='Descripción Detallada'
    )
    
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Efectivo'),
            ('card', 'Tarjeta'),
            ('transfer', 'Transferencia'),
            ('domiciliation', 'Domiciliación'),
            ('other', 'Otro'),
        ],
        string='Método de Pago',
        default='transfer'
    )
    
    invoice_type = fields.Selection(
        selection=[
            ('enrollment', 'Matrícula'),
            ('monthly', 'Mensualidad'),
            ('materials', 'Materiales'),
            ('exam', 'Examen'),
            ('certificate', 'Certificado'),
            ('other', 'Otros'),
        ],
        string='Tipo de Factura',
        default='monthly',
        required=True
    )
    
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('pending', 'Pendiente'),
            ('paid', 'Pagada'),
            ('overdue', 'Vencida'),
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
    
    notes = fields.Text(
        string='Notas'
    )

    # === RELACIÓN MANY2ONE ===
    # Una factura pertenece a UN alumno
    alumno_id = fields.Many2one(
        comodel_name='academia.alumno',
        string='Alumno',
        required=True,
        ondelete='restrict',  # No permite borrar alumno con facturas
        tracking=True
    )
    
    # Una factura puede estar asociada a UN curso
    curso_id = fields.Many2one(
        comodel_name='academia.curso',
        string='Curso',
        ondelete='set null',
        tracking=True
    )
    
    # Una factura puede estar asociada a UNA clase
    clase_id = fields.Many2one(
        comodel_name='academia.clase',
        string='Clase',
        ondelete='set null',
        domain="[('curso_id', '=', curso_id)]"
    )

    # === CAMPOS RELACIONADOS ===
    alumno_email = fields.Char(
        related='alumno_id.email',
        string='Email Alumno'
    )
    
    alumno_phone = fields.Char(
        related='alumno_id.phone',
        string='Teléfono Alumno'
    )
    
    curso_name = fields.Char(
        related='curso_id.name',
        string='Nombre Curso'
    )

    # === CAMPOS CALCULADOS ===
    is_overdue = fields.Boolean(
        string='Está Vencida',
        compute='_compute_is_overdue',
        store=True
    )
    
    days_overdue = fields.Integer(
        string='Días de Retraso',
        compute='_compute_is_overdue',
        store=True
    )

    # === MÉTODOS COMPUTE ===
    @api.depends('due_date', 'state')
    def _compute_is_overdue(self):
        """Calcula si la factura está vencida."""
        today = date.today()
        for factura in self:
            if factura.state == 'pending' and factura.due_date:
                factura.is_overdue = factura.due_date < today
                if factura.is_overdue:
                    factura.days_overdue = (today - factura.due_date).days
                else:
                    factura.days_overdue = 0
            else:
                factura.is_overdue = False
                factura.days_overdue = 0

    # === MÉTODOS CREATE/WRITE ===
    @api.model_create_multi
    def create(self, vals_list):
        """Genera número de factura automáticamente."""
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                # Genera secuencia: FAC/2026/00001
                vals['name'] = self.env['ir.sequence'].next_by_code('academia.facturacion') or 'Nuevo'
        return super().create(vals_list)

    # === ONCHANGE ===
    @api.onchange('curso_id')
    def _onchange_curso_id(self):
        """Al seleccionar curso, sugiere el precio como cantidad."""
        if self.curso_id:
            self.amount = self.curso_id.price
            if not self.concept:
                self.concept = f"Curso: {self.curso_id.name}"
    
    @api.onchange('invoice_type')
    def _onchange_invoice_type(self):
        """Sugiere concepto según tipo de factura."""
        type_concepts = {
            'enrollment': 'Matrícula',
            'monthly': 'Mensualidad',
            'materials': 'Material didáctico',
            'exam': 'Tasa de examen',
            'certificate': 'Emisión de certificado',
        }
        if self.invoice_type and not self.concept:
            self.concept = type_concepts.get(self.invoice_type, '')

    # === RESTRICCIONES ===
    _sql_constraints = [
        ('amount_positive', 'CHECK(amount >= 0)', 'La cantidad debe ser positiva.'),
        ('name_unique', 'UNIQUE(name)', 'El número de factura debe ser único.'),
    ]

    @api.constrains('payment_date', 'date')
    def _check_payment_date(self):
        """Valida que la fecha de pago no sea anterior a la de factura."""
        for factura in self:
            if factura.payment_date and factura.payment_date < factura.date:
                raise ValidationError(
                    'La fecha de pago no puede ser anterior a la fecha de factura.'
                )

    # === MÉTODOS DE ACCIÓN ===
    def action_confirm(self):
        """Confirma la factura (pasa a pendiente)."""
        self.write({'state': 'pending'})
    
    def action_pay(self):
        """Marca la factura como pagada."""
        self.write({
            'state': 'paid',
            'payment_date': fields.Date.today()
        })
    
    def action_cancel(self):
        """Cancela la factura."""
        self.write({'state': 'cancelled'})
    
    def action_draft(self):
        """Vuelve a borrador."""
        self.write({'state': 'draft', 'payment_date': False})
    
    def action_check_overdue(self):
        """Acción programada para marcar facturas vencidas."""
        today = date.today()
        overdue_invoices = self.search([
            ('state', '=', 'pending'),
            ('due_date', '<', today)
        ])
        overdue_invoices.write({'state': 'overdue'})
