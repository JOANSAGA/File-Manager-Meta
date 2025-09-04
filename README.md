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

- **Clasificación de Ficheros**: Organiza ficheros en subdirectorios basándose en su extensión o fecha de creación.
- **Informes Detallados**: Genera informes en la consola o en formato HTML con los hashes de integridad (MD5, SHA-1, SHA-256) de todos los ficheros, agrupados por subcarpetas.
- **Detección y Eliminación de Duplicados**: Localiza ficheros con contenido idéntico en todas las subcarpetas y ofrece la opción de eliminarlos de forma segura, conservando uno de ellos según una regla (ej. el más antiguo).
- **Reparación de Extensiones**: Analiza ficheros sin extensión y les asigna la correcta basándose en sus metadatos (requiere ExifTool).

---

## Uso

A continuación se detallan los comandos principales y sus opciones.

### Ordenar Ficheros (`sort`)

Organiza los ficheros de un directorio en subcarpetas.

```bash
file-manager-meta sort <directorio> --sort-by <criterio>
```

- **Criterios de ordenación (`--sort-by`)**: `ext` (extensión), `date` (fecha).

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

Busca ficheros sin extensión en un directorio y se la asigna usando sus metadatos.

```bash
file-manager-meta repair <directorio>
```

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
    ├── deduplicate.py  # Lógica para eliminar duplicados
    ├── enums.py        # Enumeraciones para criterios de la CLI
    ├── hashes.py       # Lógica para calcular hashes
    ├── repair.py       # Lógica para reparar extensiones de archivo
    ├── report.py       # Lógica para generar informes
    └── sort.py         # Lógica para clasificar archivos
tests/
└── __init__.py
```

---

## Bugs Conocidos

- El manejo de ficheros con tildes o caracteres especiales en el nombre puede ser inconsistente.
- El conteo de ficheros en los resúmenes puede no ser siempre exacto.
- Errores de permisos con ficheros ocultos o del sistema (ej. `System Volume Information`).

---

## Contribuidores

- [JOANSAGA](https://github.com/JOANSAGA)

---

## Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.
