# XLIB > xparser.py
# 07:10 p.m. 21/09/2020
# Medina Dylan
# XParser (Analizador)
#
# -------------------------------------------------------------------------------------------------
# Indicaciones:
# -------------
#  TOKEN          LETRA   DESCRIPCIÓN
# -------------- ------- --------------------------------------------------------------------------
# [FILE_CONTENT] -A      Inicio del contenido un archivo (debe ir después del -N).
# [COMMENT]      -C      Comentario creado por el usuario (no está cifrado, debe ir antes del -V).
# [DIR_NAME]     -D      Nombre del directorio.
# [FINISH_TASK]  -F      Finaliza la tarea (acción) actual.
# [HASH]         -H      Indica el HASH (SHA3-256), es opcional, pero ayuda en la verificación.
# [FILE_INFO]    -I      Información del archivo (debe ir después del -N).
# [FILE_NAME]    -N      Nombre del archivo.
# [SETTINGS]     -O      Opciones de configuración (información, debe ir antes del -X).
# [PERMISSION]   -P      Permisos de archivo/directorio.
# [WORK_PATH]    -R      Ruta de trabajo.
# [DIRECT]       -S      Todo el contenido del archivo es sin cifrar (debe ir antes de -X).
# [SIZE]         -T      Tamaño del archivo (bytes)
# [USER]         -U      Información sobre usuario y/o autor (debe ir antes del -X).
# [VERSION]      -V      Versión del software utilizada (debe ir antes del -X).
# [X_START]      -X      Inicia el XCIF. Sin esta intrucción el archivo no será descifrado.
# [INDEX_CHAR]   -Y      Suma de N caracteres.
# [X_END]        -Z      Finaliza el XCIF. Indica el fin del archivo XCIF. Una vez reconocida esta
#                        instrucción el faltante del archivo no será analizado.
# -------------------------------------------------------------------------------------------------
# Orden de comandos:
# ------------------
# datos: [.]*
#
# cabecera: "XCIF-File"
#
# propiedades:  [-C datos -F] [-O datos -F] [-S] [-U datos -F] -V datos -F
#
# archivo:   -N datos -F   -T datos -F  [-H datos -F] [-I datos -F]
#           [-P datos -F] [-Y datos -F]  -A datos -F
#
# directorio: -D datos -F [-P datos -F]
#
# ruta_de_trabajo: [-R datos -F]
#
# archivo_XCIF: cabecera  propiedades  -X  (archivo | directorio | ruta_de_trabajo)*  -Z
# ---------------------------------------------------------------------------------------

from enum import Enum
import os
import hashlib
import time

__version__ = 1.0

#####################################################################################################
#                                                                                                   #
#   EXCEPTIONS: Objetos usados en los posibles errores que puede haber al cargar un archivo.        #
#                                                                                                   #
#####################################################################################################


class InvalidXCIFFileException(Exception):
    pass


class DuplicateException(Exception):
    pass


class HashError(Exception):
    pass

#####################################################################################################
#                                                                                                   #
#   FILES: Objetos capaces de trabajar con archivos, de manera más inteligente.                     #
#                                                                                                   #
#####################################################################################################


class FileData():
    def __init__(self, filename, methods):
        if not os.path.exists(filename):
            raise OSError('El archivo es inexistente o es inválido.')

        elif not os.path.isfile(filename):
            raise OSError('La ruta elegida no pertenece a un archivo válido.')

        self.__file = filename
        self.__mode = "-"
        self.__openfile = None
        self.__methods = tuple(reversed(methods))  # Reverse the list to decrypt.
        self.__decrypt = False
        self.pos = 0

    def read(self, buffer=8192, mode="rb"):
        if not self.__mode == mode:
            self.__openfile = open(self.__file, mode)
            self.__openfile.seek(self.pos)
            self.__mode = mode

        data = self.__openfile.read(abs(buffer))
        self.pos += len(data)
        return data

    def set_pos(self, new_pos):
        self.pos = new_pos
        if self.__mode in ("rb", "b"):
            self.__openfile.seek(self.pos)

    def get_size(self):
        return os.path.getsize(self.__file)

    def peek(self, amount):
        if self.__mode in ("rb", "b"):
            data = self.__openfile.read(amount)
            self.__openfile.seek(self.pos)
            return data

    def read_and_decrypt(self, buffer=8192):
        data = self.read(buffer, "rb")

        if self.__decrypt and data != b"":
            for method in self.__methods:
                data = method.decrypt(data)

        return data

    def __iter__(self, buffer=8192):
        line = self.read_and_decrypt(buffer)

        while line != b"":
            yield line
            line = self.read_and_decrypt(buffer)

    def active_decrypt(self, value=True):
        self.__decrypt = value

    def sort_methods(self, data, reverse=False):
        methods = []
        if reverse:
            data = data[::-1]

        for i in data.decode():
            if i == "0":
                pass
            else:
                id_method = int(i)
                for method in self.__methods:
                    if method.ID == id_method:
                        methods.append(method)
                        break

        self.__methods = methods


