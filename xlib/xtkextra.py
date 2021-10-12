# XTK_Viewer extras
# 09:17 p.m. 09/11/2020
# Medina Dylan
# XTKViewer Extras (Visor de XCIF en Tkinter - Extras)


from tkinter import ttk
import os


class FileEntry(ttk.Entry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.unbind_all("<<NextWindow>>")
        self.bind("<Key-Tab>", self._search_files)
        self._search_data = {'filter_ext': []}
        self._delete_search_data()

        self.bind("<Key-Left>", self._delete_search_data)
        self.bind("<Key-Right>", self._delete_search_data)

    def _delete_search_data(self, _=None):
        self._search_data.update(
            {'text': None, 'last_edit': None, 'basepath': None, 'current': None, 'number': 0}
        )

    def _search_files(self, _=None):
        path = self.get()
        last_edit = self._search_data.get("last_edit", None)

        if not path == last_edit:
            self._delete_search_data()
            self._search_data['text'] = path
            basepath, current = os.path.split(path)
            basepath = os.path.abspath(basepath)

            self._search_data['basepath'] = basepath
            self._search_data['current'] = current

        else:
            basepath = self._search_data['basepath']
            current = self._search_data['current']

        current = current.lower()
        number = 0
        result = list(filter(lambda x: self._filter_search(x, current, basepath), os.listdir(basepath+"\\")))
        number_result = len(result)

        for i in result:
            if number >= (self._search_data['number'] % number_result):
                new_path = os.path.join(basepath, i)
                if new_path != last_edit:
                    self.delete(0, "end")
                    self.insert(0, new_path)
                    if os.path.isdir(new_path):
                        self.insert("end", "\\")

                self._search_data['last_edit'] = self.get()
                self._search_data['number'] = number+1
                break

            number += 1

    def _filter_search(self, x, current, basepath):
        path = os.path.join(basepath, x)

        if x.lower().startswith(current):
            if len(self._search_data['filter_ext']) >= 1 and not os.path.isdir(path):
                return os.path.splitext(x)[-1].lower() in self._search_data['filter_ext']
            else:
                return True
        else:
            return False

    def set_filter_search(self, data: list):
        self._search_data['filter_ext'] = tuple(map(str.lower, data))


HELP_DICT = {}

HELP_DICT['PRINCIPAL'] = """\
Este programa permite la creación de archivos XCIF; los mismos funcionan como \
contenedores de archivos y directorios, protegiendolos contra accesos no deseados.
Dichos archivos pueden contener hasta 3 contraseñas distintas.

Botones del menú:
* Nuevo:
    Permite la creación de nuevos archivos XCIF mediante una serie de pasos.
* Abrir:
    Permite extraer los archivos XCIF mediante una serie de pasos. 
* Configuración:
    Permite cambiar los ajustes de la aplicación.
* Acerca de:
    Permite ver información sobre el autor y el programa.
* Ayuda:
    Permite visualizar el menú de ayuda (este mensaje).
* Salir:
    Finaliza la ejecución de la aplicación.

Archivos Recientes:
* Es una lista de los últimos archivos nuevos y archivos abiertos recientemente.
* Para abrir un archivo usado recientemente solo realice clic sobre él dos veces.

Teclas rápidas:
* Control + 1 / Control + N: Nuevo archivo XCIF.
* Control + 2 / Control + O: Abrir archivo XCIF.
* Control + 3 / Control + S: Abre el menú de "Ajustes".
* Control + 4 / Control + A: Abre el menú de "Acerca de."
* Control + 5 / Control + H / F1: Muestra la ayuda.
* Control + 9: Salir de la aplicación.
"""

HELP_DICT['NUEVO_PASO_1'] = """\
Añadir:
* Archivos:
    Permite añadir archivos a la lista para que estos sean cifrados.
* Carpeta:
    Permite añadir un directorio (y todo su contenido) a la lista.

Excluir:
* Archivos:
    Permite añadir archivos que serán excluidos al realizar el escaneo de los archivos.
* Carpetas:
    Permite añadir un directorio que será excluido al realizar el escaneo de las carpetas.
* Extensión:
    Permite excluir una extensión durante el escaneo, todos los archivos que contengan \
dicha extensión no serán incluidos. Las extensiones deben empezar con ".", ejemplo: ".exe".

Otros:
* Remover:
    Permite quitar los archivos seleccionados de la lista (los archivos seguirán disponibles en la \
unidad de almacenamiento).


Teclas rápidas:
* Control + 1: Añadir Archivo
* Control + 2: Añadir Carpeta
* Control + 3: Añadir Archivo para Excluír
* Control + 4: Añadir Carpeta para Excluír
* Control + 5: Añadir Extensión para Excluír
* Control + 6: Remover seleccion.
* Delete (Suprimir): Remover seleccion.
* Shift: Seleccionar muchos (consecutivos).
* Control: Seleccionar muchos (de a uno).
"""

HELP_DICT['NUEVO_PASO_2'] = """\
Guardar Archivo XCIF:
* Seleccionar el directorio donde se guardará el archivo XCIF y el nombre del mismo.

Autor:
* Indicar el nombre del autor del archivo. Por defecto, se tomará el nombre del usuario actual.

Comentario:
* Una nota sobre el archivo, la misma podrá ser vista aunque no se conozca la contraseña del archivo.
* Es posible cargar y guardar comentarios en archivos de texto (.txt).


Teclas rápidas:
* F2: Seleccionar directorio
* F3: Colocar el autor predeterminado.
* Control + F2: Cargar comentario.
* Control + F3: Guardar un comentario.
"""

HELP_DICT['CONTRASEÑAS'] = """\
Claves:
* Escribir una clave que posea como mínimo 8 letras.
* El uso de las claves es opcional.
* Se pueden elegir hasta 3 claves, es decir, no es obligatorio usar todas.
* No es posible definir la contraseña número 2 sin primero definir la número 1.
* Tampoco es posible definir la contraseña número 3 sin primero definir la número 1 y 2.

Mostrar:
* Permite visualizar la clave escrita.

Usar archivo:
* Permite usar un archivo como contraseña.
* Del archivo se obtiene su Identificador de 128 caracteres que representa únicamente \
a este archivo.
* Es recomendable, en archivos muy sensibles, utilizar una clave alfanumérica, y un \
archivo, para mayor seguridad.
"""


HELP_DICT['ABRIR_PASO_1'] = """\
Archivo XCIF:
* Selecionar el archivo XCIF para realizar la extracción.

Extraer en:
* Directorio donde se guardará los archivos y directorios que están dentro del archivo XCIF.

Tamaño:
* Indica el tamaño del fichero seleccionado.

Espacio Libre (Disco):
* Indica el tamaño disponible en la unidad que contiene el directorio seleccionado para la extracción.

Teclas rápidas:
* F2: Seleccionar el archivo XCIF / Seleccionar el directorio de extracción
"""

HELP_DICT['ABRIR_PASO_2'] = """\
Versión de XCIF utilizada:
* Indica qué versión de XCIF se utilizó al cifrar el archivo.
* Es posible copiar la información al portapapeles.

Autor:
* Nombre del autor del archivo.
* Es posible copiar la información al portapapeles.

Comentario:
* Notas que dejó el autor al crear el archivo. 
* Puede estar vacío.
* Es posible copiar la información al portapapeles.
* Es posible exportar la información a un documento de texto.
"""

HELP_DICT['AJUSTES_PASO_1'] = """\
Vaciar lista de archivos recientes:
* Permite vaciar la lista de archivos recientes de la ventana principal.
"""

HELP_DICT['AJUSTES_PASO_2'] = """\
Método de verificación por HASH:
* Es el método de verificación que se usa internamente dentro del archivo XCIF.
* Este método es guardado dentro del archivo XCIF, es decir, si un archivo fue \
creado con un método, el mismo no puede cambiarse.
* No es necesario cambiar este ajuste generalmente.
* Predeterminado: SHA3-256.
"""


HELP_DICT['GUARDANDO'] = """\
Esta ventana sirve para ver el progreso de creación del archivo.

Total:
* Aquí se muestran datos tales como: La cantidad de archivos, el tamaño total, \
el progreso, el tiempo transcurrido, y el tiempo restante (aproximado).

Actual:
* Aquí se muestran datos tales como: El nombre del archivo, el tamaño del mismo, \
el tiempo transcurrido (solo para el archivo actual) y el tiempo total (aproximado, \
y solo para el archivo actual).
"""

HELP_DICT['CARGANDO'] = """\
Esta ventana sirve para ver el progreso de descifrado del archivo.

Total:
* Aquí se muestran datos tales como: La cantidad de archivos procesados, el tamaño \
total, el progreso, el tiempo transcurrido, y el tiempo restante (aproximado).

Actual:
* Aquí se muestran datos tales como: El nombre del archivo, el tamaño del mismo, \
el tiempo transcurrido (solo para el archivo actual) y el tiempo total (aproximado, \
y solo para el archivo actual).
"""
