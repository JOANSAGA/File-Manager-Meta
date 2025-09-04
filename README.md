# File Manager Meta

Herramienta de línea de comandos para gestionar, organizar y analizar ficheros de forma eficiente.

## Tabla de Contenidos

- [Instalación](#instalación)
- [Requisitos Externos](#requisitos-externos)
- [Características](#características)
- [Uso](#uso)
  - [Ordenar Ficheros (`sort`)](#ordenar-ficheros-sort)
  - [Generar Informes (`report`)](#generar-informes-report)
  - [Reparar Extensiones (`repair`)](#reparar-extensiones-repair)
  - [Eliminar Duplicados (`deduplicate`)](#eliminar-duplicados-deduplicate)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Bugs Conocidos](#bugs-conocidos)
- [Contribuidores](#contribuidores)
- [Licencia](#licencia)

---

## Instalación

Sigue estos pasos para instalar y configurar el proyecto en tu entorno local:

1.  **Clona el repositorio**:
    ```bash
    git clone https://github.com/JOANSAGA/File-Manager-Meta
    cd File-Manager-Meta
    ```
2.  **Instala Poetry (si no lo tienes instalado):**
    ```bash
    pip install poetry
    ```
3.  **Instala las dependencias del proyecto:**
    ```bash
    poetry install
    ```
4.  **Ejecuta la aplicación**:
    ```bash
    poetry run file-manager-meta --help
    ```

---

## Requisitos Externos

Este proyecto requiere **ExifTool** para la funcionalidad de `repair`. Asegúrate de tenerlo instalado y accesible en el PATH de tu sistema.

- **Windows**: `winget install exiftool`
- **Linux**: `apt install exiftool`
- **MacOS**: `brew install exiftool`

---

## Características

- **Clasificación de Ficheros**: Organiza ficheros en subdirectorios basándose en su extensión, fecha de creación (con granularidad por año, mes o día) o tamaño.
- **Informes Detallados**: Genera informes en la consola o en formato HTML con los hashes de integridad (MD5, SHA-1, SHA-256) de todos los ficheros, agrupados por subcarpetas, e identifica conjuntos de ficheros duplicados.
- **Detección y Eliminación de Duplicados**: Localiza ficheros con contenido idéntico en todas las subcarpetas y ofrece la opción de eliminarlos de forma segura, conservando uno de ellos según una regla (ej. el más antiguo), con un modo de simulación (`--dry-run`) para prevenir la pérdida de datos.
- **Reparación de Extensiones**: Analiza ficheros sin extensión y les asigna la correcta basándose en sus metadatos (requiere ExifTool). Ahora soporta procesamiento por lotes y cacheo de resultados para mayor eficiencia.

---

## Uso

A continuación se detallan los comandos principales y sus opciones.

### Ordenar Ficheros (`sort`)

Organiza los ficheros de un directorio en subcarpetas.

```bash
file-manager-meta sort <directorio> --sort-by <criterio>
```

- **Criterios de ordenación (`--sort-by`)**:
    *   `ext`: Por extensión.
    *   `date`: Por fecha de creación. Puede usarse con `--date-granularity`.
    *   `size`: Por tamaño.

- **Granularidad de fecha (`--date-granularity`)**: Solo válido con `--sort-by date`.
    *   `year`: Organiza por año (ej. `2023/`).
    *   `month`: Organiza por año y mes (ej. `2023/01/`).
    *   `day`: Organiza por año, mes y día (ej. `2023/01/15/`). (Por defecto si no se especifica granularidad).

### Generar Informes (`report`)

Crea un informe con los hashes de todos los ficheros y una lista de los duplicados.

```bash
file-manager-meta report <directorio>
```

- **Salida a HTML (`--output`)**: Para guardar el informe en un fichero HTML.
  ```bash
  file-manager-meta report <directorio> --output reporte.html
  ```

### Reparar Extensiones (`repair`)

Busca ficheros sin extensión en uno o varios directorios/ficheros y se la asigna usando sus metadatos. Soporta múltiples rutas.

```bash
file-manager-meta repair <ruta1> [ruta2 ...]
```

- **Ejemplo**: `file-manager-meta repair /ruta/a/directorio1 /ruta/a/fichero.bin`

### Eliminar Duplicados (`deduplicate`)

Busca y elimina ficheros duplicados. **¡Usa este comando con precaución!**

```bash
file-manager-meta deduplicate <directorio> [OPTIONS]
```

**Flujo de trabajo recomendado y seguro:**

1.  **Ejecuta una simulación (`--dry-run`)**: Este modo te mostrará un informe detallado de qué ficheros se conservarían (`KEEP`) y cuáles se borrarían (`DELETE`) sin tocar nada.

    ```bash
    file-manager-meta deduplicate <directorio> --dry-run
    ```

2.  **Revisa el plan**: Analiza las tablas para asegurarte de que estás de acuerdo con las acciones propuestas.

3.  **Ejecuta el borrado real**: Si estás seguro, ejecuta el comando sin `--dry-run`. El programa te pedirá una confirmación final antes de borrar nada.

    ```bash
    file-manager-meta deduplicate <directorio>
    ```

- **Opción de conservación (`--keep`)**: Por defecto, se conserva el fichero más antiguo (`oldest`).

---

## Estructura del Proyecto

```
src/
└── file_manager_meta/
    ├── __init__.py
    ├── cli.py          # Comandos principales de la CLI
    ├── cache_manager.py # Gestión de la caché de hashes y metadatos
    ├── deduplicate.py  # Lógica para eliminar duplicados
    ├── enums.py        # Enumeraciones para criterios de la CLI
    ├── hashes.py       # Lógica para calcular hashes (con cacheo)
    ├── repair.py       # Lógica para reparar extensiones (con batching y cacheo)
    ├── report.py       # Lógica para generar informes (con cacheo y paralelismo)
    └── sort.py         # Lógica para clasificar archivos (con manejo de errores)
tests/
└── __init__.py
```

---

## Bugs Conocidos

- **Error con archivos que tengan tilde**: Puede ocurrir con algunos nombres de archivo que contienen caracteres especiales, especialmente en `repair`. La herramienta ahora proporciona mensajes de error más claros, pero la solución definitiva podría depender de la configuración del sistema o de actualizaciones de `ExifTool`/`pyexiftool`.

---

## Contribuidores

- [JOANSAGA](https://github.com/JOANSAGA)

---

## Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.