class FileIter():
    def __init__(self, filedata, buffer=8192):
        self.filedata = filedata
        self.pos = 0
        self.buffer = buffer
        self.text = b""

    def get_next(self, amount=1):
        data = b""
        while (len(self.text) - self.pos) < amount:
            data += self.text[self.pos:]
            amount -= (len(self.text)-self.pos)
            self.text = self.filedata.read_and_decrypt(self.buffer)
            self.pos = 0
            if self.text == b"":
                return data

        data += self.text[self.pos:self.pos+amount]
        self.pos += amount
        return data

    def ignore(self, amount=1):
        if (len(self.text) - self.pos) < amount:
            self.filedata.set_pos(self.filedata.pos - (len(self.text)-self.pos)+amount)
            self.pos = 0
            self.text = b""
            return True

        else:
            self.pos += amount

    def peek(self, amount=1):
        while (len(self.text) - self.pos) < amount:
            self.text += self.filedata.read_and_decrypt(self.buffer)
            if self.text == b"":
                return self.text[self.pos:self.pos+amount]

        return self.text[self.pos:self.pos+amount]

    def active_decrypt(self, value=True):
        self.filedata.active_decrypt(value)
        self.filedata.set_pos(self.filedata.pos - (len(self.text)-self.pos))
        self.pos = 0
        self.text = b""

    def sort_methods(self, data, reverse=True):
        self.filedata.sort_methods(data, reverse)

    def iter_to(self, amount, buffer=None):
        if buffer is None:
            buffer = self.buffer

        left = (len(self.text) - self.pos)
        if left < amount:
            yield self.text[self.pos:]
            self.text = b""
            self.pos = 0
            amount -= left

            while amount > 0:
                left = min(buffer, amount)
                amount -= left
                yield self.filedata.read_and_decrypt(left)

        else:
            yield self.get_next(amount)


#####################################################################################################
#                                                                                                   #
#   TOKENS: Objetos que pueden ser usados para trabajar en una estructura.                          #
#                                                                                                   #
#####################################################################################################

class TokenType(Enum):
    # Propiedades:
    COMMENT = b'-C'
    SETTINGS = b'-O'
    DIRECT = b'-S'
    USER = b'-U'
    VERSION = b'-V'

    # Archivos y Directorios:
    FILE_CONTENT = b'-A'
    HASH = b'-H'
    FILE_INFO = b'-I'
    FILE_NAME = b'-N'
    SIZE = b'-T'
    INDEX_CHAR = b'-Y'
    DIR_NAME = b'-D'
    PERMISSION = b'-P'
    WORK_PATH = b'-R'

    # General:
    FINISH_TASK = b'-F'
    X_START = b'-X'
    X_END = b'-Z'

    # Control:
    EOF = 0
    HEADER = 1
    CONTENT = 2
    UNRECOGNIZED_TOKEN = 3


class Token():
    def __init__(self, type, value, pos, pos_end, **kwargs):
        self.type = type
        self.value = value
        self.pos = pos
        self.pos_end = pos_end

    def compare(self, token_type):
        return self.type == token_type

    def __repr__(self):
        return f"Token(type={self.type!r}, value={self.value!r}, pos={self.pos!r}, pos_end={self.pos_end!r}, len={self.pos_end-self.pos!r})"

    def __str__(self):
        return self.__repr__()


#####################################################################################################
#                                                                                                   #
#   LEXER: Analiza un archivo, y retorna los token encontrados.                                     #
#                                                                                                   #
#####################################################################################################

