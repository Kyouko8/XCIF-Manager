# XData
# 01:07 a.m. 09/11/2020
# Medina Dylan
# XData (Datos de configuración de XTKViewer)

def load_config(filename: str):
    """
    Load config-data from a file.
    """
    data = {}
    with open(filename, "rb") as r:
        line = r.readline()
        while line != b"":
            if b"\x01" in line:
                k, v = line.split(b"\x01", 1)
                try:
                    k = k.decode()
                except UnicodeDecodeError:
                    pass

                try:
                    v = v.decode()
                except UnicodeDecodeError:
                    pass

                data[k] = v

            line = r.readline()

    return data


def save_config(filename: str, data: dict):
    """
    Save config-data into a file
    """
    with open(filename, "wb") as w:
        for k, v in data.items():
            if not isinstance(k, bytes):
                k = str(k).encode()
            if not isinstance(v, bytes):
                v = str(v).encode()

            w.write(k+b"\x01"+v+b"\n")
