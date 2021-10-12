#-----------------------------------------------------------------------------#
#                    PROYECTO PRÁCTICAS PROFESIONALIZANTES                    #
#-----------------------------------------------------------------------------#
#   Datos sobre el alumno:                                                    #
#   ----------------------                                                    #
#   Alumno:        Medina Dylan                                               #
#   Profesor:      Stevenin Flavio                                            #
#   Curso:         7mo 3ra                                                    #
#   Año:           2020                                                       #
#   Escuela:       E.E.S.T. N1 de Muñiz "Nuestra Señora del Valle"            #
#-----------------------------------------------------------------------------#
#   Datos sobre el proyecto:                                                  #
#   ------------------------                                                  #
#   Nombre:                 Administrador XCIF                                #
#   Descripción Breve:      Software capaz de encriptar y desencriptar datos  #
#                           de archivos ".xcif". Dichos archivos pueden estar #
#                           protegidos por una o más claves de seguridad.     #
#   Categoría:              Seguridad                                         #
#-----------------------------------------------------------------------------#
#   Datos técnicos sobre el proyecto:                                         #
#   ---------------------------------                                         #
#   Lenguaje:               Python                                            #
#   Versión:                3.6.0 o superior                                  #
#   Sistema Operativo:      Windows 7 SP1 o superior [32b o 64b]              #
#   Requisitos extra:       Modulos:                                          #
#                           * pywin32                                         #
#                           * pillow                                          #
#-----------------------------------------------------------------------------#

import sys
import argparse
import os

from xlib import xcif, xtkviewer


def start_graphical(**kwargs):
    xtkviewer.start_window(**kwargs)


def process_graphical_command(data):
    if data.option is None:
        start_graphical()
    else:
        kwargs = dict(option=data.option, exit_after=data.exit)

        if data.option == "open":
            kwargs['data_option'] = [{}, {}]

            if data.data_open is not None:
                kwargs['data_option'][0]['xcif_file'] = os.path.abspath(data.data_open)

            if data.data_folder is not None:
                kwargs['data_option'][0]['save_as'] = os.path.abspath(data.data_folder)

        elif data.option == "new":
            kwargs['data_option'] = [{}, {}, {}]

            if data.data_paths is not None:
                kwargs['data_option'][0]['paths'] = list(
                    map(os.path.abspath,
                        data.data_paths)
                )

            if data.data_exclude_paths is not None:
                kwargs['data_option'][0]['exclude_paths'] = list(
                    map(os.path.abspath,
                        data.data_exclude_paths)
                )

            if data.data_exclude_exts is not None:
                kwargs['data_option'][0]['exclude_ext'] = data.data_exclude_exts

            if data.data_save_as is not None:
                kwargs['data_option'][1]['save_as'] = os.path.abspath(data.data_save_as)

            if data.data_author is not None:
                kwargs['data_option'][1]['author'] = data.data_author

            if data.data_comment is not None:
                kwargs['data_option'][1]['comment'] = data.data_comment

        if data.option in ("open", "new"):
            if data.data_password is not None:
                passwords = data.data_password
                if len(passwords) >= 1:
                    kwargs['data_option'][-1]['password1'] = passwords[0]
                    if len(passwords) >= 2:
                        kwargs['data_option'][-1]['password2'] = passwords[1]
                        if len(passwords) >= 3:
                            kwargs['data_option'][-1]['password3'] = passwords[2]
                            if len(passwords) >= 4:
                                print(f"Error: Too many passwords: Max 3 passwords, {len(data.data_password)} found.")
                                return False

            kwargs['data_option'].append(dict(ok_command=data.data_ok_command))

        start_graphical(**kwargs)


def process_encrypt_command(data):
    new = xcif.XCIF(data.filename)
    if data.password:
        if len(data.password) <= 3:
            new.add_methods_by_passwords(*data.password)
        else:
            print(f"Error: Too many passwords: Max 3 passwords, {len(data.password)} found.")
            return False

    if data.method is not None:
        new.hashlib_method = {
            "sha3_224": b"3_224",
            "sha3_256": b"3_256",
            "sha3_384": b"3_384",
            "sha3_512": b"3_512",
            "sha224": b"224",
            "sha256": b"256",
            "sha384": b"384",
            "sha512": b"512",
            "sha1": b"1",
            "md5": b"md5"
        }.get(data.method)

    try:
        new.compress_from(data.paths, data.exclude_paths, data.exclude_exts,
                          author=data.author, comment=data.comment)

    except BaseException as exc:
        return print(f"Error:\n{exc.__class__.__name__}: {exc}")

    print("\nComplete!")