class Lexer():
    def __init__(self, fileiter):
        self.fileiter = fileiter
        self.pos = 0
        self.current_char = None
        self.have_a_task = False

    def get_first_token(self):
        # Restart filedata:
        self.fileiter.filedata.set_pos(0)
        self.advance()

        # Match header "XCIF-File".
        if self.current_char is not None:
            if self.current_char.lower() == b"x":
                if self.peek(8).lower() == b"cif-file":
                    for _ in range(9):
                        self.advance()

                    return Token(
                        type=TokenType.HEADER,
                        value="XCIF-File",
                        pos=0,
                        pos_end=9,
                    )

    def get_next_token(self):
        while self.current_char is not None:

            if self.current_char == b"-":
                next_char = self.peek(1)

                if next_char == b"-":  # ignore "--"
                    self.advance()
                    self.advance()

                elif next_char.lower() in (b"a", b"c", b"d", b"f", b"h",
                                           b"i", b"n", b"o", b"p", b"r",
                                           b"s", b"t", b"u", b"v", b"x",
                                           b"y", b"z"):

                    value = (self.current_char + next_char).upper()
                    try:
                        token_type = TokenType(value)
                    except ValueError as exc:
                        print(f"Error, {exc.__class__.__name__}: {exc}")
                        self.advance()
                        self.advance()
                        continue

                    else:
                        token = Token(
                            type=token_type,
                            value=value,
                            pos=self.pos,
                            pos_end=self.pos+2,
                        )

                        if next_char.lower() in (b"a", b"c", b"d", b"h",
                                                 b"i", b"n", b"o", b"p",
                                                 b"r", b"t", b"u", b"v",
                                                 b"y"):

                            self.have_a_task = True
                        else:
                            self.have_a_task = False

                        self.advance()
                        self.advance()
                        return token

                else:
                    token = Token(
                        type=TokenType.UNRECOGNIZED_TOKEN,
                        value=(self.current_char+next_char),
                        pos=self.pos,
                        pos_end=self.pos+2)

                    self.advance()
                    self.advance()

                    return token

            else:
                if self.have_a_task:
                    return self.match_content_token()
                else:
                    self.advance()

        return Token(TokenType.EOF, None, self.pos+1, self.pos+1)

    def advance(self):
        self.pos += 1

        char = self.fileiter.get_next()

        if not char == b'':
            self.current_char = char
        else:
            self.current_char = None

    # ignore the current character and (ignore_amount-1) characters too, and advance.
    def ignore_and_advance(self, ignore_amount=1):
        if ignore_amount >= 2:
            self.pos += ignore_amount - 1
            self.fileiter.ignore(ignore_amount - 1)
        self.advance()

    def peek(self, count=1):
        return self.fileiter.peek(count)

    def iter_to(self, amount, buffer=None):
        if amount >= 1:
            if amount == 1:
                yield self.current_char
            else:
                file_content = self.fileiter.iter_to(amount-1, buffer)
                yield self.current_char + next(file_content)

                for content in file_content:
                    yield content

            self.advance()

    def match_content_token(self):
        value = b""
        initial_pos = self.pos

        while self.current_char is not None:
            if self.current_char != b'-':
                value = value + self.current_char
                self.advance()

            else:
                next_char = self.peek(1)
                if next_char == b'-':
                    value = value + b'-'
                    self.advance()
                    self.advance()
                else:
                    break

        return Token(
            type=TokenType.CONTENT,
            value=value,
            pos=initial_pos,
            pos_end=self.pos
        )


#####################################################################################################
#                                                                                                   #
#   PARSER: Recibe los tokens, y los utiliza en base a una estructura predefinida.                  #
#                                                                                                   #
#####################################################################################################

