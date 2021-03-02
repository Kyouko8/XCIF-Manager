# XTK_Viewer
# 03:19 p.m. 24/09/2020
# Medina Dylan
# XTKViewer (Visor de XCIF en Tkinter)

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog as tkfd
from tkinter import messagebox as tkmb
import getpass
import os
import shutil
import subprocess
import time
import math
import hashlib

try:
    from . import xcif
except ImportError:
    try:
        from xlib import xcif
    except ImportError:
        import xcif

try:
    from . import xdata
except ImportError:
    try:
        from xlib import xdata
    except ImportError:
        import xdata

try:
    from .xtkextra import FileEntry, HELP_DICT
except ImportError:
    try:
        from xlib.xtkextra import FileEntry, HELP_DICT
    except ImportError:
        from xtkextra import FileEntry, HELP_DICT

# This code is not mine ;)
# and is not very important.
try:
    from . import iconfiles
except ImportError:
    try:
        from xlib import iconfiles
    except ImportError:
        try:
            import iconfiles
        except ImportError:
            iconfiles = None

IMG_PATH = "./icons"
if not os.path.exists(IMG_PATH):
    IMG_PATH = "../icons"

DATA_PATH = "./data"
if not os.path.exists(DATA_PATH):
    DATA_PATH = "../data"
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

DICT_EXTENSION_IMG_PATH = {
    'accessdb.png': ['.adp', '.adn', '.accdb', '.laccdb', '.accdw', '.accdc', '.accda', '.accdr', '.accdt'],
    'bat.png': ['.bat', '.cmd', '.sh', '.btm', ],
    'compress.png': ['.zip', '.rar', '.7z', '.tar', '.gz', '.xcif', '.bin', '.cab'],
    'database.png': ['.sql', '.sqlite', '.sqlite3', '.db', '.dat', '.bdd'],
    'dll.png': ['.dll', '.lib'],
    'document.png': ['.txt', '.log', '.html', '.htm', '.text', '.plain'],
    'excel.png': ['.xlsx', '.xls', '.csv', '.xlsm', '.xlsb', '.xltx', '.xltm', '.xlt', '.xls'],
    'image.png': ['.png', '.gif', '.tiff', '.bmp', '.dib'],
    'image_jpg.png': ['.jpg', '.jpeg'],
    'isoburn.png': ['.nrg', '.iso', '.cd', '.cue', '.cdz'],
    'java.png': ['.jar', '.java', '.class', '.javaclass'],
    'music.png': ['.wav', '.mp3', '.mp2', '.ogg', '.flac', '.aif', '.aifc', '.aiff', '.mid', '.midi',
                  '.aux', '.cda', '.aac', '.m4a', '.wma'],
    'powerpoint.png': ['.pptx', '.ppt', '.pot', '.potm', '.potx', '.pps', '.ppsm', '.ppsx', '.pptm', ],
    'program.png': ['.exe', '.msi', '.msu'],
    'python.png': ['.py', '.pyc', '.pyw', '.pyd'],
    'settings.png': ['.ini', '.conf', '.xml', '.css'],
    'torrent.png': ['.torrent'],
    'videos.png': ['.mp4', '.mpg', '.mpeg', '.avi', '.3gp', '.mov', '.wmv', '.3gpp'],
    'word.png': ['.doc', '.docx',  '.docm', '.dot', '.dotx', '.rtf'],
    'xcif.png': ['.xcif']
}


class ApplicationFrame(ttk.Frame):
    def __init__(self, root, **kwargs):
        self.init_data = {}
        for i in tuple(kwargs.keys()):
            if i in ("option", "data_option", "exit_after"):
                self.init_data[i] = kwargs.pop(i)

        super().__init__(root, **kwargs)

        self.root = root
        self.root.title("Administrador XCIF v1.0")
        self.root.iconbitmap(f"{DATA_PATH}\\xcif.ico")

        # Files:
        self.recents_filename = os.path.join(DATA_PATH, "recents.xtkv")
        self.config_filename = os.path.join(DATA_PATH, "config.xtkv")

        # Data-Configs:
        self.recents_data = {}
        self.config_data = self.default_configs()
        # Imgs:
        self.image_bitmaps = {'ext': {}, "folder": {}}
        self.recents = {}
        # Buttons Panel
        self.frame_buttons = ttk.LabelFrame(self, text="Acciones")
        self.button1 = ttk.Button(self.frame_buttons, text="Nuevo", command=self.show_new_popup)
        self.button2 = ttk.Button(self.frame_buttons, text="Abrir", command=self.show_open_popup)
        self.button3 = ttk.Button(self.frame_buttons, text="Configuración", command=self.show_settings_popup)
        self.button4 = ttk.Button(self.frame_buttons, text="Acerca de", command=self.show_about_popup)
        self.button5 = ttk.Button(self.frame_buttons, text="Ayuda", command=self.show_help_popup)
        self.button6 = ttk.Button(self.frame_buttons, text="Salir", command=self.quit_app)

        # Recents Files Panel
        self.frame_recents = ttk.LabelFrame(self, text="Archivos usados recientementes")
        self.treeview = ttk.Treeview(self.frame_recents, columns=("date", "path"))
        self.treeview.column("#0", stretch=True, width=300, minwidth=300)
        self.treeview.column("date", anchor="center", stretch=True, width=140, minwidth=140)
        self.treeview.column("path", anchor="w", stretch=True, width=400, minwidth=140)
        self.treeview.heading("#0", text="Nombre")
        self.treeview.heading("date", text="Fecha (últ. acceso)")
        self.treeview.heading("path", text="Ruta")

        self.vsb1 = ttk.Scrollbar(self.frame_recents, command=self.treeview.yview)
        self.treeview['yscrollcommand'] = self.vsb1.set

        self.vsb2 = ttk.Scrollbar(self.frame_recents, command=self.treeview.xview, orient="horizontal")
        self.treeview['xscrollcommand'] = self.vsb2.set

        self.treeview.tag_bind("file", "<<TreeviewOpen>>", self.open_recent_filename)
        # Apply config:
        self.load_configs()
        self.configure_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.root.bind("<Key-F1>", lambda _=None, self=self: self.show_help_popup())
        self.root.bind("<Control-Key-1>", lambda _=None, self=self: self.show_new_popup())
        self.root.bind("<Control-Key-2>", lambda _=None, self=self: self.show_open_popup())
        self.root.bind("<Control-Key-3>", lambda _=None, self=self: self.show_settings_popup())
        self.root.bind("<Control-Key-4>", lambda _=None, self=self: self.show_about_popup())
        self.root.bind("<Control-Key-5>", lambda _=None, self=self: self.show_help_popup())
        self.root.bind("<Control-Key-9>", lambda _=None, self=self: self.quit_app())
        self.root.bind("<Control-Key-N>", lambda _=None, self=self: self.show_new_popup())
        self.root.bind("<Control-Key-n>", lambda _=None, self=self: self.show_new_popup())
        self.root.bind("<Control-Key-O>", lambda _=None, self=self: self.show_open_popup())
        self.root.bind("<Control-Key-o>", lambda _=None, self=self: self.show_open_popup())
        self.root.bind("<Control-Key-S>", lambda _=None, self=self: self.show_settings_popup())
        self.root.bind("<Control-Key-s>", lambda _=None, self=self: self.show_settings_popup())
        self.root.bind("<Control-Key-A>", lambda _=None, self=self: self.show_about_popup())
        self.root.bind("<Control-Key-a>", lambda _=None, self=self: self.show_about_popup())
        self.root.bind("<Control-Key-H>", lambda _=None, self=self: self.show_help_popup())
        self.root.bind("<Control-Key-h>", lambda _=None, self=self: self.show_help_popup())

        self.after(150, self.use_init_data)

    def use_init_data(self, _=None):
        self.root.update()
        data = self.init_data

        if "option" in data:
            commands = {'new': self.show_new_popup, 'open': self.show_open_popup,
                        'settings': self.show_settings_popup, 'about': self.show_about_popup}

            if data["option"] in commands:
                command = commands[data["option"]]
                if command in (self.show_new_popup, self.show_open_popup):
                    command(data.get("data_option", None))

                if data.get("exit_after", False):
                    print("Quit!")
                    return self.quit_app()

            else:
                tkmb.showerror("Datos de inicio:", "Se ha introducido una orden de inicio no reconocida.")

    def load_configs(self):
        if os.path.exists(self.recents_filename):
            self.recents_data = {}
            for k, v in xdata.load_config(self.recents_filename).items():
                k = os.path.abspath(k)
                if os.path.exists(k) and k not in self.recents_data:
                    self.recents_data[k] = int(v)
                    self.add_to_recent_files(path=k, time=int(v))

        if os.path.exists(self.config_filename):
            data = xdata.load_config(self.config_filename)
            self.config_data['hash'] = int(data.get('hash', self.config_data['hash']))

    def save_configs(self):
        xdata.save_config(self.recents_filename, self.recents_data)
        xdata.save_config(self.config_filename, self.config_data)

    def default_configs(self):
        return {"hash": 3256}

    def configure_layout(self):
        width, height = self.winfo_width(), self.winfo_height()

        if (width, height) == (1, 1):  # The size is incorrect :(
            return False

        button_height = 32
        button_width = 180

        self.frame_buttons.place(x=10, y=10, width=20+button_width, height=height-20)

        self.button1.place(x=8, y=2, width=button_width, height=button_height)
        self.button2.place(x=8, y=38, width=button_width, height=button_height)
        self.button3.place(x=8, y=74, width=button_width, height=button_height)
        self.button4.place(x=8, y=110, width=button_width, height=button_height)
        self.button5.place(x=8, y=146, width=button_width, height=button_height)
        self.button6.place(x=8, y=height-48-button_height,
                           width=button_width, height=button_height)

        self.frame_recents.place(x=40+button_width, y=10, width=width-50-button_width, height=height-20)
        self.treeview.place(x=8, y=2, width=width-90-button_width, height=height-70)
        self.vsb1.place(x=width-80-button_width, y=2, height=height-70)
        self.vsb2.place(x=8, y=height-66, width=width-90-button_width,)

    def get_default_icons(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                if self.image_bitmaps["folder"].get("normal", None) is None:
                    self.image_bitmaps['folder']["normal"] = tk.PhotoImage(file=f"{IMG_PATH}/folder.png")

                return self.image_bitmaps['folder']["normal"]
            else:
                ext = os.path.splitext(path)[1].lower()
                bitmap = self.image_bitmaps['ext'].get(ext, None)
                if bitmap is None:
                    image = f"{IMG_PATH}/file.png"
                    for k, v in DICT_EXTENSION_IMG_PATH.items():
                        if ext in v:
                            image = f"{IMG_PATH}/{k}"
                    self.image_bitmaps['ext'][ext] = tk.PhotoImage(file=image)

                return self.image_bitmaps['ext'][ext]

    def get_icon(self, path):
        if iconfiles is None:
            return self.get_default_icons(path)

        try:
            path = path.replace("/", "\\")
            if os.path.exists(path):
                if os.path.splitext(path)[-1].lower() == ".xcif":
                    return self.get_default_icons(path)

                if os.path.isdir(path):
                    if self.image_bitmaps["folder"].get(path.lower(), None) is None:
                        img = iconfiles.get_icon(path)
                        self.image_bitmaps['folder'][path.lower()] = iconfiles.convert_to_tkimage(img)

                    return self.image_bitmaps['folder'][path.lower()]
                else:
                    ext = os.path.splitext(path)[1].lower()
                    bitmap = self.image_bitmaps['ext'].get(ext, None)
                    if bitmap is None:
                        img = iconfiles.get_icon(path)
                        self.image_bitmaps['ext'][ext] = iconfiles.convert_to_tkimage(img)

                    return self.image_bitmaps['ext'][ext]

        except BaseException:
            return self.get_default_icons(path)

    def reset_icons(self):
        self.image_bitmaps['ext'].clear()
        self.image_bitmaps['folder'].clear()

    def show_about_popup(self):
        popup = PopUpMessage(self.root)
        popup.set_title('Acerca de')
        popup.set_text("Administrador de Archivos XCIF\n"
                       "Autor: Medina Dylan\n"
                       "Versión del Administrador de Archivos: 1.0\n"
                       "Versión de XCIF: 1.0\n\n"
                       "Este programa permite la creación de archivos XCIF, "
                       "dichos ficheros permiten proteger con contraseña los "
                       "archivos y carpetas que haya en su interior.")
        popup.show()

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Administrador de Archivos XCIF:\n\n"+HELP_DICT['PRINCIPAL'])
        popup.show()

    def show_settings_popup(self):
        popup = PopUpAppSettings(self.root, self)
        popup.set_title('Configuraciones')
        popup.show()

        if popup.data is not None:
            for k, v in popup.data[0].items():
                self.config_data[k] = v

        self.save_configs()

    def show_open_popup(self, data=None):
        popup1 = PopUpLoad(self.root, self, data)
        popup1.set_title('Extraer archivo XCIF')
        popup1.show()

        if popup1.data is None:
            return None

        data = popup1.data
        path = data[0]['xcif_file']

        self.recents_data[path] = int(time.time())
        self.save_configs()

        popup_loading = PopUpLoadingXCIF(self.root, self, path, data[0]['save_as'])
        popup_loading.set_title('Descifrando: {xcif_file}'.format(**data[0]))

        load = xcif.XCIF(path, {})
        load.add_methods_by_passwords(**data[1])
        try:
            load.extract_to(
                path=data[0]['save_as'],
                message_box=lambda path, size, filehash, root=popup_loading.top:
                PopUpConfirmReplace.as_message_box(path, size, filehash, root),
                interface=popup_loading,
            )
        except Exception as EXC:
            tkmb.showerror(
                "Error:",
                "Un error ha ocurrido al intentar descifrar el archivo.\nCompruebe:\n"
                "\n* Que las contraseñas fueron correctamente escritas"
                "(mayúsculas, minúsculas, números y orden de las mismas)."
                "\n* Que el archivo no está dañado."
                "\n* Que hay permiso de escritura en el directorio seleccionado."
                "\n* Que el programa tiene los permisos suficientes para realizar esta operación."
            )
            popup_loading.cancel_command(force=True)
            print(type(EXC).__name__, EXC)
            return self.show_open_popup(data)

        self.add_to_recent_files(path=path, time=self.recents_data[path])
        # On cancel:
        if popup_loading.cancel:
            return None

        tkmb.showinfo("Fin", "Finalizó el proceso.")
        popup_loading.wait()

    def show_new_popup(self, data=None):
        popup1 = PopUpSave(self.root, self, data)
        popup1.set_title('Crear Nuevo Archivo XCIF')
        popup1.show()

        if popup1.data is None:
            return None

        data = popup1.data
        path = data[1]['save_as']

        self.recents_data[path] = int(time.time())
        self.save_configs()

        popup_saving = PopUpSavingXCIF(self.root, self, path)
        popup_saving.set_title('Cifrando: {save_as}'.format(**data[1]))

        new = xcif.XCIF(path, {})
        new.hashlib_method = self.get_hash(self.config_data.get("hash"))
        new.add_methods_by_passwords(**data[2])
        new.compress_from(
            paths=data[0]['paths'],
            exclude_paths=data[0]['exclude_paths'],
            exclude_ext=data[0]['exclude_ext'],
            comment=data[1]['comment'],
            author=data[1]['author'],
            interface=popup_saving,
        )

        self.add_to_recent_files(path=path, time=self.recents_data[path])
        # On cancel:
        if popup_saving.cancel:
            return None

        tkmb.showinfo("Fin", "Finalizó el proceso.")
        popup_saving.wait()

    def get_hash(self, hashnumber):
        dict_hash = {
            1: b'1',
            5: b'md5',
            224: b'224',
            256: b'256',
            384: b'384',
            512: b'512',
            3224: b'3_224',
            3256: b'3_256',
            3384: b'3_384',
            3512: b'3_512',
        }

        return dict_hash.get(hashnumber, b"3_256")

    def open_recent_filename(self, _=None):
        for path in self.treeview.selection():
            if os.path.exists(path):
                self.show_open_popup(
                    data=[{'xcif_file': path}, {}]
                )

            break

    def quit_app(self):
        self.save_configs()
        self.root.destroy()
        self.root.quit()

    def add_to_recent_files(self, **data):
        path = os.path.abspath(data.get("path", "???"))

        if os.path.exists(path) and data.get("time", 0):
            self.recents[path] = data["time"]
            self.insert_recent_files(path)

    def insert_recent_files(self, *paths):
        for path in paths:
            if not self.treeview.exists(path):
                self.treeview.insert(
                    "",
                    -1,
                    text=os.path.basename(path),
                    values=(get_datetime_format(self.recents[path]), path),
                    tag=("file",),
                    iid=path
                )
                self.treeview.item(path, image=self.get_icon(path))

        pos = 0
        for i in sorted(self.recents.items(),
                        key=lambda x: x[1], reverse=True):
            self.treeview.move(i[0], "", pos)
            pos += 1


class PopUp():
    def __init__(self, root):
        self.root = root
        self.top = tk.Toplevel(self.root)
        self.top.resizable(False, False)
        self.top.bind("<Key-F1>", lambda _=None, self=self: self.show_help_popup())

    def set_title(self, title):
        self.top.iconbitmap(f"{DATA_PATH}\\xcif.ico")
        self.top.title(title)

    def set_geometry(self, size):
        if isinstance(size, str):
            size = size.split("x", 1)

        width = int(size[0])
        height = int(size[1])

        max_width, max_height = self.top.maxsize()

        self.top.geometry("{wid}x{hei}+{posx}+{posy}".format(
            wid=width,
            hei=height,
            posx=int((max_width-width)/2),
            posy=int((max_height-height)/2)
        ))

    def show_help_popup(self):  # This will be replace
        pass


class PopUpHelp(PopUp):
    def __init__(self, root):
        super().__init__(root)
        self.set_geometry("620x414")

        self.filename_size = f"{DATA_PATH}\\font.xtkv"
        if os.path.exists(self.filename_size):
            self.font_data = xdata.load_config(f"{DATA_PATH}\\font.xtkv")
        else:
            self.font_data = {"size": 9}

        self.button_size_up = ttk.Button(self.top, text="+", command=self.size_up)
        self.button_size_down = ttk.Button(self.top, text="-", command=self.size_down)
        self.check_size()
        self.scrolledtext = ScrolledText(self.top, state="disabled", wrap="word", font=self.get_font())
        self.button_close = ttk.Button(self.top, text="Cerrar", command=self.top.destroy)

        self.top.bind("<Key-Return>", lambda _=None, self=self: self.button_close.invoke())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.button_close.invoke())

    def show(self):
        self.scrolledtext.place(x=10, y=10, width=600, height=360)
        self.button_close.place(x=260, y=380, width=100, height=24)
        self.button_size_down.place(x=10, y=380, width=24, height=24)
        self.button_size_up.place(x=44, y=380, width=24, height=24)

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def save_config(self):
        xdata.save_config(f"{DATA_PATH}\\font.xtkv", self.font_data)

    def set_text(self, text):
        self.scrolledtext.config(state="normal")
        self.scrolledtext.delete("1.0", tk.END)
        self.scrolledtext.insert(tk.END, text)
        self.scrolledtext.config(state="disabled")

    def get_font(self):
        return "Courier New", int(self.font_data['size'])

    def check_size(self):
        self.font_data['size'] = size = min(48, max(7, int(self.font_data['size'])))
        if size == 7:
            self.button_size_down.configure(state="disabled")
        else:
            self.button_size_down.configure(state="normal")
        if size == 48:
            self.button_size_up.configure(state="disabled")
        else:
            self.button_size_up.configure(state="normal")

    def size_up(self):
        self.font_data['size'] = min(48, max(7, int(self.font_data['size']) + 1))
        self.scrolledtext.config(font=self.get_font())
        self.save_config()
        self.check_size()

    def size_down(self):
        self.font_data['size'] = min(48, max(7, int(self.font_data['size']) - 1))
        self.scrolledtext.config(font=self.get_font())
        self.save_config()
        self.check_size()

    @staticmethod
    def from_message(title, text, root):
        popup = PopUpHelp(root)
        popup.set_title(title)
        popup.set_text(text)
        popup.show()
        return popup


