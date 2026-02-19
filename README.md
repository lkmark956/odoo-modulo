# Academia de Idiomas - Módulo Odoo

Módulo para la gestión integral de una academia de idiomas en Odoo 19.

## Características

- **Gestión de Cursos**: Organización por niveles (A1, A2, B1, B2, C1, C2)
- **Control de Sesiones**: Programación de horarios y clases
- **Registro de Alumnos**: Gestión completa de estudiantes
- **Gestión de Profesores**: Control del personal docente
- **Facturación Integrada**: Sistema de facturación para matrículas
- **Gestión de Clases y Grupos**: Organización de grupos de estudio

## Cómo Funciona

### Estructura de Modelos

El módulo está compuesto por 6 modelos principales:

| Modelo | Descripción |
|--------|-------------|
| `academia.curso` | Cursos disponibles con niveles MCER (A1-C2) y precios |
| `academia.profesor` | Profesores con especialización por idioma |
| `academia.alumno` | Estudiantes con datos personales y edad calculada |
| `academia.clase` | Grupos de alumnos con horarios (mañana/tarde/noche) |
| `academia.sesion` | Clases individuales con fecha, hora y asistentes |
| `academia.matricula` | Inscripciones con flujo de estados |

### Flujo de Trabajo

1. **Crear Cursos**: Define cursos con nivel (A1-C2) y precio
2. **Registrar Profesores**: Añade profesores con su especialización (inglés, francés, alemán, etc.)
3. **Crear Clases/Grupos**: Asigna un curso y profesor a cada grupo con horario semanal
4. **Matricular Alumnos**: Crea matrículas (Borrador → Confirmada → Pagada)
5. **Programar Sesiones**: Agenda clases individuales con fecha, duración y asistentes

### Estados de Matrícula

```
Borrador → Confirmada → Pagada
    ↓
Cancelada
```

## Vistas Disponibles

- Vista Calendario para sesiones programadas
- Vista Kanban para gestión visual
- Filtros y agrupaciones avanzadas

## Instalación

1. Copiar el módulo en la carpeta `addons` de Odoo
2. Actualizar la lista de aplicaciones
3. Buscar "Academia de Idiomas" e instalar

## Dependencias

- `base`
- `mail`

## Autor

Marco

## Licencia

LGPL-3