class Parser():
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None
        self.maker = None
        self.interface = None

    def eat(self, token_type):
        if self.current_token.compare(token_type):
            self.current_token = self.lexer.get_next_token()
            # Omitir tokens no reconocidos...
            while self.current_token.type == TokenType.UNRECOGNIZED_TOKEN:
                self.current_token = self.lexer.get_next_token()

        else:
            print("Wait: ", token_type, "Found: ", self.current_token)
            raise Exception(f"Unexpected token at {self.current_token.pos}, char: {self.lexer.current_char}.")

    def start(self, path='./extract', message_box="default", interface=None):
        self.current_token = self.lexer.get_first_token()
        self.maker = Maker(path, message_box=message_box)

        self.interface = interface
        if interface is not None:
            self.maker.set_interface(interface, self.lexer.fileiter.filedata)

        return self.start_rule()

    def get_header(self):
        self.current_token = self.lexer.get_first_token()
        return self.read_header_rule()

    def get_content_list(self):
        self.current_token = self.lexer.get_first_token()
        return self.read_list_rule()

    # PROGRAMA: cabecera propiedades
    def read_header_rule(self):
        """ read_header_rule: HEADER properties """
        if self.current_token.type == TokenType.HEADER:
            self.eat(TokenType.HEADER)

        else:
            raise InvalidXCIFFileException("Unrecognized header")

        properties = self.properties_rule()

        if properties['VERSION'] is None:
            raise InvalidXCIFFileException("Unspecified version")

        elif properties['VERSION'] > __version__:
            raise ValueError(
                "The version of the program is old, update the program to work with this file.")

        return properties

    # PROGRAMA: cabecera  propiedades  -X  (archivo | directorio | ruta_de_trabajo)*  -Z
    def read_list_rule(self):
        """ read_list_rule: HEADER properties X_START (file|folder|work_directory)* X_END """

        if self.current_token.type == TokenType.HEADER:
            self.eat(TokenType.HEADER)

        else:
            raise InvalidXCIFFileException("Unrecognized header")

        properties = self.properties_rule()

        if properties['VERSION'] is None:
            raise InvalidXCIFFileException("Unspecified version")

        elif properties['VERSION'] > __version__:
            raise ValueError(
                "The version of the program is old, update the program to work with this file.")

        self.eat(TokenType.X_START)

        out = working = {}

        while self.current_token.type in (TokenType.FILE_NAME, TokenType.DIR_NAME, TokenType.WORK_PATH):
            current = self.current_token
            if current.type == TokenType.FILE_NAME:
                data = self.file_rule(use_maker=False)
                working[data['NAME']] = data
                data.pop("NAME")
                data['FILE'] = True

            elif current.type == TokenType.DIR_NAME:
                data = self.dir_rule()
                working[data['NAME']] = {}

            elif current.type == TokenType.WORK_PATH:
                data = self.workpath_rule()
                working = out

                if data["WORK_PATH"] == b".":
                    continue

                split_path = []
                s = data['WORK_PATH']
                while s != b"":
                    s, t = os.path.split(s)
                    split_path.insert(0, t)

                for s in split_path:
                    working = working[s]

        self.eat(TokenType.X_END)

        return out

    # PROGRAMA: cabecera  propiedades  -X  (archivo | directorio | ruta_de_trabajo)*  -Z
    def start_rule(self):
        """ start_rule: HEADER properties X_START (file|folder|work_directory)* X_END """

        if self.maker is None:
            raise ValueError(
                "A Maker is required to extract data.\nUse my_parser_instance.start(path_to_extract, message_box)")

        if self.interface is not None:
            self.interface.show()
            self.interface.update()

        if self.current_token.type == TokenType.HEADER:
            self.eat(TokenType.HEADER)

        else:
            raise InvalidXCIFFileException("Unrecognized header")

        properties = self.properties_rule()

        if properties['VERSION'] is None:
            raise InvalidXCIFFileException("Unspecified version")

        elif properties['VERSION'] > __version__:
            raise ValueError(
                "The version of the program is old, update the program to work with this file.")

        if self.interface is not None:
            self.interface.update()

        self.eat(TokenType.X_START)

        while self.current_token.type in (TokenType.FILE_NAME, TokenType.DIR_NAME, TokenType.WORK_PATH):
            current = self.current_token
            if current.type == TokenType.FILE_NAME:
                data = self.file_rule()

            elif current.type == TokenType.DIR_NAME:
                data = self.dir_rule()
                self.maker.make_dir(data)

            elif current.type == TokenType.WORK_PATH:
                data = self.workpath_rule()
                self.maker.change_workpath(data)

            if self.interface is not None:
                if self.interface.cancel:
                    return None

                self.interface.update()

        self.eat(TokenType.X_END)

        if self.interface is not None:
            self.interface.end()

    # PROPIEDADES: [-C valor -F] [-O valor -F] [-S] [-U valor -F] -V valor -F
    def properties_rule(self):
        """
        properties_rule:
                [COMMENT value FINISH_TASK]
                [SETTINGS value FINISH_TASK]
                [DIRECT]
                [USER value FINISH_TASK]
                VERSION value FINISH_TASK
        """
        properties = {'COMMENT': None, 'SETTINGS': None,
                      'DIRECT': False, 'USER': None, 'VERSION': None}

        if self.current_token.type == TokenType.COMMENT:
            self.eat(TokenType.COMMENT)
            properties['COMMENT'] = self.value_rule()
            self.eat(TokenType.FINISH_TASK)

        if self.current_token.type == TokenType.SETTINGS:
            self.eat(TokenType.SETTINGS)
            properties['SETTINGS'] = self.value_rule()
            self.eat(TokenType.FINISH_TASK)

        if self.current_token.type == TokenType.DIRECT:
            self.eat(TokenType.DIRECT)
            properties['DIRECT'] = True

        if self.current_token.type == TokenType.USER:
            self.eat(TokenType.USER)
            properties['USER'] = self.value_rule()
            self.eat(TokenType.FINISH_TASK)

        # Version Token: Obligatory
        self.eat(TokenType.VERSION)
        properties['VERSION'] = float(self.value_rule())

        # Apply properties:
        self.lexer.fileiter.active_decrypt(not bool(properties['DIRECT']))

        if properties['SETTINGS'] is not None:
            self.lexer.fileiter.sort_methods(properties['SETTINGS'], True)

        # Close version:
        self.eat(TokenType.FINISH_TASK)
        return properties

    # VALOR: datos
    def value_rule(self):
        """ value_rule:  (CONTENT | FINISH_TASK) """
        if self.current_token.type == TokenType.CONTENT:
            value = self.current_token.value
            self.eat(TokenType.CONTENT)
            return value

        elif self.current_token.type == TokenType.FINISH_TASK:
            return None

        else:
            text = f"value is not defined at {self.current_token.pos}"
            raise ValueError(text)

    # ARCHIVO: -N valor -F   -T valor -F  [-H valor -F] [-I valor -F] [-P valor -F] [-Y valor -F]  -A valor -F
    def file_rule(self, use_maker=True):
        """
        file_rule:
            FILE_NAME value FINISH_TASK
            (
                SIZE value FINISH_TASK
                | [HASH value FINISH_TASK]
                | [FILE_INFO value FINISH_TASK]
                | [PERMISSION value FINISH_TASK]
                | [INDEX_CHAR value FINISH_TASK]
            )+
            FILE_CONTENT value FINISH_TASK
        """

        file_properties = {'NAME': None, 'SIZE': None, 'HASH': None,
                           'FILE_INFO': None, 'PERMISSION': None,
                           'INDEX_CHAR': None, 'FILE_CONTENT_POS': None}

        if self.current_token.type == TokenType.FILE_NAME:
            self.eat(TokenType.FILE_NAME)
            file_properties['NAME'] = self.value_rule()
            self.eat(TokenType.FINISH_TASK)

            while self.current_token.type in (TokenType.SIZE, TokenType.HASH, TokenType.FILE_INFO,
                                              TokenType.PERMISSION, TokenType.INDEX_CHAR):

                t_type = self.current_token.type  # token type
                self.eat(t_type)

                if t_type == TokenType.SIZE:
                    if file_properties['SIZE'] is None:
                        file_properties['SIZE'] = int(self.value_rule())
                        self.eat(TokenType.FINISH_TASK)

                    else:
                        raise DuplicateException(
                            "'SIZE' property defined twice.")

                elif t_type == TokenType.HASH:
                    if file_properties['HASH'] is None:
                        file_properties['HASH'] = self.value_rule()
                        self.eat(TokenType.FINISH_TASK)

                    else:
                        raise DuplicateException(
                            "'HASH' property defined twice.")

                elif t_type == TokenType.FILE_INFO:
                    if file_properties['FILE_INFO'] is None:
                        file_properties['FILE_INFO'] = self.value_rule()
                        self.eat(TokenType.FINISH_TASK)

                    else:
                        raise DuplicateException(
                            "'FILE_INFO' property defined twice.")

                elif t_type == TokenType.PERMISSION:
                    if file_properties['PERMISSION'] is None:
                        file_properties['PERMISSION'] = self.value_rule()
                        self.eat(TokenType.FINISH_TASK)

                    else:
                        raise DuplicateException(
                            "'PERMISSION' property defined twice.")

                elif t_type == TokenType.INDEX_CHAR:
                    if file_properties['INDEX_CHAR'] is None:
                        file_properties['INDEX_CHAR'] = int(
                            float(self.value_rule()))
                        self.eat(TokenType.FINISH_TASK)

                    else:
                        raise DuplicateException(
                            "'INDEX_CHAR' property defined twice.")

            if self.current_token.type == TokenType.FILE_CONTENT:
                file_properties['FILE_CONTENT_POS'] = (self.current_token.pos_end,
                                                       self.current_token.pos_end + file_properties['SIZE'])

                if use_maker:
                    self.maker.make_file(file_properties, self.lexer)
                else:
                    self.lexer.ignore_and_advance(file_properties['SIZE'])

                self.eat(TokenType.FILE_CONTENT)
                self.eat(TokenType.FINISH_TASK)

            return file_properties

    # DIRECTORIO: -D valor -F  [-P valor -F]
    def dir_rule(self):
        """
        dir_rule:
            DIR_NAME value FINISH_TASK
            [PERMISSION value FINISH_TASK]
        """

        dir_properties = {'NAME': None, 'PERMISSION': None}

        if self.current_token.type == TokenType.DIR_NAME:
            self.eat(TokenType.DIR_NAME)
            dir_properties['NAME'] = self.value_rule()
            self.eat(TokenType.FINISH_TASK)

            if self.current_token.type == TokenType.PERMISSION:
                self.eat(TokenType.PERMISSION)
                dir_properties['PERMISSION'] = self.value_rule()
                self.eat(TokenType.FINISH_TASK)

            return dir_properties

    # DIRECTORIO DE TRABAJO: -R valor -F
    def workpath_rule(self):
        """
        workpath_rule: WORK_PATH value FINISH_TASK
        """

        workpath_properties = {'WORK_PATH': None}

        if self.current_token.type == TokenType.WORK_PATH:
            self.eat(TokenType.WORK_PATH)
            workpath_properties['WORK_PATH'] = self.value_rule()
            self.eat(TokenType.FINISH_TASK)

            return workpath_properties