class PopUpMessage(PopUpHelp):
    def __init__(self, root):
        super().__init__(root)
        self.set_geometry("420x214")

    def show(self):
        self.scrolledtext.place(x=10, y=10, width=400, height=160)
        self.button_close.place(x=160, y=180, width=100, height=24)
        self.button_size_down.place(x=10, y=180, width=24, height=24)
        self.button_size_up.place(x=44, y=180, width=24, height=24)

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    @staticmethod
    def from_message(title, text, root):
        popup = PopUpMessage(root)
        popup.set_title(title)
        popup.set_text(text)
        popup.show()
        return popup


class PopUpEntry(PopUp):
    def __init__(self, root):
        super().__init__(root)
        self.set_geometry("420x100")

        self.data = None
        self.label = ttk.Label(self.top, text="Ingrese el dato solicitado:")
        self.entry = ttk.Entry(self.top)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_ok = ttk.Button(self.top, text="Aceptar", command=self.ok_command)

        self.top.bind("<Key-Return>", lambda _=None, self=self: self.button_ok.invoke())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.button_cancel.invoke())

    def show(self):
        self.label.place(x=10, y=10, width=400, height=24)
        self.entry.place(x=10, y=40, width=400, height=24)
        self.button_cancel.place(x=240, y=70, width=80, height=24)
        self.button_ok.place(x=330, y=70, width=80, height=24)

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def set_text(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def ok_command(self):
        self.data = self.entry.get()
        self.top.destroy()

    @staticmethod
    def ask(title, text, root, value=""):
        popup = PopUpEntry(root)
        popup.set_title(title)
        popup.label['text'] = text
        popup.set_text(value)
        popup.show()
        return popup


class PopUpEntryText(PopUp):
    def __init__(self, root):
        super().__init__(root)
        self.set_geometry("420x244")

        self.data = None
        self.label = ttk.Label(self.top, text="Ingrese el dato solicitado:")
        self.scrolledtext = ScrolledText(self.top, state="normal", wrap="word")
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_ok = ttk.Button(self.top, text="Aceptar", command=self.ok_command)

        self.top.bind("<Key-Return>", lambda _=None, self=self: self.button_ok.invoke())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.button_cancel.invoke())

    def show(self):
        self.label.place(x=10, y=10, width=400, height=24)
        self.scrolledtext.place(x=10, y=40, width=400, height=160)
        self.button_cancel.place(x=240, y=204, width=80, height=24)
        self.button_ok.place(x=330, y=204, width=80, height=24)

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def set_text(self, text):
        self.scrolledtext.delete("1.0", tk.END)
        self.scrolledtext.insert(tk.END, text)

    def ok_command(self):
        self.data = self.scrolledtext.get("1.0", tk.END)
        self.top.destroy()

    @staticmethod
    def ask(title, text, root, value=""):
        popup = PopUpEntryText(root)
        popup.set_title(title)
        popup.label['text'] = text
        popup.set_text(value)
        popup.show()
        return popup


