# XLIB > XCIF
# 05:16 p.m. 21/09/2020
# Medina Dylan
# XCIF (X-Cifrado)
import random

try:
    from . import xparser
except ImportError:
    try:
        from xlib import xparser
    except ImportError:
        import xparser

try:
    from . import xhash
except ImportError:
    try:
        from xlib import xhash
    except ImportError:
        import xhash

try:
    from . import xmaker
except ImportError:
    try:
        from xlib import xmaker
    except ImportError:
        import xmaker
#####################################################################################################
#                                                                                                   #
#   METODOS DE CIFRADO                                                                              #
#                                                                                                   #
#####################################################################################################


class BaseMethod(object):
    def __init__(self, myhash, **kwargs):
        self.myhash = myhash
        self.active = True
        self.ID = 0
        self.extra_data = kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}(ID={self.ID}, myhash={self.myhash})"

    def restart(self):
        pass

    def decrypt(self, data):
        return data

    def encrypt(self, data):
        return data


class MethodShuffle(BaseMethod):
    def __init__(self, myhash, **kwargs):
        super(MethodShuffle, self).__init__(myhash, **kwargs)

        self.__charlist = xhash.get_table_of_characters(
            self.myhash['base_hash'], self.myhash['len'], self.myhash['my_hash'])

        self.ID = 1

    def decrypt(self, data):
        if not self.active:
            return data
        else:
            output = b""
            for i in data:
                output += self.__charlist[i]

            return output

    def encrypt(self, data):
        if not self.active:
            return data
        else:
            output = b""
            for i in data:
                char = bytes((i,))
                output += bytes((self.__charlist.index(char),))

            return output


class MethodAdd(BaseMethod):
    def __init__(self, myhash, **kwargs):
        super(MethodAdd, self).__init__(myhash, **kwargs)

        random.seed(myhash['len'])
        random.seed(myhash['len'] * random.randint(0, 256))
        self.__amount_list = list((random.randint(0, 64) for i in range(8)))
        self.__amount_pos = 0
        self.__amount_len = len(self.__amount_list)
        self.ID = 2

    def restart(self):
        super().restart()
        self.__amount_pos = 0
        self.__amount_len = len(self.__amount_list)

    def decrypt(self, data):
        if not self.active:
            return data
        else:
            output = b""
            for d in data:
                nro_char = (d - self.__amount_list[self.__amount_pos]) % 256
                output += bytes((nro_char,))
                self.__amount_pos = (self.__amount_pos + 1) % self.__amount_len

            return output

    def encrypt(self, data):
        if not self.active:
            return data
        else:
            output = b""
            for d in data:
                nro_char = (d + self.__amount_list[self.__amount_pos]) % 256
                output += bytes((nro_char,))
                self.__amount_pos = (self.__amount_pos + 1) % self.__amount_len

            return output


class MethodBitsShuffle(BaseMethod):
    def __init__(self, myhash, **kwargs):
        super(MethodBitsShuffle, self).__init__(myhash, **kwargs)

        random.seed(myhash['len'])
        self.__amount_list = list((random.randint(0, 8) for i in range(8)))
        self.__amount_pos = 0
        self.__amount_len = len(self.__amount_list)
        self.ID = 3

    def restart(self):
        super().restart()
        self.__amount_pos = 0
        self.__amount_len = len(self.__amount_list)

    def decrypt(self, data):
        if not self.active:
            return data
        else:
            output = b""
            for i in data:
                nro_bin = bin(i)[2:]
                nro_bin = ("0"*7 + nro_bin)[-8:]
                amount = self.__amount_list[self.__amount_pos]
                nro_bin = nro_bin[8-amount:]+nro_bin[:8-amount]
                output += bytes((int(nro_bin, base=2),))
                self.__amount_pos = (self.__amount_pos + 1) % self.__amount_len

            return output

    def encrypt(self, data):
        if not self.active:
            return data
        else:
            output = b""
            for i in data:
                nro_bin = bin(i)[2:]
                nro_bin = ("0"*7 + nro_bin)[-8:]
                amount = self.__amount_list[self.__amount_pos]
                nro_bin = nro_bin[amount:]+nro_bin[:amount]
                output += bytes((int(nro_bin, base=2),))
                self.__amount_pos = (self.__amount_pos + 1) % self.__amount_len

            return output

#####################################################################################################
#                                                                                                   #
#   XCIF                                                                                            #
#                                                                                                   #
#####################################################################################################


class XCIF():
    def __init__(self, filename: str, hashes: dict = None):
        self.filename = filename
        self.methods = []
        self.hashes = {}
        self.hashlib_method = b"3_256"

        if hashes is not None:
            for k, v in hashes:
                self.add_method(v, k)

    def add_method(self, hash_data, method):
        self.hashes[method] = hash_data
        self._add_method(method)

    def _add_method(self, method):
        add = method(self.hashes[method])
        if isinstance(add, BaseMethod):
            self.methods.append(add)

    def add_methods_by_passwords(self, password1="", password2="", password3=""):

        if len(password1) >= 8:
            self.add_method(
                generate_hash_data(password1),
                MethodShuffle
            )

        if len(password2) >= 8:
            self.add_method(
                generate_hash_data(password2),
                MethodAdd
            )

        if len(password3) >= 8:
            self.add_method(
                generate_hash_data(password3),
                MethodBitsShuffle
            )

    def extract_to(self, path, message_box="default", interface=None):
        filedata = xparser.FileData(self.filename, self.methods)
        fileiter = xparser.FileIter(filedata)
        lex = xparser.Lexer(fileiter)
        par = xparser.Parser(lex)

        for method in self.methods:
            method.restart()

        if isinstance(path, str):
            bytes_path = path.encode()
        elif isinstance(path, bytes):
            bytes_path = path

        par.start(bytes_path, message_box, interface)

    def get_content_files(self):
        filedata = xparser.FileData(self.filename, self.methods)
        fileiter = xparser.FileIter(filedata)
        lex = xparser.Lexer(fileiter)
        par = xparser.Parser(lex)

        for method in self.methods:
            method.restart()

        return par.get_content_list()

    def get_header(self):
        filedata = xparser.FileData(self.filename, self.methods)
        fileiter = xparser.FileIter(filedata)
        lex = xparser.Lexer(fileiter)
        par = xparser.Parser(lex)

        for method in self.methods:
            method.restart()

        return par.get_header()

    def compress_from(self, paths, exclude_paths=None, exclude_ext=None, **kwargs):
        walk = xmaker.Walker(paths, exclude_paths, exclude_ext)
        fmaker = xmaker.FileMaker(self.filename, walk, self.methods, self.hashlib_method, **kwargs)
        fmaker.automatic()


def generate_hash_data(password):
    password = password.encode()
    len_pass = len(password)
    basehash = xhash.get_hash_of_key(password)
    myhash = xhash.get_my_hash(basehash, len_pass)

    return {'base_hash': basehash,
            'len': len_pass,
            'my_hash': myhash}


if __name__ == '__main__':
    x = XCIF('./demo.xcif', {})
    x.add_method(generate_hash_data("Hola mundo"), MethodShuffle)
    x.compress_from(["./extract"], [], [])
    x.extract_to("../extract")