def process_decrypt_command(data):
    load = xcif.XCIF(data.filename)
    if data.password:
        if len(data.password) <= 3:
            load.add_methods_by_passwords(*data.password)
        else:
            print(f"Error: Too many passwords: Max 3 passwords, {len(data.password)} found.")
            return False

    try:
        load.extract_to(os.path.abspath(data.dest))
    except BaseException as exc:
        return print(f"Error:\n{exc.__class__.__name__}: {exc}")

    print("\nComplete!")


def process_readinfo_command(data):
    load = xcif.XCIF(data.filename)

    try:
        properties = load.get_header()
    except BaseException as exc:
        return print(f"Error:\n{exc.__class__.__name__}: {exc}")

    if properties['COMMENT'] is None:
        properties['COMMENT'] = "<< Información desconocida >>".encode()

    if properties['USER'] is None:
        properties['USER'] = "<< Información desconocida >>".encode()

    print(f"\nInformación del archivo: {os.path.basename(data.filename)}\n\n"
          f"Versión Requerida:    {properties['VERSION']}\n"
          f"Usuario:              {properties['USER'].decode()}\n"
          f"Comentario:           {properties['COMMENT'].decode()}\n"
          )


if __name__ == "__main__":
    # Controlar la versión de python.
    if not (sys.version_info.major >= 3 and sys.version_info.minor >= 6):
        print("No es posible ejecutar el archivo en esta versión de Python.\n"
              "Por favor utilice una versión más reciente.")

    # Controlar argumentos de ejecusión recibidos:
    # Si no hay argumentos, iniciar la ventana.
    if len(sys.argv) < 2:
        start_graphical()

    # Si hay argumentos usar la interfaz en consola con "argparse"
    else:
        parser = argparse.ArgumentParser(
            fromfile_prefix_chars="@",
            description="Permite cifrar y descifrar archivos XCIF"
                        "mediante el uso de hasta tres contraseñas.\n"
        )

        subparsers = parser.add_subparsers(
            title="Sub-comandos",
            description="Para obtener la ayuda de un subcomando ejecute %(prog)s [COMMAND] -h",
            help="",
            dest='command'
        )
        # Encrypt command
        encrypt = subparsers.add_parser(name="encrypt",
                                        aliases=["enc"],
                                        help="Permite cifrar los archivos indicados dentro de un archivo XCIF de destino.",
                                        description="Permite cifrar los archivos indicados dentro de un archivo XCIF de destino."
                                        )
        encrypt.add_argument('filename', help="Archivo XCIF de destino.")
        encrypt.add_argument('-i', '--paths', '--include_paths',
                             metavar="PATH",
                             nargs="+",
                             help="Ruta de los archivos que se desea agregar.",
                             required=1
                             )
        encrypt.add_argument('-e', '--exclude_paths',
                             metavar="PATH",
                             nargs="+",
                             help="Ruta de los archivos que se desea omitir.",
                             default=[]
                             )
        encrypt.add_argument('-x', '--exclude_exts',
                             metavar="PATH",
                             nargs="+",
                             help="Ruta de las extensiones que sea desea omitir.",
                             default=[]
                             )
        encrypt.add_argument('-m', '--method', '--hash',
                             metavar="HASH",
                             help="Nombre del hash a utilizar para las verificaciones (por defecto: sha3_256).",
                             default="3_256",
                             choices=["sha3_224", "sha3_256", "sha3_384", "sha3_512",
                                      "sha224", "sha256", "sha384", "sha512", "sha1", "md5"]
                             )
        encrypt.add_argument('-c', '--comment',
                             metavar="COMMENT",
                             help="Comentario del archivo (opcional)."
                             )
        encrypt.add_argument('-a', '--author', '--user',
                             help="Autor del archivo (opcional)."
                             )
        encrypt.add_argument("-p", "--password",
                             metavar="PASSWORD",
                             help='Contraseñas de seguridad del archivo. Se recomienda usar comillas para escribir las mismas.\n'
                             'Ejemplo: %(prog)s "file.xcif" -i "include.jpg" -p "password1" "pass word 2"',
                             nargs="+")

        # Decrypt command
        decrypt = subparsers.add_parser(name="decrypt",
                                        aliases=["dec"],
                                        help="Permite descifrar el archivo XCIF indicado en un directorio de destino.",
                                        description="Permite descifrar el archivo XCIF indicado en un directorio de destino."
                                        )
        decrypt.add_argument('filename', metavar="PATH", help="Archivo XCIF existente.")
        decrypt.add_argument("dest", metavar="FOLDER_PATH", help="Directorio de destino.")
        decrypt.add_argument("-p", "--password",
                             metavar="PASSWORD",
                             help='Contraseñas de seguridad del archivo. Se recomienda usar comillas para escribir las mismas.\n'
                             'Ejemplo: %(prog)s "file.xcif" "extract" -p "password1" "pass word 2"',
                             nargs="+")

        # ReadInfo command
        readinfo = subparsers.add_parser(name="readinfo",
                                         aliases=["get_properties", "info"],
                                         help="Permite conocer la información básica del archivo XCIF.",
                                         description="Permite conocer la información básica del archivo XCIF."
                                         )
        readinfo.add_argument('filename', metavar="PATH", help="Archivo XCIF existente.")

        # Graphical command
        graphical = subparsers.add_parser(name="graphical",
                                          aliases=["win", "window"],
                                          help="Inicia la ventana del Administrador de XCIF",
                                          description="Inicia la ventana del Administrador de XCIF"
                                          )

        graphical.add_argument('-o', "--option",
                               help="Inicia la ventana y automáticamente selecciona una opción.",
                               choices=["new", "open", "settings", "about", ]
                               )
        graphical.add_argument('-q', "--exit", "--quit",
                               help="Salir de la ventana luego de haber llamado la opción requerida.",
                               action="store_true"
                               )
        graphical.add_argument('-a', "--data_open",
                               metavar="FILE",
                               help='Envía el archivo XCIF predeterminado al usar la opción "open": Archivo XCIF. Ejemplo:\n'
                               '%(prog)s -o open --data_open "file.xcif" --data_folder "extract_folder"',
                               )
        graphical.add_argument('-b', "--data_folder",
                               metavar="FOLDER",
                               help='Envía el directorio de extracción al usar la opción "open". Ejemplo:\n'
                               '%(prog)s -o open --data_open "file.xcif" --data_folder "extract_folder"',
                               )
        graphical.add_argument('-c', "--data_comment",
                               metavar="COMMENT",
                               help='Envía el comentario al usar la opción "new": Archivo XCIF. Ejemplo:\n'
                               '%(prog)s -o new --data_comment "Comment"',
                               )
        graphical.add_argument('-d', "--data_author",
                               metavar="AUTHOR",
                               help='Envía el autor al usar la opción "new". Ejemplo:\n'
                               '%(prog)s -o new --data_author "Author"',
                               )
        graphical.add_argument('-f', "--data_save_as",
                               metavar="FILE",
                               help='Envía el directorio de extracción al usar la opción "new". Ejemplo:\n'
                               '%(prog)s -o new "file.xcif" --data_save_as "file.xcif"',
                               )
        graphical.add_argument('-i', '--data_paths', '--data_include_paths',
                               metavar="PATH",
                               nargs="+",
                               help='Ruta de los archivos que se desea agregar al usar la opcion "new".Ejemplo:\n'
                               '%(prog)s -o new --data_paths "file1.txt" "file2.txt"',
                               default=[]
                               )
        graphical.add_argument('-e', '--data_exclude_paths',
                               metavar="PATH",
                               nargs="+",
                               help='Ruta de los archivos que se desea omitir al usar la opcion "new".Ejemplo:\n'
                               '%(prog)s -o new --data_exclude_paths "documents\\file1.txt" "documents\\file2.txt"',
                               default=[]
                               )
        graphical.add_argument('-x', '--data_exclude_exts',
                               metavar="PATH",
                               nargs="+",
                               help='Ruta de las extensiones que sea desea omitir al usar la opcion "new". Ejemplo:\n'
                               '%(prog)s -o new --data_exclude_exts ".txt" ".jpg"',
                               default=[]
                               )
        graphical.add_argument("-p", "--data_password",
                               metavar="PASSWORD",
                               help='Contraseñas de seguridad del archivo al usar las opciones "new" y "open".\n'
                               'Ejemplo: %(prog)s -o open -a "file.xcif" -b "extract" -p "password1"',
                               nargs="+")
        graphical.add_argument("-s", "--data_ok_command",
                               help='Inicia el proceso de cifrado/descifrado al usar "new" y "open".\n'
                               'Ejemplo: %(prog)s -o open -a "file.xcif" -b "extract" -p "password1" -s',
                               action="store_true")

        # General argument
        parser.add_argument('--version',
                            action='version',
                            version='%(prog)s: v1.0, XCIF: v1.0, Interfaz XCIF: v1.0'
                            )

        args = parser.parse_args()

        if args.command in ("graphical", "win", "window"):
            process_graphical_command(args)

        elif args.command in ("encrypt", "enc"):
            process_encrypt_command(args)

        elif args.command in ("decrypt", "dec"):
            process_decrypt_command(args)

        elif args.command in ("readinfo", "get_properties", "info"):
            process_readinfo_command(args)

        # print(args)
        # print(sys.argv)