class FramePasswords(ttk.Frame):
    def __init__(self, root, app, parent):
        super().__init__(root)
        self.top = self
        self.data = None
        self.root = root
        self.app = app
        self.parent = parent

        self.password_char = "\u2022"

        self.label1 = ttk.Label(self.top, text="Clave 1:")
        self.var1 = tk.IntVar(self.top, value=0)
        self.check1 = ttk.Checkbutton(self.top, text="Mostrar", variable=self.var1,
                                      command=self.change_visibility_password1,)
        self.entry1 = ttk.Entry(self.top, text="", show=self.password_char)
        self.entry1.bind("<Key-Return>", self.password1_return_key)
        self.select_file1 = ttk.Button(self.top, text="Usar Archivo", command=self.set_password1)

        self.label2 = ttk.Label(self.top, text="Clave 2:")
        self.var2 = tk.IntVar(self.top, value=0)
        self.check2 = ttk.Checkbutton(self.top, text="Mostrar", variable=self.var2,
                                      command=self.change_visibility_password2,)
        self.entry2 = ttk.Entry(self.top, text="", show=self.password_char)
        self.entry2.bind("<Key-Return>", self.password2_return_key)
        self.select_file2 = ttk.Button(self.top, text="Usar Archivo", command=self.set_password2)

        self.label3 = ttk.Label(self.top, text="Clave 3:")
        self.var3 = tk.IntVar(self.top, value=0)
        self.check3 = ttk.Checkbutton(self.top, text="Mostrar", variable=self.var3,
                                      command=self.change_visibility_password3,)
        self.entry3 = ttk.Entry(self.top, text="", show=self.password_char)
        self.entry3.bind("<Key-Return>", self.password3_return_key)
        self.select_file3 = ttk.Button(self.top, text="Usar Archivo", command=self.set_password3)

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_prev = ttk.Button(self.top, text="Anterior", command=self.prev_tabs)
        self.button_next = ttk.Button(self.top, text="Aceptar", command=self.ok_command)

    def layout(self):
        self.label1.place(x=10, y=10, width=480, height=24)
        self.check1.place(x=495, y=10, width=80, height=24)
        self.entry1.place(x=10, y=40, width=480, height=24)
        self.select_file1.place(x=495, y=40, width=80, height=24)

        self.label2.place(x=10, y=70, width=480, height=24)
        self.check2.place(x=495, y=70, width=80, height=24)
        self.entry2.place(x=10, y=100, width=480, height=24)
        self.select_file2.place(x=495, y=100, width=80, height=24)

        self.label3.place(x=10, y=130, width=480, height=24)
        self.check3.place(x=495, y=130, width=80, height=24)
        self.entry3.place(x=10, y=160, width=480, height=24)
        self.select_file3.place(x=495, y=160, width=80, height=24)

        self.button_help.place(x=235, y=370, width=80, height=24)
        self.button_cancel.place(x=325, y=370, width=80, height=24)
        self.button_prev.place(x=415, y=370, width=80, height=24)
        self.button_next.place(x=505, y=370, width=80, height=24)

    def ok_command(self):
        self.data = {
            'password1': self.entry1.get(),
            'password2': self.entry2.get(),
            'password3': self.entry3.get(),
        }

    def verify(self):
        self.ok_command()
        if self.data:
            return True
        else:
            return False

    def prev_tabs(self):
        self.root.select(1)

    def password1_return_key(self, _=None):
        password = self.entry1.get()
        if len(password) == 0:
            self.button_next.invoke()

        elif len(password) >= 8:
            self.entry2.focus_set()

    def password2_return_key(self, _=None):
        password = self.entry2.get()
        if len(password) == 0:
            self.button_next.invoke()

        elif len(password) >= 8:
            if len(self.entry1.get()) >= 8:
                self.entry3.focus_set()
            else:
                self.entry1.focus_set()

    def password3_return_key(self, _=None):
        password = self.entry3.get()
        if len(password) == 0:
            self.button_next.invoke()

        elif len(password) >= 8:
            if len(self.entry1.get()) >= 8:
                if len(self.entry2.get()) >= 8:
                    self.button_next.invoke()
                else:
                    self.entry2.focus_set()
            else:
                self.entry1.focus_set()

    def change_visibility_password1(self):
        if self.var1.get():
            self.entry1.configure(show="")
        else:
            self.entry1.configure(show=self.password_char)

    def change_visibility_password2(self):
        if self.var2.get():
            self.entry2.configure(show="")
        else:
            self.entry2.configure(show=self.password_char)

    def change_visibility_password3(self):
        if self.var3.get():
            self.entry3.configure(show="")
        else:
            self.entry3.configure(show=self.password_char)

    def get_sha_of_file(self, path):
        sha3 = hashlib.sha3_512(b"")

        with open(path, "rb") as f:
            line = f.read(8192)
            while line != b"":
                sha3.update(line)
                line = f.read(8192)

        return sha3

    def set_password1(self):
        path = tkfd.askopenfilename()
        if os.path.exists(path):
            sha3 = self.get_sha_of_file(path)

            self.entry1.delete(0, len(self.entry1.get()))
            self.entry1.insert(0, sha3.hexdigest().upper())
        else:
            tkmb.showerror("Error", "El archivo seleccionado no existe.")

    def set_password2(self):
        path = tkfd.askopenfilename()
        if os.path.exists(path):
            sha3 = self.get_sha_of_file(path)

            self.entry2.delete(0, len(self.entry2.get()))
            self.entry2.insert(0, sha3.hexdigest().upper())
        else:
            tkmb.showerror("Error", "El archivo seleccionado no existe.")

    def set_password3(self):
        path = tkfd.askopenfilename()
        if os.path.exists(path):
            sha3 = self.get_sha_of_file(path)

            self.entry3.delete(0, len(self.entry3.get()))
            self.entry3.insert(0, sha3.hexdigest().upper())
        else:
            tkmb.showerror("Error", "El archivo seleccionado no existe.")

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Seguridad XCIF:\n\n"+HELP_DICT['CONTRASEÑAS'])
        popup.show()

    def load_data(self, data):
        if 'password1' in data:
            self.entry1.delete(0, len(self.entry1.get()))
            self.entry1.insert(0, data['password1'])

        if 'password2' in data:
            self.entry2.delete(0, len(self.entry2.get()))
            self.entry2.insert(0, data['password2'])

        if 'password3' in data:
            self.entry3.delete(0, len(self.entry3.get()))
            self.entry3.insert(0, data['password3'])


