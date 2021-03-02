# XLIB > XHASH
# 07:51 p.m. 23/09/2020
# Medina Dylan
# XHASH (X-Hash)

import hashlib
import random


def get_hash_of_key(key, method=hashlib.sha3_256):
    return method(key).hexdigest()


def get_my_hash(hash_base, len_key):
    new_hash = ""
    int_hash = int(hash_base, 16)
    set_seed(int_hash - len_key*256)

    last_number = (int(hash_base[-1], 16) + len_key) % 8

    if last_number == 0:
        for i in hash_base.lower():
            if i == "f":
                new_hash += "a"
            elif i == "a":
                new_hash += "f"
            else:
                new_hash += i

    elif last_number == 1:
        for i in hash_base.lower():
            if i == "1":
                new_hash += "8"
            elif i == "8":
                new_hash += "1"
            else:
                new_hash += i

    elif last_number == 2:
        for i in hash_base.lower():
            if i in ("1", "2", "5"):
                new_hash = new_hash + i
            else:
                new_hash = new_hash[::-1] + i

    elif last_number == 3:
        for i in hash_base.lower():
            if i == "e":
                new_hash += "4"
            elif i == "4":
                new_hash += "e"
            else:
                new_hash += i

    elif last_number == 4:
        for i in hash_base.lower():
            if i == "9":
                new_hash += "8"
            elif i == "8":
                new_hash += "9"
            else:
                new_hash += i

    elif last_number == 5:
        for i in hash_base.lower():
            if i in ("3", "6", "8"):
                new_hash = new_hash + i
            else:
                new_hash = new_hash[::-1] + i

    elif last_number == 6:
        for i in hash_base.lower():
            if i == "b":
                new_hash += "7"
            elif i == "7":
                new_hash += "b"
            else:
                new_hash += i

    elif last_number == 7:
        for i in hash_base.lower():
            if i in ("1", "2", "5", "7", "9", "a", "b", "f"):
                new_hash = new_hash[::-1] + i
            else:
                new_hash += i

    new_hash = "".join(random.sample(list(new_hash), len(new_hash)))
    set_seed(len_key*int(new_hash, base=16))
    new_hash = "".join(random.sample(list(new_hash), len(new_hash)))

    return hashlib.sha3_512(new_hash.encode()).hexdigest()


def set_seed(seed_number):
    seed_number = round(seed_number / 1000000000000000) - 42
    random.seed(seed_number)


def get_table_of_characters(hash_base, len_key, my_hash):
    int_hash_base = int(hash_base, base=16)
    int_my_hash = int(my_hash, base=16)

    random.seed(int_hash_base-len_key)
    random_number1 = random.randint(2, 60000000000) * len_key

    random.seed(abs(int_my_hash-int_hash_base))
    random_number2 = random.random() * (6000000000 * len_key)

    random.seed(int(abs(random_number1+random_number2)*len_key))
    random_number3 = random.randint(
        3, 800000000000000000000000000000) * len_key

    random.seed(int_my_hash * random_number3 - len_key * 80)
    table = random.sample(list(range(256)), 256)
    table = map(lambda x: bytes((x,)), table)
    return tuple(table)
