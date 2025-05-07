# File Manager Meta

## Tabla de Contenidos

- [Instalación para Desarrollo](#instalación-para-desarrollo)
- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Pruebas](#pruebas)
- [Notas Adicionales, Bugs](#notas-adicionales-bugs)
- [Contribuidores](#contribuidores)
- [Referencias](#referencias)
- [Licencia](#licencia)

---

## Instalación para Desarrollo:

Sigue estos pasos para instalar y configurar el proyecto en tu entorno local:

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/JOANSAGA/File-Manager-Meta
   cd File-Manager-Meta
   ```
2. **Instala Poetry (si no lo tienes instalado):**
   ```bash
   pip install poetry
   ```
3. **Instala las dependencias del proyecto:**
   ```bash
    poetry install
    ```
4. **Ejecuta la aplicación**
    ```bash
    file-manager-meta
    ```

---

## Requisitos Externos

Este proyecto requiere la instalación de una herramienta externa llamada `Exiftool` para manejar metadatos de archivos.
Asegúrate de instalarla antes de usar las funcionalidades relacionadas.

Instucciones de instalación desde la web oficial de [ExifTool](https://exiftool.org/)

### Instalación usando gestores de paquetes:

- **Windows**:
  ```bash
  winget install exiftool
  ```

- **Linux**:
  ```bash
  apt install exiftool
  ```

- **MacOS**:
  ```bash
  brew install exiftool
  ```

---

## Características

- Funcionalidades listas:
    - Reparar archivos sin extensión.
    - Ordenar por extensión.
    - Ordenar por fecha.


- Funcionalidades futuras:
    - Ordenar por tamaño.
    - Generar reportes en HTML con:
        - Ubicación de los archivos.
        - Hashes.
        - Metadatos Exif.

---

## Estructura del Proyecto

   ```plaintext
   src/
   ├── file_manager_meta/
   │   ├── cli.py          # Comandos principales de la CLI
   │   ├── sort.py         # Lógica para ordenar archivos
   │   ├── repair.py       # Reparación de extensiones
   ├── tests/              # Pruebas unitarias
   README.md               # Documentación del proyecto
   ```

---

## Pruebas

Pruebas unitarias en proceso.

   ```markdown
   
   ```

---

## Bugs

- Error con archivos que tengan tilde
- Restar archivos sin extensión del conteo final de archivos ordenados
- Corregir el conteo de archivos reparados sin extensión
- Modificar Funcionalidad "REPARAR" para que acepte arrary de direcciones o archivos
- Ignorar Carpeta System volumen information
- La herramienta puede dar error con archivos ocultos.

---

## Contribuidores

Lista de personas que han contribuido al proyecto.

- [JOANSAGA](https://github.com/JOANSAGA)

---

## Referencias

- [ExifTool](https://exiftool.org/)
- [Rich](https://rich.readthedocs.io/en/stable/)
- [Typer](https://typer.tiangolo.com/)