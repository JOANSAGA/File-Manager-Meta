En el archivo `README.md`, podrías agregar las siguientes secciones para hacerlo más completo y profesional:

1. **Tabla de Contenidos**  
   Facilita la navegación en el archivo, especialmente si es extenso.

   ```markdown
   ## Tabla de Contenidos
   - [Características](#características)
   - [Instalación](#instalación)
   - [Uso](#uso)
   - [Ejemplo](#ejemplo)
   - [Requisitos](#requisitos)
   - [Contribuciones](#contribuciones)
   - [Licencia](#licencia)
   ```

2. **Estado del Proyecto**  
   Este proyecto está en desarrollo activo. Se aceptan contribuciones y sugerencias.

   ```markdown
   Funcionalidades listas
   - Desarrollar Reparar archivos sin extensión
   - Desarrollar sort by ext
   - Desarrollar sort by date
   
   Funcionalidades Futuras
    - Desarrollar sort by size
    - Desarrollar Report: 
        - Generar documento HTML
        - Ubicación de los archivos
        - Hashes
        - Exif
    ```

3. **Estructura del Proyecto**  
   Explica brevemente la estructura de carpetas y archivos principales.

   ```markdown
   ## Estructura del Proyecto
   ```
   ```plaintext
   src/
   ├── file_manager_meta/
   │   ├── cli.py          # Comandos principales de la CLI
   │   ├── sort.py         # Lógica para ordenar archivos
   │   ├── repair.py       # Reparación de extensiones
   ├── tests/              # Pruebas unitarias
   README.md               # Documentación del proyecto
   ```

4. **Pruebas**  
   Pruebas unitarias en proceso.

   ```markdown
   
   ```

5. **Contribuidores**  
   Lista de personas que han contribuido al proyecto.

   ```markdown
   ## Contribuidores
   - [Nombre del Contribuidor](https://github.com/usuario)
   ```

6. **Notas Adicionales o Limitaciones**  
   Menciona cualquier limitación conocida o aspectos importantes del proyecto.

   ```markdown
   ## Notas Adicionales
   - Actualmente, la herramienta no soporta archivos ocultos.
   - Se requiere `exiftool` instalado para la funcionalidad de reparación.
   
   ## Bugs
   - Error con archivos que tengan tilde
   - Restar archivos sin extensión del conteo final de archivos ordenados
   - Corregir el conteo de archivos reparados sin extensión
   - Modificar Funcionalidad "REPARAR" para que acepte arrary de direcciones o archivos
   - Ignorar Carpeta System volumen information 
   ```

7. **Referencias**  
   Incluye enlaces a documentación o recursos externos relevantes.

   ```markdown
   ## Referencias
   - [Typer Documentation](https://typer.tiangolo.com/)
   - [Rich Documentation](https://rich.readthedocs.io/)
   ```

Estas secciones harán que tu `README.md` sea más informativo y útil para los usuarios y colaboradores.