class PopUpSave(PopUp):
    def __init__(self, root, app, data):
        super().__init__(root)
        self.set_geometry("620x450")
        self.app = app
        self.data = None
        # Create widget:
        self.notebook = ttk.Notebook(self.top)

        # Create tabs:
        self.frame_step1 = FrameSaveFileStep1(self.notebook, self.app, self.top)
        self.frame_step2 = FrameSaveFileStep2(self.notebook, self.app, self.top)
        self.frame_step3 = FramePasswords(self.notebook, self.app, self.top)

        # Add tabs:
        self.notebook.add(self.frame_step1, text="Archivos y Carpetas")
        self.notebook.add(self.frame_step2, text="Guardar en")
        self.notebook.add(self.frame_step3, text="Seguridad")

        # Configure tabs:
        self.frame_step1.button_cancel['command'] = self.cancel_command
        self.frame_step2.button_cancel['command'] = self.cancel_command
        self.frame_step3.button_cancel['command'] = self.cancel_command
        self.frame_step3.button_next['command'] = self.ok_command

        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.cancel_command)

        if data is not None:
            self.frame_step1.load_data(data[0])
            self.frame_step2.load_data(data[1])
            self.frame_step3.load_data(data[2])

            if len(data) >= 4:
                if data[3].get('ok_command', False):
                    self.top.after(50, lambda _=None: self.ok_command())

        # Shortcuts
        self.top.bind("<Control-Key-Left>", lambda _=None, self=self: self.key_control_left())
        self.top.bind("<Control-Key-Right>", lambda _=None, self=self: self.key_control_right())
        self.top.bind("<Control-Key-Return>", lambda _=None, self=self: self.key_control_return())
        self.top.bind("<Control-Key-BackSpace>", lambda _=None, self=self: self.key_control_backspace())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.key_escape())
        self.top.bind("<Key-Return>", lambda _=None, self=self: self.key_return())
        self.top.bind("<Key-F1>", lambda _=None, self=self: self.key_f1())

    def layout(self):
        self.notebook.place(x=10, y=10, width=600, height=430)

    def show(self):
        self.layout()
        self.frame_step1.layout()
        self.frame_step2.layout()
        self.frame_step3.layout()

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def ok_command(self):
        self.data = []
        for frame in [self.frame_step1, self.frame_step2, self.frame_step3]:
            if frame.verify():
                self.data.append(frame.data)
            else:
                return self.notebook.select(frame)

        if not (len(self.data[2]['password1']) == 0 or len(self.data[2]['password1']) >= 8):
            return tkmb.showerror(
                "Contraseña 1",
                "La contraseña número 1 no cumple con alguno de los siguientes requisitos:\n"
                "* Tamaño: 8 caracteres."
            )

        elif not (len(self.data[2]['password2']) == 0 or
                  (len(self.data[2]['password2']) >= 8 and
                   len(self.data[2]['password1']) >= 8)):

            return tkmb.showerror(
                "Contraseña 2",
                "La contraseña número 2 no cumple con alguno de los siguientes siguientes requisitos:\n"
                "* Tamaño: 8 caracteres.\n* La 'Contraseña 1' debe estar definida."
            )

        elif not (len(self.data[2]['password3']) == 0 or
                  (len(self.data[2]['password3']) >= 8 and
                   len(self.data[2]['password1']) >= 8 and
                   len(self.data[2]['password2']) >= 8)):

            return tkmb.showerror(
                "Contraseña 3",
                "La contraseña número 3 no cumple con alguno de los siguientes siguientes requisitos:\n"
                "* Tamaño: 8 caracteres.\n* La 'Contraseña 1' debe estar definida.\n"
                "* La 'Contraseña 2' debe estar definida."
            )

        self.top.destroy()

    def cancel_command(self):
        if tkmb.askyesno("Cancelar operación",
                         "¿Desea cancelar la operación actual?"):
            self.data = None
            self.top.destroy()
            return True

    def get_current_frame(self):
        frames = [self.frame_step1, self.frame_step2, self.frame_step3]
        select = self.notebook.select()

        for i in frames:
            if str(i) == str(select):
                return i

    def key_control_left(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

        elif frame == self.frame_step3:
            self.frame_step3.button_next.invoke()

    def key_control_right(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step1:
            self.frame_step1.button_next.invoke()

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

    def key_control_backspace(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

        elif frame == self.frame_step3:
            self.frame_step3.button_next.invoke()

    def key_control_return(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step1:
            self.frame_step1.button_next.invoke()

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

    def key_escape(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        else:
            self.cancel_command()

    def key_return(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step1:
            self.frame_step1.button_next.invoke()

    def key_f1(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame in (self.frame_step1, self.frame_step2, self.frame_step3):
            frame.show_help_popup()


class FrameSaveFileStep1(ttk.Frame):
    def __init__(self, root: ttk.Notebook, app, parent):
        super().__init__(root)
        self.top = self

        self.root = root
        self.app = app
        self.parent = parent

        self.path_dict = {}
        self.exclude_path_dict = {}
        self.exclude_ext_dict = {}
        self._npaths = 0
        self.data = {'paths': [], 'exclude_paths': [], 'exclude_ext': []}

        self.imgs = {'add_file': tk.PhotoImage(file=f"{IMG_PATH}\\file.png")}

        self.label1 = ttk.Label(self.top, text="Seleccione los archivos y carpetas que desea cifrar:")

        self.label_add = ttk.LabelFrame(self.top, text="Añadir")
        self.add_files = ttk.Button(self.label_add, text="Archivos", command=self.add_file)
        self.add_folder = ttk.Button(self.label_add, text="Carpeta", command=self.add_directory)

        self.label_other = ttk.LabelFrame(self.top, text="Otros")
        self.remove = ttk.Button(self.label_other, text="Remover", command=self.remove_paths)

        self.label_sub = ttk.LabelFrame(self.top, text="Excluir")
        self.exclude_files = ttk.Button(self.label_sub, text="Archivos", command=self.add_exclude_file)
        self.exclude_folder = ttk.Button(self.label_sub, text="Carpeta", command=self.add_exclude_directory)
        self.exclude_ext = ttk.Button(self.label_sub, text="Extensión", command=self.add_exclude_ext)

        self.treeview = ttk.Treeview(self.top, columns=("size",))
        self.treeview.column("#0", stretch=True, width=330, minwidth=250)
        self.treeview.column("size", anchor="center", stretch=True, width=128, minwidth=128)
        self.treeview.heading("#0", text="Nombre")
        self.treeview.heading("size", text="Tamaño")

        self.vsb1 = ttk.Scrollbar(self.top, command=self.treeview.yview)
        self.treeview['yscrollcommand'] = self.vsb1.set

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_prev = ttk.Button(self.top, text="Anterior", state=tk.DISABLED)
        self.button_next = ttk.Button(self.top, text="Siguiente", command=self.next_tabs)

        # Shortcut:
        self.parent.bind("<Control-Key-1>", lambda _=None, self=self: self.add_file())
        self.parent.bind("<Control-Key-2>", lambda _=None, self=self: self.add_directory())
        self.parent.bind("<Control-Key-3>", lambda _=None, self=self: self.add_exclude_file())
        self.parent.bind("<Control-Key-4>", lambda _=None, self=self: self.add_exclude_directory())
        self.parent.bind("<Control-Key-5>", lambda _=None, self=self: self.add_exclude_ext())
        self.parent.bind("<Control-Key-6>", lambda _=None, self=self: self.remove_paths())
        self.parent.bind("<Key-Delete>", lambda _=None, self=self: self.remove_paths())

    def layout(self):
        self.label_add.place(x=10, y=10, width=180, height=52)
        self.add_files.place(x=5, y=2, width=80, height=24)
        self.add_folder.place(x=90, y=2, width=80, height=24)

        self.label_sub.place(x=200, y=10, width=265, height=52)
        self.exclude_files.place(x=5, y=2, width=80, height=24)
        self.exclude_folder.place(x=90, y=2, width=80, height=24)
        self.exclude_ext.place(x=175, y=2, width=80, height=24)

        self.label_other.place(x=475, y=10, width=100, height=52,)
        self.remove.place(x=5, y=2, width=80, height=24)

        self.label1.place(x=10, y=70, width=575, height=24)
        self.treeview.place(x=10, y=100, width=555, height=260)
        self.vsb1.place(x=575, y=100, height=260)

        self.button_help.place(x=235, y=370, width=80, height=24)
        self.button_cancel.place(x=325, y=370, width=80, height=24)
        self.button_prev.place(x=415, y=370, width=80, height=24)
        self.button_next.place(x=505, y=370, width=80, height=24)

    def next_tabs(self):
        if self.verify():
            self.root.select(1)

    def get_icon(self, iid):
        if iid in self.path_dict:
            path = self.path_dict.get(iid, ".")
        elif iid in self.exclude_path_dict:
            path = self.exclude_path_dict.get(iid, ".")
        else:
            return None

        self.treeview.item(iid, image=self.app.get_icon(os.path.abspath(path)))

    def insert_paths(self, *newpaths):
        if len(newpaths) >= 1:
            if not self.treeview.exists("include"):
                self.treeview.insert("", 1, text="Archivos y carpetas:", values=("-"), iid="include", open=True)

        for path in newpaths:
            if os.path.exists(path):
                if not path in self.path_dict.values():
                    size_text = self.get_size_text(path)
                    self.treeview.insert("include", -1, text=os.path.basename(path), values=(size_text,), iid=self._npaths)
                    self.path_dict[self._npaths] = path
                    self.get_icon(self._npaths)
                    self._npaths += 1

        pos = 0
        for k, v in sorted(self.path_dict.items(),
                           key=lambda x: (os.path.isfile(x[1]),
                                          os.path.basename(x[1]))):
            self.treeview.move(k, "include", pos)
            if not os.path.exists(v) or v in self.exclude_path_dict.values():
                self.treeview.delete(k)
            else:
                pos += 1

        if pos == 0 and self.treeview.exists("include"):
            self.treeview.delete("include")

    def insert_exclude_paths(self, *newpaths):
        if len(newpaths) >= 1:
            if not self.treeview.exists("exclude"):
                self.treeview.insert("", 2, text="Excluir archivos y carpetas:", values=("-"), iid="exclude", open=True)

        for path in newpaths:
            if os.path.exists(path):
                if not path in self.exclude_path_dict.values():
                    size_text = self.get_size_text(path)
                    self.treeview.insert("exclude", -1, text=os.path.basename(path), values=(size_text,), iid=self._npaths)
                    self.exclude_path_dict[self._npaths] = path
                    self.get_icon(self._npaths)
                    self._npaths += 1

        pos = 0
        for k, v in sorted(self.exclude_path_dict.items(),
                           key=lambda x: (os.path.isfile(x[1]),
                                          os.path.basename(x[1]))):
            self.treeview.move(k, "exclude", pos)
            if not os.path.exists(v) or v in self.path_dict.values():
                self.treeview.delete(k)
            else:
                pos += 1

        if pos == 0 and self.treeview.exists("exclude"):
            self.treeview.delete("exclude")

    def insert_exclude_ext(self, *newexts):
        if len(newexts) >= 1:
            if not self.treeview.exists("exclude_ext"):
                self.treeview.insert("", 3, text="Excluir Extensiones:", values=("-"), iid="exclude_ext", open=True)

        for ext in newexts:
            if not ext in self.exclude_ext_dict.values():
                self.treeview.insert("exclude_ext", -1, text=ext, values=("-",), iid=self._npaths)
                self.exclude_ext_dict[self._npaths] = ext
                self.get_icon(self._npaths)
                self._npaths += 1

        pos = 0
        for i in sorted(self.exclude_ext_dict.items(),
                        key=lambda x: x[1]):
            self.treeview.move(i[0], "exclude_ext", pos)
            pos += 1

        if pos == 0 and self.treeview.exists("exclude_ext"):
            self.treeview.delete("exclude_ext")

    def remove_paths(self):
        selected = self.treeview.selection()

        for i in selected:
            self.treeview.delete(i)

            # Incluir:
            if int(i) in self.path_dict:
                path = self.path_dict.pop(int(i))
                if path in self.data['paths']:
                    self.data['paths'].remove(path)

            # Excluir rutas
            elif int(i) in self.exclude_path_dict:
                path = self.exclude_path_dict.pop(int(i))
                if path in self.data['exclude_paths']:
                    self.data['exclude_paths'].remove(path)

            # Excluir extensiones
            elif int(i) in self.exclude_ext_dict:
                ext = self.exclude_ext_dict.pop(int(i))
                if ext in self.data['exclude_ext']:
                    self.data['exclude_ext'].remove(ext)

    def get_size_text(self, path):
        if os.path.isfile(path):
            return f"{int(math.ceil(os.path.getsize(path)/1024)):,}KB".replace(",", ".")
        else:
            return "-"

    def add_file(self, filenames=None):
        if filenames is None:
            filenames = tkfd.askopenfilenames()

        for filename in filenames:
            if not filename in self.data['paths']:
                self.data['paths'].append(filename)

            if filename in self.data['exclude_paths']:
                self.data['exclude_paths'].remove(filename)
                for k, v in tuple(self.exclude_path_dict.items()):
                    if v == filename:
                        self.exclude_path_dict.pop(k)
                        self.treeview.delete(k)

        self.insert_paths(*filenames)
        self.insert_exclude_paths()  # Actualizar la lista

    def add_directory(self, dirname=None):
        if dirname is None:
            dirname = tkfd.askdirectory()

        if dirname is None:
            return None

        elif not os.path.exists(dirname):
            return None

        if not dirname in self.data['paths']:
            self.data['paths'].append(dirname)

        if dirname in self.data['exclude_paths']:
            self.data['exclude_paths'].remove(dirname)
            for k, v in tuple(self.exclude_path_dict.items()):
                if v == dirname:
                    self.exclude_path_dict.pop(k)
                    self.treeview.delete(k)

        self.insert_paths(dirname)
        self.insert_exclude_paths()  # Actualizar la lista

    def add_exclude_file(self, filenames=None):
        if filenames is None:
            filenames = tkfd.askopenfilenames()

        for filename in filenames:
            if not filename in self.data['exclude_paths']:
                self.data['exclude_paths'].append(filename)

            if filename in self.data['paths']:
                self.data['paths'].remove(filename)
                for k, v in tuple(self.path_dict.items()):
                    if v == filename:
                        self.path_dict.pop(k)
                        self.treeview.delete(k)

        self.insert_exclude_paths(*filenames)
        self.insert_paths()  # Actualizar la lista

    def add_exclude_directory(self, dirname=None):
        if dirname is None:
            dirname = tkfd.askdirectory()

        if dirname is None:
            return None

        elif not os.path.exists(dirname):
            return None

        if not dirname in self.data['exclude_paths']:
            self.data['exclude_paths'].append(dirname)

        if dirname in self.data['paths']:
            self.data['paths'].remove(dirname)
            for k, v in tuple(self.path_dict.items()):
                if v == dirname:
                    self.path_dict.pop(k)
                    self.treeview.delete(k)

        self.insert_exclude_paths(dirname)
        self.insert_paths()  # Actualizar la lista

    def add_exclude_ext(self, ext=None):
        if ext is None:
            ext = PopUpEntry.ask("Excluir extensión:", "Ingrese la extensión que desea excluir:", self.root, value=".exe").data

        if ext is None:
            return None

        ext = "."+ext.split(".")[-1]

        self.insert_exclude_ext(ext)

        if not ext in self.data['exclude_ext']:
            self.data['exclude_ext'].append(ext)

    def verify(self, message=True):
        if len(self.data['paths']) >= 1:
            return True
        elif message:
            tkmb.showerror("Falta información", "No se ha seleccionado ningún archivo o carpeta para cifrar.")
        else:
            return False

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Agregar los archivos:\n\n"+HELP_DICT['NUEVO_PASO_1'])
        popup.show()

    def load_data(self, data):
        if "paths" in data:
            self.add_file(data["paths"])

        if "exclude_paths":
            self.add_exclude_file(data["exclude_paths"])

        if "exclude_ext":
            for ext in data["exclude_ext"]:
                self.add_exclude_ext(ext)


class FrameSaveFileStep2(ttk.Frame):
    def __init__(self, root, app, parent):
        super().__init__(root)
        self.top = self
        self.root = root
        self.app = app
        self.parent = parent

        self.data = None

        if os.path.exists(f"{IMG_PATH}\\guardar.png") and os.path.exists(f"{IMG_PATH}\\cargar.png"):
            self.img_guardar = tk.PhotoImage(file=f"{IMG_PATH}\\guardar.png")
            self.img_cargar = tk.PhotoImage(file=f"{IMG_PATH}\\cargar.png")
        else:
            self.img_guardar = None
            self.img_cargar = None

        self.label1 = ttk.Label(self.top, text="Guardar archivo XCIF en:")
        self.entry_file = FileEntry(self.top,)
        self.entry_file.set_filter_search([".xcif"])  # filter search when press "key-tab"
        self.entry_file.bind("<Key-Return>", self.entry_file_return_key)
        self.select_entry_file = ttk.Button(self.top, text="Guardar en", command=self.set_save_file_path)

        self.label2 = ttk.Label(self.top, text="Autor (opcional):")
        self.entry_author = ttk.Entry(self.top,)
        self.entry_author.bind("<Key-Return>", self.entry_author_return_key)
        self.select_entry_author = ttk.Button(self.top, text="Predeterminado", command=self.set_default_author)

        self.label3 = ttk.Label(self.top, text="Comentario (opcional):")
        self.comment = ScrolledText(self.top)
        self.comment.bind("<Control-Key-Return>", self.comment_control_return_keys)

        self.button_save_comment = ttk.Button(self.top, text="Guardar", command=self.save_comment)
        self.button_load_comment = ttk.Button(self.top, text="Cargar", command=self.load_comment)

        if self.img_guardar is not None:
            self.button_save_comment['image'] = self.img_guardar
            self.button_load_comment['image'] = self.img_cargar

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_prev = ttk.Button(self.top, text="Anterior", command=self.prev_tabs)
        self.button_next = ttk.Button(self.top, text="Siguiente", command=self.next_tabs)

        self.set_default_author()

        # Shortcuts
        self.parent.bind("<Key-F2>", lambda _=None, self=self: self.select_entry_file.invoke())
        self.parent.bind("<Key-F3>", lambda _=None, self=self: self.select_entry_author.invoke())

        self.parent.bind("<Control-Key-F2>", lambda _=None, self=self: self.button_save_comment.invoke())
        self.parent.bind("<Control-Key-F3>", lambda _=None, self=self: self.button_load_comment.invoke())

    def entry_file_return_key(self, _=None):
        path = self.entry_file.get()
        if len(path) == 0:
            return self.select_entry_file.invoke()

        if os.path.splitext(path)[-1].lower() == ".xcif" and os.path.isabs(path):
            self.set_save_file_path(path)
            self.entry_author.focus_set()

    def entry_author_return_key(self, _=None):
        self.comment.focus_set()

    def comment_control_return_keys(self, _=None):
        self.button_next.invoke()

    def set_save_file_path(self, path=None):
        if path is None:
            path = os.path.abspath(tkfd.asksaveasfilename(filetypes=[('Archivos XCIF', '*.xcif')]))

        if path is None:
            return None

        else:
            if not os.path.splitext(path)[1].lower() == ".xcif":
                path += ".xcif"

        self.entry_file.delete(0, len(self.entry_file.get()))
        self.entry_file.insert(0, path)

        if os.path.exists(path):
            load = xcif.XCIF(path)
            properties = load.get_header()

            if properties['USER'] is not None:
                self.set_default_author(properties['USER'].decode())
            else:
                self.set_default_author("")

            if properties['COMMENT'] is not None:
                self.set_comment(properties['COMMENT'].decode())
            else:
                self.set_comment("")

    def set_default_author(self, author=None):
        self.entry_author.delete(0, len(self.entry_author.get()))
        if author is None:
            self.entry_author.insert(0, getpass.getuser())
        else:
            self.entry_author.insert(0, author)

    def save_comment(self):
        path = tkfd.asksaveasfilename(filetypes=[('Archivos de Texto (*.txt)', '*.txt')])

        if path is None:
            return None

        elif not os.path.splitext(path)[1].lower() == ".txt":
            path = path+".txt"

        try:
            with open(path, "w") as f:
                f.write(self.comment.get("1.0", "end").rstrip())

        except OSError:
            tkmb.showerror("Imposible guardar el archivo:",
                           "El archivo no pudo ser guardado.\nCompruebe:\n"
                           "\n* La existencia del directorio de destino.\n"
                           "\n* Los permisos de escritura en el directorio.\n"
                           "\n* Los permisos de la aplicación.")

    def load_comment(self):
        path = tkfd.askopenfilename(filetypes=[('Archivos de Texto (*.txt)', '*.txt')])

        if path is None:
            return None

        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.comment.delete("1.0", "end")
                    self.comment.insert("1.0", f.read())

        except OSError:
            tkmb.showerror("Imposible leer el archivo:",
                           "El archivo no pudo ser cargado.\nCompruebe:\n"
                           "\n* La existencia del archivo.\n"
                           "\n* La extensión sea TXT.\n"
                           "\n* Que el archivo no se encuentre dañado.")

    def set_comment(self, text=None):
        self.comment.delete("1.0", "end")
        if text is not None:
            self.comment.insert("1.0", text)

    def layout(self):
        self.label1.place(x=10, y=10, width=580, height=24)
        self.entry_file.place(x=10, y=40, width=470, height=24)
        self.select_entry_file.place(x=485, y=40, width=100, height=24)

        self.label2.place(x=10, y=70, width=580, height=24)
        self.entry_author.place(x=10, y=100, width=470, height=24)
        self.select_entry_author.place(x=485, y=100, width=100, height=24)

        self.label3.place(x=10, y=130, width=200, height=24)
        self.comment.place(x=10, y=160, width=575, height=200)

        if self.img_guardar is not None:
            self.button_load_comment.place(x=484, y=128, width=48, height=28)
            self.button_save_comment.place(x=537, y=128, width=48, height=28)

        else:
            self.button_load_comment.place(x=415, y=130, width=80, height=24)
            self.button_save_comment.place(x=505, y=130, width=80, height=24)

        self.button_help.place(x=235, y=370, width=80, height=24)
        self.button_cancel.place(x=325, y=370, width=80, height=24)
        self.button_prev.place(x=415, y=370, width=80, height=24)
        self.button_next.place(x=505, y=370, width=80, height=24)

    def prev_tabs(self):
        self.root.select(0)
        self.parent.frame_step1.focus_set()

    def next_tabs(self):
        if self.verify():
            self.root.select(2)

    def verify(self, message=True):
        self.data = {
            'save_as': self.entry_file.get(),
            'author': self.entry_author.get().rstrip(),
            'comment': self.comment.get('1.0', 'end').rstrip()
        }
        if len(self.data['save_as']) >= 1:
            if os.path.isabs(self.data['save_as']):
                return True
            else:
                if message:
                    tkmb.showerror("Error", "La ruta elegida para el archivo XCIF de destino no es válida.")
                return False

        else:
            if message:
                tkmb.showerror("Falta información", "No se ha seleccionado ningún archivo XCIF de destino.")
            return False

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Datos del Archivo XCIF:\n\n"+HELP_DICT['NUEVO_PASO_2'])
        popup.show()

    def load_data(self, data):
        if "save_as" in data:
            self.set_save_file_path(data['save_as'])

        if "author" in data:
            self.set_default_author(data["author"])

        if "comment" in data:
            self.set_comment(data["comment"])


class PopUpSavingXCIF(PopUp):
    def __init__(self, root, app, filename):
        super().__init__(root)
        self.set_geometry("620x340")
        self.app = app
        self.filename = filename
        self.data = None
        self.cancel = False
        # Create widget:
        # total:
        self.labelframe_total = ttk.LabelFrame(self.top, text="Total:")
        self.label_number_files = ttk.Label(self.labelframe_total, text="Archivos:")
        self.label_total_size = ttk.Label(self.labelframe_total, text="Procesado:")
        self.label_total_percent = ttk.Label(self.labelframe_total, text="Porcentaje:")
        self.label_time = ttk.Label(self.labelframe_total, text="Tiempo:")
        self.label_remain_time = ttk.Label(self.labelframe_total, text="Restante:")
        self.label_speed = ttk.Label(self.labelframe_total, text="Velocidad:")

        self.value_number_files = ttk.Label(self.labelframe_total, text="0 / 0")
        self.value_total_size = ttk.Label(self.labelframe_total, text="0 KB / 0 KB")
        self.value_total_percent = ttk.Label(self.labelframe_total, text="%0")
        self.value_time = ttk.Label(self.labelframe_total, text="0:00:00")
        self.value_remain_time = ttk.Label(self.labelframe_total, text="0:00:00")
        self.value_speed = ttk.Label(self.labelframe_total, text="0 KB/s")

        self.total_percent = tk.IntVar(value=99.99)
        self.total_bar = ttk.Progressbar(self.labelframe_total, variable=self.total_percent)

        # current:
        self.labelframe_current = ttk.LabelFrame(self.top, text="Actual:")
        self.label_name = ttk.Label(self.labelframe_current, text="Nombre:")
        self.label_current_size = ttk.Label(self.labelframe_current, text="Procesado:")
        self.label_current_percent = ttk.Label(self.labelframe_current, text="Porcentaje:")
        self.label_current_time = ttk.Label(self.labelframe_current, text="Tiempo:")
        self.label_represent = ttk.Label(self.labelframe_current, text="Representa:")

        self.value_name = ttk.Label(self.labelframe_current, text="")
        self.value_current_size = ttk.Label(self.labelframe_current, text="0 KB / 0 KB")
        self.value_current_percent = ttk.Label(self.labelframe_current, text="%0")
        self.value_current_time = ttk.Label(self.labelframe_current, text="0:00:00 / 0:00:00")
        self.value_represent = ttk.Label(self.labelframe_current, text="%100.00 del total")

        self.current_percent = tk.IntVar(value=0)
        self.current_bar = ttk.Progressbar(self.labelframe_current, variable=self.current_percent)

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_close = ttk.Button(self.top, text="Finalizar", command=self.top.destroy, state="disabled")
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.cancel_command)
        self.button_open = ttk.Button(self.top, text="Abrir Carpeta Contenedora", command=self.open_folder, state="disabled")
        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.cancel_command)

    def layout(self):
        # total
        self.labelframe_total.place(x=10, y=10, width=600, height=142)
        self.label_number_files.place(x=5, y=2, width=80, height=24)
        self.label_total_size.place(x=5, y=32, width=80, height=24)
        self.label_total_percent.place(x=5, y=62, width=80, height=24)
        self.label_time.place(x=300, y=2, width=80, height=24)
        self.label_remain_time.place(x=300, y=32, width=80, height=24)
        self.label_speed.place(x=300, y=62, width=80, height=24)

        self.value_number_files.place(x=85, y=2, width=205, height=24)
        self.value_total_size.place(x=85, y=32, width=205, height=24)
        self.value_total_percent.place(x=85, y=62, width=205, height=24)
        self.value_time.place(x=380, y=2, width=205, height=24)
        self.value_remain_time.place(x=380, y=32, width=205, height=24)
        self.value_speed.place(x=380, y=62, width=205, height=24)

        self.total_bar.place(x=5, y=92, width=580, height=20)

        # current
        self.labelframe_current.place(x=10, y=154, width=600, height=142)
        self.label_name.place(x=5, y=2, width=80, height=24)
        self.label_current_size.place(x=5, y=32, width=80, height=24)
        self.label_current_percent.place(x=5, y=62, width=80, height=24)
        self.label_current_time.place(x=300, y=32, width=80, height=24)
        self.label_represent.place(x=300, y=62, width=80, height=24)

        self.value_name.place(x=85, y=2, width=470, height=24)
        self.value_current_size.place(x=85, y=32, width=205, height=24)
        self.value_current_percent.place(x=85, y=62, width=205, height=24)
        self.value_current_time.place(x=380, y=32, width=205, height=24)
        self.value_represent.place(x=380, y=62, width=205, height=24)

        self.current_bar.place(x=5, y=92, width=580, height=20)

        self.button_open.place(x=10, y=305, width=170, height=24)
        self.button_help.place(x=350, y=305, width=80, height=24)
        self.button_cancel.place(x=440, y=305, width=80, height=24)
        self.button_close.place(x=530, y=305, width=80, height=24)

    def update_static_info(self, **data):
        # total
        self.value_number_files['text'] = "{n_files} / {n_total_files}".format(**data)
        # current
        self.value_name['text'] = "{name}".format(**data)
        self.value_represent['text'] = "%{represent:2.2f} del total".format(**data)

    def update_info(self, **data):
        # total
        self.value_total_size['text'] = "{tot_proc} / {tot_total_proc}".format(**data)
        self.value_total_percent['text'] = "%{tot_percent:2.1f}".format(**data)
        self.value_time['text'] = "{tot_time}".format(**data)
        self.value_remain_time['text'] = "{tot_remain_time}".format(**data)
        self.value_speed['text'] = "{speed}/s".format(**data)
        self.total_percent.set(min(99.99, data["tot_percent"]))
        # current
        self.value_current_size['text'] = "{cur_proc} / {cur_total_proc}".format(**data)
        self.value_current_percent['text'] = "%{cur_percent:2.1f}".format(**data)
        self.value_current_time['text'] = "{cur_time} / {cur_time_total}".format(**data)
        self.current_percent.set(min(99.99, data["cur_percent"]))

    def update(self):
        self.root.update()

    def end(self):
        self.button_close.configure(state=tk.NORMAL)
        self.button_open.configure(state=tk.NORMAL)
        self.button_cancel.configure(state=tk.DISABLED)

        self.top.bind("<Key-Return>", lambda _=None, self=self: self.button_close.invoke())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.button_close.invoke())
        self.top.bind("<Key-F2>", lambda _=None, self=self: self.button_open.invoke())

        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.button_close.invoke)

    def open_folder(self):
        subprocess.call(f'explorer.exe /select,"{os.path.abspath(self.filename)}"')

    def show(self):
        self.layout()

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)

    def wait(self):
        self.root.wait_window(self.top)

    def cancel_command(self):
        if tkmb.askyesno("Cancelar operación",
                         "¿Desea cancelar la operación actual?"):
            self.top.destroy()

            self.cancel = True

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Exportando Archivo XCIF:\n\n"+HELP_DICT['GUARDANDO'])
        popup.show()


class PopUpLoad(PopUp):
    def __init__(self, root, app, data=None):
        super().__init__(root)
        self.set_geometry("620x450")
        self.app = app
        self.data = None
        # Create widget:
        self.notebook = ttk.Notebook(self.top)

        # Create tabs:
        self.frame_step1 = FrameLoadFileStep1(self.notebook, self.app, self.top)
        self.frame_step2 = FrameLoadFileStep2(self.notebook, self.app, self.top)
        self.frame_step3 = FramePasswords(self.notebook, self.app, self.top)

        # Add tabs:
        self.notebook.add(self.frame_step1, text="Archivos")
        self.notebook.add(self.frame_step2, text="Información")
        self.notebook.add(self.frame_step3, text="Seguridad")

        # Configure tabs:
        self.frame_step1.step2 = self.frame_step2
        self.frame_step1.button_cancel['command'] = self.cancel_command
        self.frame_step2.button_cancel['command'] = self.cancel_command
        self.frame_step3.button_cancel['command'] = self.cancel_command
        self.frame_step3.button_next['command'] = self.ok_command

        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.cancel_command)

        if data is not None:
            self.frame_step1.load_data(data[0])
            self.frame_step3.load_data(data[1])

            if len(data) >= 3:
                if data[2].get('ok_command', False):
                    self.top.after(50, lambda _=None: self.ok_command())

        # Shortcuts
        self.top.bind("<Control-Key-Left>", lambda _=None, self=self: self.key_control_left())
        self.top.bind("<Control-Key-Right>", lambda _=None, self=self: self.key_control_right())
        self.top.bind("<Control-Key-Return>", lambda _=None, self=self: self.key_control_return())
        self.top.bind("<Control-Key-BackSpace>", lambda _=None, self=self: self.key_control_backspace())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.key_escape())
        self.top.bind("<Key-Return>", lambda _=None, self=self: self.key_return())
        self.top.bind("<Key-F1>", lambda _=None, self=self: self.key_f1())

    def layout(self):
        self.notebook.place(x=10, y=10, width=600, height=430)

    def show(self):
        self.layout()
        self.frame_step1.layout()
        self.frame_step2.layout()
        self.frame_step3.layout()

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def ok_command(self):
        self.data = []
        for frame in [self.frame_step1, self.frame_step3]:
            if frame.verify():
                self.data.append(frame.data)
            else:
                return self.notebook.select(frame)

        if not (len(self.data[1]['password1']) == 0 or len(self.data[1]['password1']) >= 8):
            return tkmb.showerror(
                "Contraseña 1",
                "La contraseña número 1 no cumple con alguno de los siguientes requisitos:\n"
                "* Tamaño: 8 caracteres."
            )

        elif not (len(self.data[1]['password2']) == 0 or
                  (len(self.data[1]['password2']) >= 8 and
                   len(self.data[1]['password1']) >= 8)):

            return tkmb.showerror(
                "Contraseña 2",
                "La contraseña número 2 no cumple con alguno de los siguientes siguientes requisitos:\n"
                "* Tamaño: 8 caracteres.\n* La 'Contraseña 1' debe estar definida."
            )

        elif not (len(self.data[1]['password3']) == 0 or
                  (len(self.data[1]['password3']) >= 8 and
                   len(self.data[1]['password1']) >= 8 and
                   len(self.data[1]['password2']) >= 8)):

            return tkmb.showerror(
                "Contraseña 3",
                "La contraseña número 3 no cumple con alguno de los siguientes siguientes requisitos:\n"
                "* Tamaño: 8 caracteres.\n* La 'Contraseña 1' debe estar definida.\n"
                "* La 'Contraseña 2' debe estar definida."
            )

        self.top.destroy()

    def cancel_command(self):
        if tkmb.askyesno("Cancelar operación",
                         "¿Desea cancelar la operación actual?"):
            self.data = None
            self.top.destroy()
            return True

    def get_current_frame(self):
        frames = [self.frame_step1, self.frame_step2, self.frame_step3]
        select = self.notebook.select()

        for i in frames:
            if str(i) == str(select):
                return i

    def key_control_left(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

        elif frame == self.frame_step3:
            self.frame_step3.button_next.invoke()

    def key_control_right(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step1:
            self.frame_step1.button_next.invoke()

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

    def key_control_backspace(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

        elif frame == self.frame_step3:
            self.frame_step3.button_next.invoke()

    def key_control_return(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step1:
            self.frame_step1.button_next.invoke()

        elif frame == self.frame_step2:
            self.frame_step2.button_next.invoke()

    def key_escape(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        else:
            self.cancel_command()

    def key_return(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame == self.frame_step2:
            self.frame_step2.focus_set()

    def key_f1(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame in (self.frame_step1, self.frame_step2, self.frame_step3):
            frame.show_help_popup()


class FrameLoadFileStep1(ttk.Frame):
    def __init__(self, root, app, parent):
        super().__init__(root)
        self.top = self
        self.root = root
        self.app = app
        self.parent = parent

        self.data = None
        self.step2 = None

        self.label1 = ttk.Label(self.top, text="Archivo XCIF:")
        self.entry_xcif = FileEntry(self.top,)
        self.entry_xcif.set_filter_search([".xcif"])
        self.entry_xcif.bind("<Key-Return>", self.entry_xcif_return_key)  # Validate
        self.select_xcif_file = ttk.Button(self.top, text="Cargar Archivo", command=self.set_xcif)
        self.entry_xcif.bind("<Key-F2>", lambda _=None, self=self: self.select_xcif_file.invoke())

        self.label2 = ttk.Label(self.top, text="Extraer en:")
        self.entry_directory = FileEntry(self.top)
        self.entry_directory.set_filter_search(["(folder)"])
        self.entry_directory.bind("<Key-Return>", self.entry_directory_return_key)  # Validate
        self.select_directory = ttk.Button(self.top, text="Examinar", command=self.set_directory)
        self.entry_directory.bind("<Key-F2>", lambda _=None, self=self: self.select_directory.invoke())

        self.label3 = ttk.Label(self.top, text="Tamaño:")
        self.entry_size = ttk.Entry(self.top, state="readonly")

        self.label4 = ttk.Label(self.top, text="Espacio Libre (Disco):")
        self.entry_size_disk = ttk.Entry(self.top, state="readonly")
        self.var_size_disk_percent = tk.IntVar(value=0)
        self.progressbar_size = ttk.Progressbar(self.top, variable=self.var_size_disk_percent)

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_prev = ttk.Button(self.top, text="Anterior", state="disabled")
        self.button_next = ttk.Button(self.top, text="Siguiente", command=self.next_tabs)

    def entry_xcif_return_key(self, _=None):
        path = self.entry_xcif.get()
        if len(path) == 0:
            return self.select_xcif_file.invoke()

        if os.path.isabs(path) and os.path.exists(path) and os.path.splitext(path)[-1].lower() == ".xcif":
            self.set_xcif(path)
            self.entry_directory.focus_set()

    def entry_directory_return_key(self, _=None):
        path = self.entry_directory.get()
        if len(path) == 0:
            return self.select_directory.invoke()

        if os.path.isabs(path) and \
                ((not os.path.exists(path)) or os.path.isdir(path)):

            self.set_directory(path)
            self.button_next.invoke()

    def set_xcif(self, path=None):
        if path is None:
            path = tkfd.askopenfilename(filetypes=[('Archivos XCIF', '*.xcif')])

        if path is None:
            return None

        elif os.path.isabs(path) and os.path.exists(path):
            self.entry_xcif.delete(0, len(self.entry_xcif.get()))
            self.entry_xcif.insert(0, os.path.abspath(path))

            size = os.path.getsize(path)
            size_unit = xcif.xmaker.get_size_unit(size)

            self.set_size(size_unit)

            if len(self.entry_directory.get()) == 0:
                basepath = os.path.split(path)[0]
                name = os.path.splitext(os.path.basename(path))[0]
                self.set_directory(os.path.join(basepath, "XCIF_"+name))

            if self.step2 is not None:
                load = xcif.XCIF(path)
                properties = load.get_header()

                self.step2.set_version(properties['VERSION'])
                if properties['USER'] is not None:
                    self.step2.set_author(properties['USER'].decode())
                else:
                    self.step2.set_author("")

                if properties['COMMENT'] is not None:
                    self.step2.set_comment(properties['COMMENT'].decode())
                else:
                    self.step2.set_comment("")

    def set_directory(self, path=None):
        if path is None:
            path = tkfd.askdirectory()

        if path is None:
            return None

        elif os.path.isabs(path):
            self.entry_directory.delete(0, len(self.entry_directory.get()))
            self.entry_directory.insert(0, os.path.abspath(path))
            self.set_size_disk(path)

    def set_size(self, size):
        self.entry_size.config(state="normal")
        self.entry_size.delete(0, len(self.entry_size.get()))
        self.entry_size.insert(0, size)
        self.entry_size.config(state="readonly")

    def set_size_disk(self, path):
        disk = f"{os.path.splitdrive(os.path.abspath(path))[0]}/."
        disks = shutil.disk_usage(disk)

        total, used, free = disks.total, disks.used, disks.free
        if total > 0:
            percent = 100*(used/total)
        else:
            percent = 0

        self.entry_size_disk.config(state="normal")
        self.entry_size_disk.delete(0, len(self.entry_size.get()))
        self.entry_size_disk.insert(0, xcif.xmaker.get_size_unit(free) + " / "+xcif.xmaker.get_size_unit(total) + f" (%{100-percent:2.1f})")
        self.entry_size_disk.config(state="readonly")

        self.var_size_disk_percent.set(min(99.99, max(0, percent)))

    def layout(self):
        self.label1.place(x=10, y=10, width=580, height=24)
        self.entry_xcif.place(x=10, y=40, width=470, height=24)
        self.select_xcif_file.place(x=485, y=40, width=100, height=24)

        self.label2.place(x=10, y=70, width=580, height=24)
        self.entry_directory.place(x=10, y=100, width=470, height=24)
        self.select_directory.place(x=485, y=100, width=100, height=24)

        self.label3.place(x=10, y=130, width=200, height=24)
        self.entry_size.place(x=10, y=160, width=575, height=24)

        self.label4.place(x=10, y=190, width=200, height=24)
        self.entry_size_disk.place(x=10, y=220, width=575, height=24)
        self.progressbar_size.place(x=10, y=250, width=575, height=24)

        self.button_help.place(x=235, y=370, width=80, height=24)
        self.button_cancel.place(x=325, y=370, width=80, height=24)
        self.button_prev.place(x=415, y=370, width=80, height=24)
        self.button_next.place(x=505, y=370, width=80, height=24)

    def next_tabs(self):
        if self.verify():
            self.root.select(1)

    def verify(self, message=True):
        self.data = {
            'xcif_file': self.entry_xcif.get(),
            'save_as': self.entry_directory.get().rstrip(),
        }
        if len(self.data['xcif_file']) >= 1:
            if not os.path.isabs(self.data['xcif_file']):
                if message:
                    tkmb.showerror("Error", "El archivo XCIF no existe.")
                return False
        else:
            if message:
                tkmb.showerror("Falta información", "No se ha seleccionado ningún archivo XCIF.")
            return False

        if len(self.data['save_as']) >= 1:
            if not os.path.isabs(self.data['save_as']):
                if message:
                    tkmb.showerror("Error", "La ruta elegida para la extración del archivo XCIF no es válida.")
                return False
        else:
            if message:
                tkmb.showerror("Falta información", "No se ha seleccionado ninguna ruta de extracción para el archivo XCIF.")
            return False

        return True

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Seleccionar Archivo XCIF y Directorio de Destino:\n\n"+HELP_DICT['ABRIR_PASO_1'])
        popup.show()

    def load_data(self, data):
        if 'xcif_file' in data:
            self.set_xcif(data['xcif_file'])

        if 'save_as' in data:
            self.set_directory(data['save_as'])


class FrameLoadFileStep2(ttk.Frame):
    def __init__(self, root, app, parent):
        super().__init__(root)
        self.top = self
        self.root = root
        self.app = app
        self.parent = parent

        self.data = None

        if os.path.exists(f"{IMG_PATH}\\guardar.png") and os.path.exists(f"{IMG_PATH}\\cargar.png"):
            self.img_guardar = tk.PhotoImage(file=f"{IMG_PATH}\\guardar.png")
            self.img_copiar = tk.PhotoImage(file=f"{IMG_PATH}\\rundll32.png")
        else:
            self.img_guardar = None
            self.img_copiar = None

        self.label1 = ttk.Label(self.top, text="Versión del XCIF utilizada:")
        self.entry_version = ttk.Entry(self.top, state="readonly")
        self.button_copy_version = ttk.Button(self.top, text="Copiar", command=self.copy_version)

        self.label2 = ttk.Label(self.top, text="Autor:")
        self.entry_author = ttk.Entry(self.top, state="readonly")
        self.button_copy_author = ttk.Button(self.top, text="Copiar", command=self.copy_author)

        self.label3 = ttk.Label(self.top, text="Comentario:")
        self.comment = ScrolledText(self.top, state="disabled", wrap="word")
        self.button_save_comment = ttk.Button(self.top, text="Guardar", command=self.save_comment)
        self.button_copy_comment = ttk.Button(self.top, text="Copiar", command=self.copy_comment)

        if self.img_guardar is not None:
            self.button_save_comment['image'] = self.img_guardar
            self.button_copy_comment['image'] = self.img_copiar

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.top.destroy)
        self.button_prev = ttk.Button(self.top, text="Anterior", command=self.prev_tabs)
        self.button_next = ttk.Button(self.top, text="Siguiente", command=self.next_tabs)

        self.bind("<Key-Return>", lambda _=None, self=self: self.button_next.invoke())

    def set_version(self, version):
        self.entry_version.config(state="normal")
        self.entry_version.delete(0, len(self.entry_version.get()))
        if version is not None:
            self.entry_version.insert(0, version)
        self.entry_version.config(state="readonly")

    def set_author(self, author):
        self.entry_author.config(state="normal")
        self.entry_author.delete(0, len(self.entry_author.get()))
        if author is not None:
            self.entry_author.insert(0, author)
        self.entry_author.config(state="readonly")

    def save_comment(self):
        path = tkfd.asksaveasfilename(filetypes=[('Archivos de Texto (*.txt)', '*.txt')])

        if path is None:
            return None

        elif not os.path.splitext(path)[1].lower() == ".txt":
            path = path+".txt"

        try:
            with open(path, "w") as f:
                f.write(self.comment.get("1.0", "end").rstrip())

        except OSError:
            tkmb.showerror("Imposible guardar el archivo:",
                           "El archivo no pudo ser guardado.\nCompruebe:\n"
                           "\n* La existencia del directorio de destino.\n"
                           "\n* Los permisos de escritura en el directorio.\n"
                           "\n* Los permisos de la aplicación.")

    def set_comment(self, comment):
        self.comment.config(state="normal")
        self.comment.delete("1.0", "end")
        if comment is not None:
            self.comment.insert("1.0", comment)
        self.comment.config(state="disabled")

    def layout(self):
        self.label1.place(x=10, y=10, width=580, height=24)
        self.entry_version.place(x=10, y=40, width=470, height=24)
        self.button_copy_version.place(x=485, y=40, width=100, height=24)

        self.label2.place(x=10, y=70, width=580, height=24)
        self.entry_author.place(x=10, y=100, width=470, height=24)
        self.button_copy_author.place(x=485, y=100, width=100, height=24)

        self.label3.place(x=10, y=130, width=200, height=24)
        self.comment.place(x=10, y=160, width=575, height=200)

        if self.img_guardar is not None:
            self.button_copy_comment.place(x=484, y=128, width=48, height=28)
            self.button_save_comment.place(x=537, y=128, width=48, height=28)

        else:
            self.button_copy_comment.place(x=415, y=130, width=80, height=24)
            self.button_save_comment.place(x=505, y=130, width=80, height=24)

        self.button_help.place(x=235, y=370, width=80, height=24)
        self.button_cancel.place(x=325, y=370, width=80, height=24)
        self.button_prev.place(x=415, y=370, width=80, height=24)
        self.button_next.place(x=505, y=370, width=80, height=24)

    def prev_tabs(self):
        self.root.select(0)

    def next_tabs(self):
        self.root.select(2)

    def copy_author(self):
        self.copy(self.entry_author.get())

    def copy_version(self):
        self.copy(self.entry_version.get())

    def copy_comment(self):
        self.copy(self.comment.get("1.0", "end"))

    def copy(self, text):
        self.top.clipboard_clear()
        self.top.clipboard_append(text)

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Datos del Archivo XCIF:\n\n"+HELP_DICT['ABRIR_PASO_2'])
        popup.show()


class PopUpLoadingXCIF(PopUp):
    def __init__(self, root, app, filename, extracted):
        super().__init__(root)
        self.set_geometry("620x340")
        self.app = app
        self.filename = filename
        self.extracted = extracted
        self.data = None
        self.cancel = False
        # Create widget:
        # total:
        self.labelframe_total = ttk.LabelFrame(self.top, text="Total:")
        self.label_number_files = ttk.Label(self.labelframe_total, text="Archivos:")
        self.label_total_size = ttk.Label(self.labelframe_total, text="Procesado:")
        self.label_total_percent = ttk.Label(self.labelframe_total, text="Porcentaje:")
        self.label_time = ttk.Label(self.labelframe_total, text="Tiempo:")
        self.label_remain_time = ttk.Label(self.labelframe_total, text="Restante:")
        self.label_speed = ttk.Label(self.labelframe_total, text="Velocidad:")

        self.value_number_files = ttk.Label(self.labelframe_total, text="0")
        self.value_total_size = ttk.Label(self.labelframe_total, text="0 KB / 0 KB")
        self.value_total_percent = ttk.Label(self.labelframe_total, text="%0")
        self.value_time = ttk.Label(self.labelframe_total, text="0:00:00")
        self.value_remain_time = ttk.Label(self.labelframe_total, text="0:00:00")
        self.value_speed = ttk.Label(self.labelframe_total, text="0 KB/s")

        self.total_percent = tk.IntVar(value=99.99)
        self.total_bar = ttk.Progressbar(self.labelframe_total, variable=self.total_percent)

        # current:
        self.labelframe_current = ttk.LabelFrame(self.top, text="Actual:")
        self.label_name = ttk.Label(self.labelframe_current, text="Nombre:")
        self.label_current_size = ttk.Label(self.labelframe_current, text="Procesado:")
        self.label_current_percent = ttk.Label(self.labelframe_current, text="Porcentaje:")
        self.label_current_time = ttk.Label(self.labelframe_current, text="Tiempo:")
        self.label_represent = ttk.Label(self.labelframe_current, text="Representa:")

        self.value_name = ttk.Label(self.labelframe_current, text="")
        self.value_current_size = ttk.Label(self.labelframe_current, text="0 KB / 0 KB")
        self.value_current_percent = ttk.Label(self.labelframe_current, text="%0")
        self.value_current_time = ttk.Label(self.labelframe_current, text="0:00:00 / 0:00:00")
        self.value_represent = ttk.Label(self.labelframe_current, text="%100.00 del total")

        self.current_percent = tk.IntVar(value=0)
        self.current_bar = ttk.Progressbar(self.labelframe_current, variable=self.current_percent)

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_close = ttk.Button(self.top, text="Finalizar", command=self.top.destroy, state="disabled")
        self.button_cancel = ttk.Button(self.top, text="Cancelar", command=self.cancel_command)
        self.button_open1 = ttk.Button(self.top, text="Abrir Carpeta Contenedora", command=self.open_folder_filename, state="disabled")
        self.button_open2 = ttk.Button(self.top, text="Abrir Carpeta Extraída", command=self.open_folder_extracted, state="disabled")
        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.cancel_command)

    def layout(self):
        # total
        self.labelframe_total.place(x=10, y=10, width=600, height=142)
        self.label_number_files.place(x=5, y=2, width=80, height=24)
        self.label_total_size.place(x=5, y=32, width=80, height=24)
        self.label_total_percent.place(x=5, y=62, width=80, height=24)
        self.label_time.place(x=300, y=2, width=80, height=24)
        self.label_remain_time.place(x=300, y=32, width=80, height=24)
        self.label_speed.place(x=300, y=62, width=80, height=24)

        self.value_number_files.place(x=85, y=2, width=205, height=24)
        self.value_total_size.place(x=85, y=32, width=205, height=24)
        self.value_total_percent.place(x=85, y=62, width=205, height=24)
        self.value_time.place(x=380, y=2, width=205, height=24)
        self.value_remain_time.place(x=380, y=32, width=205, height=24)
        self.value_speed.place(x=380, y=62, width=205, height=24)

        self.total_bar.place(x=5, y=92, width=580, height=20)

        # current
        self.labelframe_current.place(x=10, y=154, width=600, height=142)
        self.label_name.place(x=5, y=2, width=80, height=24)
        self.label_current_size.place(x=5, y=32, width=80, height=24)
        self.label_current_percent.place(x=5, y=62, width=80, height=24)
        self.label_current_time.place(x=300, y=32, width=80, height=24)
        self.label_represent.place(x=300, y=62, width=80, height=24)

        self.value_name.place(x=85, y=2, width=500, height=24)
        self.value_current_size.place(x=85, y=32, width=205, height=24)
        self.value_current_percent.place(x=85, y=62, width=205, height=24)
        self.value_current_time.place(x=380, y=32, width=205, height=24)
        self.value_represent.place(x=380, y=62, width=205, height=24)

        self.current_bar.place(x=5, y=92, width=580, height=20)

        self.button_open1.place(x=10, y=305, width=160, height=24)
        self.button_open2.place(x=180, y=305, width=160, height=24)
        self.button_help.place(x=350, y=305, width=80, height=24)
        self.button_cancel.place(x=440, y=305, width=80, height=24)
        self.button_close.place(x=530, y=305, width=80, height=24)

    def update_static_info(self, **data):
        # total
        self.value_number_files['text'] = "{n_files}".format(**data)
        # current
        self.value_name['text'] = "{name}".format(**data)
        self.value_represent['text'] = "%{represent:2.2f} del total".format(**data)

    def update_info(self, **data):
        # total
        self.value_total_size['text'] = "{tot_proc} / {tot_total_proc}".format(**data)
        self.value_total_percent['text'] = "%{tot_percent:2.1f}".format(**data)
        self.value_time['text'] = "{tot_time}".format(**data)
        self.value_remain_time['text'] = "{tot_remain_time}".format(**data)
        self.value_speed['text'] = "{speed}/s".format(**data)
        self.total_percent.set(min(99.99, data["tot_percent"]))
        # current
        self.value_current_size['text'] = "{cur_proc} / {cur_total_proc}".format(**data)
        self.value_current_percent['text'] = "%{cur_percent:2.1f}".format(**data)
        self.value_current_time['text'] = "{cur_time} / {cur_time_total}".format(**data)
        self.current_percent.set(min(99.99, data["cur_percent"]))

    def update(self):
        self.top.update()
        self.root.update()

    def end(self):
        self.button_close.configure(state=tk.NORMAL)
        self.button_open1.configure(state=tk.NORMAL)
        self.button_open2.configure(state=tk.NORMAL)
        self.button_cancel.configure(state=tk.DISABLED)

        self.top.bind("<Key-Return>", lambda _=None, self=self: self.button_close.invoke())
        self.top.bind("<Key-Escape>", lambda _=None, self=self: self.button_close.invoke())
        self.top.bind("<Key-F2>", lambda _=None, self=self: self.button_open1.invoke())
        self.top.bind("<Key-F3>", lambda _=None, self=self: self.button_open2.invoke())

        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.button_close.invoke)

    def open_folder_filename(self):
        subprocess.call(f'explorer.exe /select,"{os.path.abspath(self.filename)}"')

    def open_folder_extracted(self):
        subprocess.call(f'explorer.exe /select,"{os.path.abspath(self.extracted)}"')

    def show(self):
        self.layout()

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)

    def wait(self):
        self.root.wait_window(self.top)

    def cancel_command(self, force=False):
        if force or tkmb.askyesno("Cancelar operación",
                                  "¿Desea cancelar la operación actual?"):
            self.top.destroy()
            self.cancel = True

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Descifrando el Archivo XCIF:\n\n"+HELP_DICT['CARGANDO'])
        popup.show()


class PopUpAppSettings(PopUp):
    def __init__(self, root, app):
        super().__init__(root)
        self.set_geometry("620x450")
        self.app = app
        self.data = None
        # Create widget:
        self.notebook = ttk.Notebook(self.top)

        # Create tabs:
        self.frame_step1 = FrameSettingsStep1(self.notebook, self.app, self.top)
        self.frame_step2 = FrameSettingsStep2(self.notebook, self.app, self.top)

        # Add tabs:
        self.notebook.add(self.frame_step1, text="Interfaz")
        self.notebook.add(self.frame_step2, text="Seguridad")

        # Configure tabs:
        self.frame_step1.button_cancel['command'] = self.cancel_command
        self.frame_step2.button_cancel['command'] = self.cancel_command
        self.frame_step1.button_ok['command'] = self.ok_command
        self.frame_step2.button_ok['command'] = self.ok_command

        # Destroy:
        self.top.protocol("WM_DELETE_WINDOW", self.confirm_command)

        # Shortcut
        self.top.bind("<Key-F1>", lambda _=None, self=self: self.key_f1())

    def layout(self):
        self.notebook.place(x=10, y=10, width=600, height=430)

    def show(self):
        self.layout()
        self.frame_step1.layout()
        self.frame_step2.layout()

        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def ok_command(self):
        self.data = []
        for frame in [self.frame_step2]:
            if frame.verify():
                self.data.append(frame.data)
            else:
                return self.notebook.select(frame)

        self.top.destroy()

    def cancel_command(self, force=False):
        if force or tkmb.askyesno("Cancelar operación",
                                  "¿Desea cancelar la operación actual?"):
            self.data = None
            self.top.destroy()
            return True

    def confirm_command(self):
        if tkmb.askyesno("Guardar primero",
                         "¿Desea guardar los cambios antes de cerrar la ventana?"):
            return self.ok_command()
        else:
            return self.cancel_command(force=True)

    def key_f1(self):
        frame = self.get_current_frame()

        if frame is None:
            return None

        elif frame in (self.frame_step1, self.frame_step2, self.frame_step3):
            frame.show_help_popup()


class FrameSettingsStep1(ttk.Frame):
    def __init__(self, root: ttk.Notebook, app, parent):
        super().__init__(root)
        self.top = self

        self.root = root
        self.app = app
        self.parent = parent
        self.data = {}

        self.button_clear = ttk.Button(self.top, text="Vaciar lista de archivos recientes", command=self.clear)

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", state="disabled")
        self.button_prev = ttk.Button(self.top, text="Anterior", state="disabled")
        self.button_next = ttk.Button(self.top, text="Siguiente", command=self.next_tabs)
        self.button_ok = ttk.Button(self.top, text="Guardar",)

        self.parent.bind("<Control-Key-Right>", lambda _=None, self=self: self.button_next.invoke())
        self.parent.bind("<Key-Return>", lambda _=None, self=self: self.button_ok.invoke())
        self.parent.bind("<Key-Escape>", lambda _=None, self=self: self.button_cancel.invoke())
        self.parent.bind("<Control-Key-Return>", lambda _=None, self=self: self.button_next.invoke())

    def layout(self):
        self.button_clear.place(x=10, y=10, width=575, height=24)

        self.button_help.place(x=145, y=370, width=80, height=24)
        self.button_cancel.place(x=235, y=370, width=80, height=24)
        self.button_prev.place(x=325, y=370, width=80, height=24)
        self.button_next.place(x=415, y=370, width=80, height=24)
        self.button_ok.place(x=505, y=370, width=80, height=24)

    def next_tabs(self):
        self.root.select(1)

    def clear(self):
        if tkmb.askyesno(
            "Vaciar lista de archivos recientes:",
            "¿Realmente desea vaciar la lista de archivos recientes?\n"
                "Este proceso no se puede deshacer."):
            treeview = self.app.treeview

            for i in treeview.get_children():
                treeview.delete(i)

            self.app.recents_data.clear()
            self.app.recents.clear()

            self.app.save_configs()
            tkmb.showinfo(
                "Proceso completado:",
                "El proceso se completó exitosamente:\nLa lista de archivos fue vaciada."
            )

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Ajustes de Interfaz:\n\n"+HELP_DICT['AJUSTES_PASO_1'])
        popup.show()


class FrameSettingsStep2(ttk.Frame):
    def __init__(self, root, app, parent):
        super().__init__(root)
        self.top = self
        self.root = root
        self.app = app
        self.parent = parent

        self.data = None

        self.label1 = ttk.Label(
            self.top,
            text=("Seleccione el método de verificación por hash:\n"
                  "Afecta a los nuevos archivos XCIF únicamente."))
        self.label2 = ttk.Label(self.top, text="SI NO SABE QUÉ SON LAS VERIFICACIONES POR HASH, NO CAMBIE ESTAS OPCIONES.")
        self.frame_hash = ttk.LabelFrame(self.top, text="Método:")
        self.value_hash = tk.IntVar(value=self.app.config_data.get("hash", 3256))
        self.option1 = ttk.Radiobutton(self.frame_hash, text="SHA3_224", value=3224, variable=self.value_hash)
        self.option2 = ttk.Radiobutton(self.frame_hash, text="SHA3_256 (Predeterminado)", value=3256, variable=self.value_hash)
        self.option3 = ttk.Radiobutton(self.frame_hash, text="SHA3_384", value=3384, variable=self.value_hash)
        self.option4 = ttk.Radiobutton(self.frame_hash, text="SHA3_512", value=3512, variable=self.value_hash)
        self.option5 = ttk.Radiobutton(self.frame_hash, text="SHA_224", value=224, variable=self.value_hash)
        self.option6 = ttk.Radiobutton(self.frame_hash, text="SHA_256", value=256, variable=self.value_hash)
        self.option7 = ttk.Radiobutton(self.frame_hash, text="SHA_384", value=384, variable=self.value_hash)
        self.option8 = ttk.Radiobutton(self.frame_hash, text="SHA_512", value=512, variable=self.value_hash)
        self.option9 = ttk.Radiobutton(self.frame_hash, text="MD5", value=5, variable=self.value_hash)
        self.option10 = ttk.Radiobutton(self.frame_hash, text="SHA1", value=1, variable=self.value_hash)

        self.button_help = ttk.Button(self.top, text="Ayuda", command=self.show_help_popup)
        self.button_cancel = ttk.Button(self.top, text="Cancelar", )
        self.button_prev = ttk.Button(self.top, text="Anterior", command=self.prev_tabs)
        self.button_next = ttk.Button(self.top, text="Siguiente", state="disabled")
        self.button_ok = ttk.Button(self.top, text="Guardar")

        self.parent.bind("<Control-Key-Left>", lambda _=None, self=self: self.button_prev.invoke())
        self.parent.bind("<Key-Return>", lambda _=None, self=self: self.button_ok.invoke())
        self.parent.bind("<Key-Escape>", lambda _=None, self=self: self.button_cancel.invoke())
        self.parent.bind("<Control-Key-BackSpace>", lambda _=None, self=self: self.button_prev.invoke())

    def layout(self):
        self.label1.place(x=10, y=10, width=580, height=48)
        self.frame_hash.place(x=10, y=64, width=580, height=175)
        self.option1.place(x=5, y=5, width=280, height=24)
        self.option2.place(x=295, y=5, width=270, height=24)
        self.option3.place(x=5, y=35, width=280, height=24)
        self.option4.place(x=295, y=35, width=270, height=24)
        self.option5.place(x=5, y=65, width=280, height=24)
        self.option6.place(x=295, y=65, width=270, height=24)
        self.option7.place(x=5, y=95, width=280, height=24)
        self.option8.place(x=295, y=95, width=270, height=24)
        self.option9.place(x=5, y=125, width=280, height=24)
        self.option10.place(x=295, y=125, width=270, height=24)
        self.label2.place(x=10, y=250, width=580, height=24)

        self.button_help.place(x=145, y=370, width=80, height=24)
        self.button_cancel.place(x=235, y=370, width=80, height=24)
        self.button_prev.place(x=325, y=370, width=80, height=24)
        self.button_next.place(x=415, y=370, width=80, height=24)
        self.button_ok.place(x=505, y=370, width=80, height=24)

    def prev_tabs(self):
        self.root.select(0)

    def verify(self, message=True):
        self.data = {
            'hash': self.value_hash.get()
        }
        if self.data['hash'] in [1, 5, 224, 256, 384, 512, 3224, 3256, 3384, 3512]:
            return True

        else:
            tkmb.showerror("Falta información", "No se ha seleccionado ningún archivo XCIF de destino.")
            return False

    def show_help_popup(self):
        popup = PopUpHelp(self.root)
        popup.set_title('Ayuda')
        popup.set_text("Ajustes de Seguridad:\n\n"+HELP_DICT['AJUSTES_PASO_2'])
        popup.show()


class PopUpConfirmReplace(PopUp):
    def __init__(self, root):
        super().__init__(root)
        self.set_geometry("480x314")

        self.data = 0
        self.label_message1 = ttk.Label(self.top, text="El archivo ya existe, ¿Qué desea hacer?")
        self.label_message2 = ttk.Label(
            self.top,
            text="Nota: si los archivo son idénticos esta ventana no se mostrará.",
            foreground="gray"
        )

        self.labelframe_current = ttk.LabelFrame(self.top, text="Archivo Actual:")
        self.label1_name = ttk.Label(self.labelframe_current, text="Nombre:")
        self.label1_size = ttk.Label(self.labelframe_current, text="Tamaño:")

        self.label1_value_name = ttk.Label(self.labelframe_current, text="")
        self.label1_value_size = ttk.Label(self.labelframe_current, text="")

        self.labelframe_new = ttk.LabelFrame(self.top, text="Archivo a Extraer:")
        self.label2_name = ttk.Label(self.labelframe_new, text="Nombre:")
        self.label2_size = ttk.Label(self.labelframe_new, text="Tamaño:")

        self.label2_value_name = ttk.Label(self.labelframe_new, text="")
        self.label2_value_size = ttk.Label(self.labelframe_new, text="")

        self.button_replace = ttk.Button(self.top, text="Reemplazar", command=self._replace)
        self.button_ignore = ttk.Button(self.top, text="Omitir", command=self._ignore)
        self.button_rename = ttk.Button(self.top, text="Renombrar", command=self._rename)
        self.button_replace_all = ttk.Button(self.top, text="Reemplazar (Todo)", command=self._replace_all)
        self.button_ignore_all = ttk.Button(self.top, text="Omitir (Todo)", command=self._ignore_all)
        self.button_rename_all = ttk.Button(self.top, text="Renombrar (Todo)", command=self._rename_all)

        self.top.protocol(
            "WM_DELETE_WINDOW",
            lambda _=None: tkmb.showerror(
                "Imposible cerrar esta ventana",
                "La ventana actual no puede ser cerrada.\nElija la acción que el programa deba realizar.")
        )

    def _ignore(self):
        self.data = 0
        self.close()

    def _ignore_all(self):
        self.data = 3
        self.close()

    def _replace(self):
        self.data = 1
        self.close()

    def _replace_all(self):
        self.data = 4
        self.close()

    def _rename(self):
        self.data = 2
        self.close()

    def _rename_all(self):
        self.data = 5
        self.close()

    def layout(self):
        self.label_message1.place(x=10, y=10, width=460, height=24)

        self.labelframe_current.place(x=10, y=40, width=460, height=80)
        self.label1_name.place(x=5, y=2, width=50, height=24)
        self.label1_value_name.place(x=55, y=2, width=400, height=24)
        self.label1_size.place(x=5, y=32, width=50, height=24)
        self.label1_value_size.place(x=55, y=32, width=400, height=24)

        self.labelframe_new.place(x=10, y=130, width=460, height=80)
        self.label2_name.place(x=5, y=2, width=50, height=24)
        self.label2_value_name.place(x=55, y=2, width=400, height=24)
        self.label2_size.place(x=5, y=32, width=50, height=24)
        self.label2_value_size.place(x=55, y=32, width=400, height=24)

        self.label_message2.place(x=10, y=220, width=460, height=24)

        self.button_replace.place(x=10, y=250, width=140, height=24)
        self.button_ignore.place(x=160, y=250, width=140, height=24)
        self.button_rename.place(x=310, y=250, width=140, height=24)

        self.button_replace_all.place(x=10, y=280, width=140, height=24)
        self.button_ignore_all.place(x=160, y=280, width=140, height=24)
        self.button_rename_all.place(x=310, y=280, width=140, height=24)

    def show(self):
        self.layout()
        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self.root)
        self.root.wait_window(self.top)

    def set_info(self, name1, name2, size1, size2):
        self.label1_value_name['text'] = name1
        self.label2_value_name['text'] = name2
        self.label1_value_size['text'] = size1
        self.label2_value_size['text'] = size2

    def close(self):
        self.top.destroy()

    @staticmethod
    def as_message_box(path, size, filehash, root=None):
        popup = PopUpConfirmReplace(root)
        popup.set_title("Operación interrumpida: ¿Qué desea hacer?")
        current_file_size = os.path.getsize(path)
        popup.set_info(
            path.decode(),
            os.path.basename(path.decode()),
            f"{xcif.xmaker.get_size_unit(current_file_size)} ({current_file_size}B)",
            f"{xcif.xmaker.get_size_unit(size)} ({size}B)"
        )
        popup.show()
        return popup.data


# Funciones:
def get_datetime_format(seconds):
    struct = time.strptime(time.ctime(seconds), "%a %b %d %H:%M:%S %Y")
    return time.strftime("%d/%m/%Y - %H:%M", struct)


def configure_size(root, app):
    app.place(width=root.winfo_width(),
              height=root.winfo_height())

    app.configure_layout()


def start_window(**kwargs):
    root = tk.Tk()
    root.minsize(700, 400)

    app = ApplicationFrame(root, **kwargs)
    app.place(x=0, y=0, width=700, height=400)

    root.bind("<Configure>", lambda event=None, root=root, app=app: configure_size(root, app))
    root.mainloop()


if __name__ == '__main__':
    start_window()
