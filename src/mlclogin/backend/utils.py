import os
import shutil
import base64
import json
from pathlib import Path
from typing import Union, Optional, Sequence

import pytz
import toml
import numpy as np
from PIL import Image
from mlcbase import (Logger, ConfigDict, SQLiteAPI, listdir, aes_encrypt_text, 
                     aes_decrypt_text, random_hex)

PathLikeType = Union[str, Path]


class ConfigFile(ConfigDict):
    def __init__(self, path: PathLikeType):
        assert Path(path).exists(), f"Config file '{path}' does not exist"
        self.parse(self, Path(path))

    def parse(self, cfg, path):
        if path.is_dir():
            for p in listdir(path, return_path=False):
                self.parse(cfg, path / p)
        else:
            if path.suffix == ".toml":
                key_name = os.path.basename(path)[:-5]
                cfg[key_name] = ConfigDict(toml.load(path))


class MLCSecretEngine:
    def __init__(self, 
                 timezone: str, 
                 nic_name: Optional[str] = None, 
                 logger: Optional[Logger] = None):
        """MuLingCloud Secret Engine

        Args:
            timezone (str): the timezone of local machine
            nic_name (Optional[str]): the name of network interface card. Defaults to None.
            logger (Optional[Logger]): Defaults to None.
        """
        assert timezone in pytz.all_timezones, f"Invalid timezone: {timezone}"
        
        if logger is None:
            self.logger = Logger()
            self.logger.init_logger()
        else:
            self.logger = logger

        self.timezone = timezone
        self.nic_name = nic_name
        self.__token = random_hex(48)
        self.__secret_db = SQLiteAPI(in_memory=True, quiet=True)
        self.__secret_db.create_table(
            table_name="secret",
            table_config=[dict(name="id", dtype="INTEGER", not_null=True, primary_key=True, auto_increment=True),
                          dict(name="domain", dtype="TEXT", not_null=True),
                          dict(name="name", dtype="TEXT", not_null=True),
                          dict(name="secret", dtype="TEXT", not_null=True)]
        )

    def get_secret(self, domain: str, name: str):
        try:
            domain = self.__encrypt_with_token(domain)
            name = self.__encrypt_with_token(name)
            secret = self.__secret_db.search_data(table_name="secret", fields="secret", 
                                                  condition=f"domain='{domain}' AND name='{name}'")[0][0]
            secret = self.__decrypt_with_token(secret)
            return secret
        except:
            return None
        
    def save_secret(self, domain: str, name: str, secret: str):
        domain = self.__encrypt_with_token(domain)
        name = self.__encrypt_with_token(name)
        secret = self.__encrypt_with_token(secret)
        self.__secret_db.insert_data(table_name="secret", data=dict(domain=domain, name=name, secret=secret))
    
    def delete_secret(self, domain: str, name: Optional[str] = None):
        domain = self.__encrypt_with_token(domain)
        if name is None:
            self.__secret_db.delete_data(table_name="secret", condition=f"domain='{domain}'")
        else:
            name = self.__encrypt_with_token(name)
            self.__secret_db.delete_data(table_name="secret", condition=f"domain='{domain}' AND name='{name}'")
        
    def __encrypt_with_token(self, plain: str):
        iv = self.__token[:16]
        key = self.__token[16:]
        return base64.urlsafe_b64encode(aes_encrypt_text(plain, key, iv)).decode("utf-8")
    
    def __decrypt_with_token(self, cipher: str):
        iv = self.__token[:16]
        key = self.__token[16:]
        return aes_decrypt_text(base64.urlsafe_b64decode(cipher), key, iv)

    def close(self):
        self.__secret_db.close()


def get_table_field_index(cfg: ConfigFile, domain: str, table_name: str, field_name: str):
    table = cfg[domain]["database"]["tables"][table_name]
    for index, field in enumerate(table):
        if field["name"] == field_name:
            return index
        

def load_image_from_path(path: str, 
                         size: Sequence = (512, 512), 
                         offsets: Sequence = (0, 0, 0, 0), 
                         color_mode: str = "RGB"):
    """load image from local path and perform center crop if necessary

    Args:
        path (str): local path
        size (Sequence, optional): target image size (width, height). Defaults to (512, 512).
        offsets (Sequence, optional): offsets before center crop, (left, top, right, bottom). 
                                      Defaults to (0, 0, 0, 0).
        color_mode (str, optional): color mode. Defaults to "RGB".

    Returns:
        pil.Image: image
    """
    image = np.array(Image.open(path).convert(color_mode))

    # perform cropping using offsets
    h, w, _ = image.shape
    left = min(offsets[0], w - 1)
    top = min(offsets[1], h - 1)
    right = min(w - 1, w - offsets[2])
    bottom = min(h - 1, h - offsets[3])
    image = image[top:bottom, left:right, :]

    # perform center crop
    h, w, _ = image.shape
    if h > w:
        image = image[(h - w) // 2: (h - w) // 2 + w, :, :]
    elif h < w:
        image = image[:, (w - h) // 2: (w - h) // 2 + h, :]
        
    image = Image.fromarray(image)
    image = image.resize(size)
    return image


def clear_cache(logger: Optional[Logger] = None):
    cache_dir = Path(__file__).parent.parent.parent.parent / "cache"
    for filepath in listdir(cache_dir, logger=logger):
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)
        else:
            raise NotImplementedError(f"unknown file type: {filepath}")
