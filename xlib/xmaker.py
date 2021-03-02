# XLIB > xmaker.py
# 03:24 p.m. 03/11/2020
# Medina Dylan
# XMaker (Creador de archivos XCIF)
import os
import getpass
import glob
import hashlib
import time

try:
    from . import xparser
except ImportError:
    try:
        from xlib import xparser
    except ImportError:
        import xparser

#####################################################################################################
#                                                                                                   #
#   WALKER: Realiza la exploración de los archivos y carpetas.                                      #
#                                                                                                   #
#####################################################################################################


class Walker():
    def __init__(self, include_paths, exclude_paths, exclude_ext):
        self.include = include_paths
        self.exclude_paths = self.prepare_excludes(exclude_paths)
        self.exclude_ext = self.prepare_ext(exclude_ext)

    def prepare_excludes(self, exclude_paths, use_glob=True):
        out = []
        for i in exclude_paths:
            if isinstance(i, bytes):
                i = i.decode()

            if "*" in i and use_glob:
                for path in glob.glob(i):
                    out.append(os.path.abspath(path).lower())
            else:
                out.append(os.path.abspath(i).lower())

        return out

    def prepare_ext(self, exclude_ext):
        out = []
        for i in exclude_ext:
            if isinstance(i, bytes):
                i = i.decode()

            if not i.startswith("."):
                i = "."+i

            out.append(i.lower())

        return out

    def walk(self):
        for inc in self.include:
            inc = os.path.abspath(inc)
            if (inc.lower() in self.exclude_paths) or \
                    os.path.splitext(inc.lower())[1] in self.exclude_ext:
                continue

            if os.path.isfile(inc):
                yield "", [os.path.basename(inc)], os.path.dirname(inc)
            else:
                inc_dir = os.path.dirname(inc)
                cut = len(inc_dir+"/")
                for path, files in self._walk(inc, self.exclude_paths, self.exclude_ext):
                    yield os.path.abspath(path)[cut:], files, inc_dir

    def _walk(self, path, exclude_paths, exclude_ext):
        try:
            files = []
            dirs = []
            for i in os.listdir(path):
                fpath = os.path.join(path, i)
                if (fpath.lower() in exclude_paths) or \
                        os.path.splitext(fpath.lower())[1] in exclude_ext:
                    continue

                if os.path.isfile(fpath):
                    files.append(i)

                else:
                    dirs.append(fpath)

            yield path, files
            for i in dirs:
                for path_to_yield, files_to_yield in self._walk(i, exclude_paths, exclude_ext):
                    yield path_to_yield, files_to_yield

        except OSError:
            pass


#####################################################################################################
#                                                                                                   #
#   FILEMAKER: Realiza la creación del archivo XCIF.                                                #
#                                                                                                   #
#####################################################################################################