#####################################################################################################
#                                                                                                   #
#   MAKER: Realiza la extracción de los archivos y carpetas.                                        #
#                                                                                                   #
#####################################################################################################

class Maker():
    def __init__(self, path, message_box="default"):
        if isinstance(path, str):
            path = path.encode()

        self.start_path = os.path.abspath(path)
        self.__workpath = b'.'
        self.__apply_message_box = {'output': 0, 'for_all': False}
        self.message_box = message_box

        if not os.path.exists(self.start_path):
            os.makedirs(self.start_path, exist_ok=True)

        # Interface:
        self.interface = None
        self.data = {}
        self.filedata = None

    def set_interface(self, interface, filedata: FileData):
        self.interface = interface
        self.filedata = filedata
        self.data['n_file'] = 0
        self.data['total_size'] = self.filedata.get_size()
        self.data['total_size_format'] = get_size_unit(self.data['total_size'])
        self.data['time_start'] = time.time()
        self.data['seconds'] = 0

    def verify_file_hashes_before_extract(self, path, size, file_hash):
        current_size = os.path.getsize(path)
        if file_hash is not None and size == current_size:
            hashitem = get_hashitem(file_hash)

            if self.interface is not None:
                self.interface.value_name['text'] = "Analizando: "+self.interface.value_name['text']

            pos = 0
            with open(path, "rb") as r:
                line = r.read(8192)
                while line != b"":
                    pos += len(line)
                    hashitem.update(line)
                    line = r.read(8192)

                    if self.interface is not None:
                        self.interface.current_percent.set(99.99*(pos/size))
                        self.interface.update()
                        self.interface.root.update_idletasks()

                current_hash = hashitem.hexdigest()
                if compare_hash(file_hash, current_hash):
                    return 0  # No extraer

        return 1  # Extraer

    # path, size, file_hash
    def default_message_box(self, path, size, _=None):
        """
        Output:
        0: No extraer
        1: Extraer de todos modos
        2: Extraer y renombrar

        3: No extraer (en todos los casos)
        4: Extraer de todos modos (en todos los casos)
        5: Extraer y renombrar (en todos los casos)
        """
        current_size = os.path.getsize(path)

        print(f"\nEl archivo {path} ya existe.\n")

        print("Archivo actual:\n"
              f"* Nombre: {os.path.basename(path)}\n"
              f"* Tamaño: {current_size}\n")

        print("Archivo nuevo:\n"
              f"* Nombre: {os.path.basename(path)}\n"
              f"* Tamaño: {size}\n")

        print("¿Desea extraer el archivo de todos modos?\n"
              "* 1) No\n"
              "* 2) Sí\n"
              "* 3) Renombrar\n"
              "* 4) No a todo\n"
              "* 5) Sí a todo\n"
              "* 6) Renombrar todo\n")

        output = "0"
        while output not in ("1", "2", "3", "4", "5", "6"):
            output = input(">")

        return int(output)-1

    def make_file(self, file_properties, lexer):
        path = self.get_abspath(file_properties['NAME'])
        size = file_properties['SIZE']
        file_hash = file_properties['HASH']

        if self.interface is None:
            writer = self._write
        else:
            writer = self._write_interface
            self.data['n_file'] += 1

            name = os.path.join(self.__workpath, file_properties['NAME']).decode()
            if name.startswith("./") or name.startswith(".\\"):
                name = name[2:]

            self.interface.update_static_info(
                n_files=self.data['n_file'],
                name=name,
                represent=(100*size/self.data['total_size'])
            )

            self.data['cur_pos'] = 0
            self.data['cur_size'] = size
            self.data['cur_size_format'] = get_size_unit(size)
            self.data['cur_time_start'] = time.time()

            if self.interface is not None:
                self.interface.update()

        if self.message_box is not None:
            if self.message_box == "default":
                self.message_box = self.default_message_box

            if os.path.exists(path):
                if self.verify_file_hashes_before_extract(path, size, file_hash):
                    start_time = time.time()
                    if not self.__apply_message_box['for_all']:
                        respuesta = self.message_box(path, size, file_hash)
                    else:
                        respuesta = self.__apply_message_box['output'] % 3

                    if respuesta in (3, 4, 5):
                        self.__apply_message_box['for_all'] = True
                        self.__apply_message_box['output'] = respuesta % 3
                        respuesta = respuesta % 3

                    end_time = time.time()
                    self.data['cur_time_start'] += end_time-start_time
                    self.data['time_start'] += end_time-start_time
                else:
                    respuesta = 0

                # 0: No extraer
                if respuesta == 0:
                    lexer.ignore_and_advance(size)
                    try:
                        if self.interface is not None:
                            self.data['cur_pos'] += size
                            writer(None, b"")  # Only update info

                    except BaseException as EXC:
                        pass

                    return False
                # 1: Extraer y reemplazar:
                elif respuesta == 1:
                    pass
                # 2: Renombrar:
                elif respuesta == 2:
                    path = self.rename_path(path)

                # Reset the name:
                if self.interface is not None:
                    name = os.path.join(self.__workpath, file_properties['NAME']).decode()
                    if name.startswith("./") or name.startswith(".\\"):
                        name = name[2:]
                    self.interface.value_name['text'] = name

        index_char_amount = file_properties['INDEX_CHAR']
        permission = file_properties['PERMISSION']  # Use this property on Linux.

        filecontent = lexer.iter_to(
            amount=size, buffer=131072)  # Each iteration gets 128KB

        try:
            cancel = False
            with open(path, mode="wb") as f:
                # OnlyFile
                if file_hash is None and index_char_amount in (0, None):
                    for content in filecontent:
                        if not writer(f, content):
                            cancel = True
                            break

                # IndexChar
                elif file_hash is None:
                    for content in filecontent:
                        if not writer(f, index_char(content, index_char_amount)):
                            cancel = True
                            break

                # Hash
                elif index_char_amount in (0, None):
                    hashitem = get_hashitem(file_hash)
                    for content in filecontent:
                        hashitem.update(content)
                        if not writer(f, content):
                            cancel = True
                            break

                    if not compare_hash(hashitem.hexdigest(), file_hash):
                        raise HashError("Hashes don't match. The extracted file will be deleted due to a possible security risk.")

                # Hash & IndexChar
                else:
                    hashitem = get_hashitem(file_hash)
                    for content in filecontent:
                        content = index_char(content, index_char_amount)
                        hashitem.update(content)
                        if not writer(f, content):
                            cancel = True
                            break

                    if not compare_hash(hashitem.hexdigest(), file_hash):
                        raise HashError("Hashes don't match. The extracted file will be deleted due to a possible security risk.")

            # On cancel the operation:
            if cancel:
                os.remove(path)

            try:
                if not os.name in ("nt", "java"):  # On windows and java dont have effect.
                    os.chmod(path, permission)
            except OSError:
                pass

        except PermissionError:
            pass

        except HashError as EXC:
            # Delete the file due to possible security risk
            os.remove(path)
            print("HashError:", path)
            print(EXC)

    def make_dir(self, dir_properties):
        path = os.path.join(self.start_path, dir_properties['NAME'])
        permission = dir_properties['PERMISSION']

        if os.path.exists(path) and os.path.isdir(path):
            return False

        elif permission is None:
            os.mkdir(path)
        else:
            os.mkdir(path, int(permission, base=8))

    def change_workpath(self, workpath_properties):
        new_workpath = workpath_properties['WORK_PATH']

        test = os.path.join(self.start_path, new_workpath)

        if os.path.exists(test) and os.path.isdir(test):
            self.__workpath = new_workpath

    def get_abspath(self, name_of_file_or_dir):
        joined_path = os.path.join(
            self.start_path, self.__workpath, name_of_file_or_dir)
        return os.path.abspath(joined_path)

    def rename_path(self, path):
        filename, ext = os.path.splitext(path)
        n = 2
        test = filename + b" ("+str(n).encode()+b")" + ext
        while os.path.exists(test):
            n += 1
            test = filename + b" ("+str(n).encode()+b")" + ext

        return test

    def _write(self, fileopen, content):
        fileopen.write(content)
        return True

    def _write_interface(self, fileopen, content):
        if self.interface.cancel:
            return False

        if not content == b"":
            fileopen.write(content)

        # current:
        len_content = len(content)
        self.data['cur_pos'] += len_content
        self.data['cur_seconds'] = time.time() - self.data['cur_time_start']
        cur_total_time = ((self.data['cur_size'] * self.data['cur_seconds']) / max(1, self.data['cur_pos']))
        # total
        pos = self.filedata.pos
        total = self.data['total_size']

        prev_seconds = self.data['seconds']
        seconds = self.data['seconds'] = time.time() - self.data['time_start']
        remain = ((total * seconds) / max(1, pos))
        if (seconds-prev_seconds) != 0:
            speed = len_content * 1/(seconds-prev_seconds)
        else:
            speed = 0

        # update:
        self.interface.update_info(
            tot_proc=get_size_unit(pos),
            tot_total_proc=self.data['total_size_format'],
            tot_percent=(pos*100)/max(1, total),
            tot_time=get_time_format(seconds),
            tot_remain_time=get_time_format(remain-seconds),
            speed=get_size_unit(speed),
            cur_proc=get_size_unit(self.data['cur_pos']),
            cur_total_proc=self.data['cur_size_format'],
            cur_percent=(self.data['cur_pos']*100)/max(1, self.data['cur_size']),
            cur_time=get_time_format(self.data['cur_seconds']),
            cur_time_total=get_time_format(cur_total_time)
        )
        self.interface.update()
        return True

