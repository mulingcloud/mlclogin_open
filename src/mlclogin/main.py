import importlib.util
import sys
import importlib
from pathlib import Path
from datetime import datetime

import pytz
from mlcbase import Logger, create, parse_version
from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

from .backend import ConfigFile, clear_cache
from .controller import Controller
from .frontend.common import resource_rc

ROOT_DIR = Path(__file__).parent.parent.parent


def run():
    cfg = ConfigFile(ROOT_DIR / "config")

    now_time = datetime.now(tz=pytz.timezone(cfg.backend.timezone)).strftime("%Y%m%d_%H%M%S")
    log_dir = ROOT_DIR / "log"
    cache_dir = ROOT_DIR / "cache"
    create(log_dir, ftype="dir")
    create(cache_dir, ftype="dir")
    logger = Logger()
    logger.init_logger(log_dir/f"{now_time}.log")
    
    # check language
    if cfg.frontend.language not in cfg.frontend.supported_languages:
        logger.warning(f"Unsupported language: {cfg.frontend.language}, "
                       f"use default language ({cfg.frontend.default_language}) instead")
        cfg.frontend.language = cfg.frontend.default_language
        
    # check dependencies version
    for k in cfg.module.dependencies.keys():
        module_name = cfg.module.dependencies[k].name
        if importlib.util.find_spec(module_name) is not None:
            module = importlib.import_module(module_name)
            module_version = module.__version__
        else:
            module_version_path = ROOT_DIR / "src" / module_name / "__init__.py"
            with open(module_version_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = f.readline().strip("\n")
                    if line.startswith("__version__"):
                        module_version = line.split("=")[1].strip().strip("\"")
                        break
        module_version = parse_version(module_version)
        if cfg.module.dependencies[k].version is not None:
            static_version = parse_version(cfg.module.dependencies[k].version)
            if module_version != static_version:
                logger.error(f"Module {module_name} version mismatch: {module_version} != {static_version}")
                return
        if cfg.module.dependencies[k].min_version is not None:
            min_version = parse_version(cfg.module.dependencies[k].min_version)
            if module_version < min_version:
                logger.error(f"Module {module_name} version is too old: {module_version} < {min_version}")
                return
        if cfg.module.dependencies[k].max_version is not None:
            max_version = parse_version(cfg.module.dependencies[k].max_version)
            if module_version > max_version:
                logger.error(f"Module {module_name} version is too new: {module_version} > {max_version}")
                return
    
    # start app
    app = QApplication(sys.argv)
    if cfg.frontend.language == "zh_CN":
        translator = QTranslator()
        translator.load(":/login/translation/zh_CN.qm")
        app.installTranslator(translator)
    controller = Controller(cfg, logger)
    controller.show_login()
    app.exec()

    if cfg.backend.auto_clear_cache:
        clear_cache(logger)
