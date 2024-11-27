from abc import abstractmethod
from pathlib import Path
from typing import Union, Optional

from mlcbase import Logger

from .frontend import Login
from .backend import ConfigFile


class Controller:
    def __init__(self, config: Union[str, Path, ConfigFile], logger: Optional[Logger] = None):
        if isinstance(config, (str, Path)):
            self.cfg = ConfigFile(config)
        else:
            self.cfg = config
        if logger is None:
            self.logger = Logger()
            self.logger.init_logger()
        else:
            self.logger = logger

    def show_login(self):
        self.login = Login(self.cfg, self.logger)
        self.login.loginSuccessSignal.connect(self.show_app)
        self.login.show()

    @abstractmethod
    def show_app(self, apis, cfg):
        ...