#####################################################################################################
#                                                                                                   #
#   FUNCTIONS:                                                                                      #
#                                                                                                   #
#####################################################################################################


def index_char(content: bytes, amount: int = 0):
    amount = amount % 256
    if amount == 0:
        return content

    out = b""
    for old in content:
        new = (old+amount)
        out += bytes((new,))

    return out


def get_hashitem(hashbase: bytes, openhash=True):
    if hashbase is None:
        if openhash:
            return hashlib.sha3_256(b'')
        else:
            return hashlib.sha3_256

    hashbase = hashbase.split(b":")[0].lower().replace(b"_", b"").replace(b"-", b"")

    hashdict = {
        b'3ff': hashlib.sha3_256,
        b'3224': hashlib.sha3_224,
        b'3256': hashlib.sha3_256,
        b'3384': hashlib.sha3_384,
        b'3512': hashlib.sha3_512,
        b'ff':  hashlib.sha256,
        b'224': hashlib.sha224,
        b'256': hashlib.sha256,
        b'384': hashlib.sha384,
        b'512': hashlib.sha512,
        b'1':   hashlib.sha1,
        b'md5': hashlib.md5,
        b'5':   hashlib.md5,
    }

    use = hashdict.get(hashbase, hashlib.sha3_256)
    if openhash:
        return use(b"")
    else:
        return use


