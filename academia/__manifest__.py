# -*- coding: utf-8 -*-
{
    'name': 'Academia de Idiomas',
    'version': '19.0.2.0.0',
    'category': 'Education',
    'summary': 'Gestión de cursos, alumnos y profesores para academia de idiomas',
    'description': """
        Módulo para la gestión integral de una academia de idiomas.
        
        Características:
        - Gestión de cursos por niveles (A1, A2, B1, B2, C1, C2)
        - Control de sesiones y horarios
        - Registro de alumnos y profesores
        - Facturación integrada
        - Gestión de clases y grupos
        
        Vistas Avanzadas (v2.0):
        - Vista Calendario para sesiones programadas
        - Vista Kanban para gestión visual de sesiones, clases y cursos
        - Filtros y agrupaciones avanzadas
        - Sección de Planificación con acceso rápido
    """,
    'author': 'Marco',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/curso_views.xml',
        'views/profesor_views.xml',
        'views/alumno_views.xml',
        'views/clase_views.xml',
        'views/sesion_views.xml',
        'views/facturacion_views.xml',
        'views/matricula_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