class FileMaker():
    def __init__(self, file: str, walker: Walker, methods: list, hashlib_method=b"3_384", **kwargs):
        self.__walker = walker
        self.__methods = methods
        self.__encrypt = False
        self.__filename = file
        self.__open = None
        self.data = None
        self.version = 1.0
        self.buffer = 8192*4
        self.author = kwargs.get("author", getpass.getuser())
        self.comment = kwargs.get("comment", None)
        self.interface = kwargs.get("interface", None)
        self.__hash = xparser.get_hashitem(hashlib_method, openhash=False)
        self.__walker.exclude_paths.append(file)

    def detect_hash(self, hashfunction):
        hashdict = {
            b'3_224': hashlib.sha3_224,
            b'3_256': hashlib.sha3_256,
            b'3_384': hashlib.sha3_384,
            b'3_512': hashlib.sha3_512,
            b'224': hashlib.sha224,
            b'256': hashlib.sha256,
            b'384': hashlib.sha384,
            b'512': hashlib.sha512,
            b'1':   hashlib.sha1,
            b'md5': hashlib.md5,
        }
        for k, v in hashdict.items():
            if v == hashfunction:
                return k

    def write(self, value: bytes, use_methods=True):
        if self.__open is None:
            raise OSError("The file is not open.")

        if self.__encrypt == True and value != b"" and use_methods:
            for method in self.__methods:
                value = method.encrypt(value)

            self.__open.write(value)
        else:
            self.__open.write(value)

    def open(self):
        self.__open = open(self.__filename, "wb")

    def close(self):
        self.__open.close()

    def write_header(self):
        methods_id = "0000"
        for method in self.__methods:
            methods_id = (methods_id+str(method.ID))[-4:]

        header = "XCIF-File"

        if self.comment is not None:
            header += f"-c{self.comment.replace('-', '--')}-f"

        if len(self.__methods) == 0:
            header += " -s"
        else:
            header += f" -o{methods_id}-f"

        header += f" -u{self.author.replace('-', '--')}-f -v{float(self.version)}-f\n"

        self.write(header.encode())

    def write_start_files(self):
        self.__encrypt = (len(self.__methods) >= 1)
        self.write(b"-x")

    def write_stop_files(self):
        self.write(b"-z")

    def automatic(self):
        self.open()
        self.write_header()
        self.write_start_files()

        if self.interface:
            self.interface.show()
            self.apply_walk_interface()
        else:
            self.apply_walk()

        self.write_stop_files()
        self.close()

        if self.interface:
            if self.interface.cancel:
                if os.path.exists(self.__filename):
                    os.remove(self.__filename)
                return None
            else:
                self.interface.end()

    def write_file(self, filename):
        name = os.path.basename(filename).replace("-", "--")
        size = os.path.getsize(filename)

        hashname = self.detect_hash(self.__hash)
        if hashname is None:
            self.__hash = hashlib.sha3_256
            hashname = b"3_256"

        hashfile = self.__hash()
        with open(filename, "rb") as f:
            line = f.read(self.buffer)
            while line != b"":
                hashfile.update(line)
                line = f.read(self.buffer)

        line = f"-n{name}-f-t{size}-f-h{hashname.decode()}:{str(hashfile.hexdigest()).replace('-', '--')}-f-a"
        self.write(line.encode())

        with open(filename, "rb") as f:
            line = f.read(self.buffer)
            while line != b"":
                self.write(line)
                line = f.read(self.buffer)

        self.write(b"-f\n")

    def write_file_interface(self, filename):
        name = os.path.basename(filename).replace("-", "--")
        size = os.path.getsize(filename)

        hashname = self.detect_hash(self.__hash)
        if hashname is None:
            self.__hash = hashlib.sha3_256
            hashname = b"3_256"

        hashfile = self.__hash()
        with open(filename, "rb") as f:
            line = f.read(self.buffer)
            while line != b"":
                hashfile.update(line)
                line = f.read(self.buffer)
                self.interface.update()

        line = f"-n{name}-f-t{size}-f-h{hashname.decode()}:{str(hashfile.hexdigest()).replace('-', '--')}-f-a"
        self.write(line.encode())

        size_format = get_size_unit(size)
        proc, total_proc, total_size = 0,  self.data['current_total_size'], self.data['total_size']
        time_start = self.data['time_start']
        current_time_start = time.time()
        seconds = time.time()-time_start
        speed = 0

        with open(filename, "rb") as f:
            line = f.read(self.buffer)
            while line != b"":
                self.write(line)
                # Update interface:
                len_line = len(line)
                proc += len_line
                total = total_proc+proc

                prev_seconds = seconds
                cur_seconds = time.time()-current_time_start
                seconds = time.time()-time_start

                remain = ((total_size * seconds) / total)
                cur_total_time = ((size * cur_seconds) / proc)

                if (seconds-prev_seconds) != 0:
                    speed = len_line * 1/(seconds-prev_seconds)

                if self.interface.cancel:
                    return None

                self.interface.update_info(
                    tot_proc=get_size_unit(total),
                    tot_total_proc=self.data['total_size_format'],
                    tot_percent=(total*100)/max(1, total_size),
                    tot_time=get_time_format(seconds),
                    tot_remain_time=get_time_format(remain-seconds),
                    speed=get_size_unit(speed),
                    cur_proc=get_size_unit(proc),
                    cur_total_proc=size_format,
                    cur_percent=(proc*100)/max(1, size),
                    cur_time=get_time_format(cur_seconds),
                    cur_time_total=get_time_format(cur_total_time)
                )
                self.interface.update()
                # update:
                line = f.read(self.buffer)

        self.data['current_total_size'] += proc
        self.write(b"-f\n")

    def write_folder(self, dirname):
        line = f"-d{(dirname).replace('-', '--')}-f\n"
        self.write(line.encode())

    def write_change_folder(self, dirname):
        line = f"-r{(dirname).replace('-', '--')}-f\n"
        self.write(line.encode())

    def apply_walk(self):
        for path, files, basepath in self.__walker.walk():
            if path != "":
                self.write_folder(path)  # os.path.join(basepath, path))
                self.write_change_folder(path)
            else:
                self.write_change_folder(".")

            for filename in files:
                full = os.path.join(basepath, path, filename)
                self.write_file(full)

    def apply_walk_interface(self):
        total_size = 0
        total_files = 0

        for path, files, basepath in self.__walker.walk():
            for filename in files:
                try:
                    full = os.path.join(basepath, path, filename)
                    total_size += os.path.getsize(full)
                    total_files += 1
                except OSError:
                    pass
            self.interface.update()

        self.data = {
            'time_start': time.time(),
            'total_size': total_size,
            'total_size_format': get_size_unit(total_size),
            'total_files': total_files,
            'current_total_file': 0,
            'current_total_size': 0,
        }

        for path, files, basepath in self.__walker.walk():
            if path != "":
                self.write_folder(path)  # os.path.join(basepath, path))
                self.write_change_folder(path)
            else:
                self.write_change_folder(".")

            for filename in files:
                try:
                    self.interface.update()
                    full = os.path.join(basepath, path, filename)
                    size = os.path.getsize(full)
                    self.data['current_total_file'] += 1

                    self.interface.update_static_info(
                        name=os.path.join(path, filename),
                        n_files=self.data['current_total_file'],
                        n_total_files=total_files,
                        represent=(100*size/total_size)
                    )
                    self.write_file_interface(full)

                    if self.interface.cancel:
                        return None
                except OSError:
                    pass


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


if __name__ == "__main__":
    my_walker = Walker('.', ["./demo.xcif"], [])
    fmaker = FileMaker("demo.xcif", my_walker, [])
    fmaker.automatic()