def compare_hash(hash1, hash2):
    if isinstance(hash1, bytes):
        hash1 = hash1.split(b":")[-1]

    elif isinstance(hash1, str):
        hash1 = hash1.encode().split(b":")[-1]

    if isinstance(hash2, bytes):
        hash2 = hash2.split(b":")[-1]

    elif isinstance(hash2, str):
        hash2 = hash2.encode().split(b":")[-1]

    if hash1.upper() == hash2.upper():
        return True
    else:
        return False


def get_size_unit(size):
    unit = "B"
    div = 1
    if size > 1073741824:
        unit = "GB"
        div = 1073741824

    elif size > 1048576:
        unit = "MB"
        div = 1048576

    elif size > 1024:
        unit = "KB"
        div = 1024

    else:
        return f"{size} B"

    return f"{size/div:2.2f} {unit}"


def get_time_format(seconds):
    hours, seconds = divmod(int(seconds), 3600)
    minutes, seconds = divmod(seconds, 60)

    return f"{hours:2d}:{minutes:02d}:{seconds:02d}"

#####################################################################################################
#                                                                                                   #
#   TEST:                                                                                           #
#                                                                                                   #
#####################################################################################################


if __name__ == '__main__':
    fd = FileData("./demo.xcif", [])
    fi = FileIter(fd)
    lx = Lexer(fi)
    pr = Parser(lx)
    pr.start(path="../extract_demo")
