import sqlite3
from pathlib import Path
from typing import Union, Optional

import pymysql
from mlcbase import Logger, ConfigDict, MySQLAPI, SQLiteAPI, SMTPAPI, SFTP, is_str

from .utils import ConfigFile, MLCSecretEngine

PathLikeType = Union[str, Path]


class Database:
    BACKENDS = ["mysql", "sqlite"]

    def __init__(self, config: Union[str, Path, ConfigFile], logger: Optional[Logger] = None):
        if logger is None:
            self.logger = Logger()
            self.logger.init_logger()
        else:
            self.logger = logger

        if isinstance(config, (str, Path)):
            self.__cfg = ConfigFile(config)
        else:
            self.__cfg = config

        assert self.__cfg.backend.database.backend in self.BACKENDS, \
            f"Backend {self.__cfg.backend.database.backend} is not supported"
        assert self.__cfg.backend.database.connect.method == "direct", "Only 'direct' connection methods are supported"
        
        self.api = self.__connect()
        self.secret = MLCSecretEngine(timezone=self.__cfg.backend.timezone, logger=self.logger)

    def __connect(self):
        if self.__cfg.backend.database.backend == "mysql":
            # check if database and tables exist
            self.logger.info(f"Checking if database '{self.__cfg.backend.database.name}' exists...")
            if self.__cfg.backend.database.connect.method == "direct":
                conn = pymysql.connect(host=self.__cfg.backend.database.connect.host, 
                                       port=self.__cfg.backend.database.connect.port,
                                       user=self.__cfg.backend.database.connect.username,
                                       password=self.__cfg.backend.database.connect.password)
                charset = self.__cfg.backend.database.connect.charset if self.__cfg.backend.database.connect.charset else "utf8"
            cursor = conn.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{self.__cfg.backend.database.name}'")
            exists_db = cursor.fetchall()
            conn.commit()
            if len(exists_db) == 0:
                # create database
                cursor.execute(f"CREATE DATABASE {self.__cfg.backend.database.name} CHARACTER SET {charset}")
                conn.commit()
                self.logger.success(f"Database '{self.__cfg.backend.database.name}' created")
                cursor.execute(f"USE {self.__cfg.backend.database.name}")
                conn.commit()
                # create tables
                for table_name, table_config in self.__cfg.backend.database.tables.items():
                    sql = f"CREATE TABLE {table_name}("
                    primary_key = []
                    for field in table_config:
                        field = ConfigDict(field)
                        command = [field.name]
                        command.append(field.dtype.upper())
                        if field.get("primary_key", False):
                            primary_key.append(field.name)
                        if field.get("auto_increment", False):
                            command.append("AUTO_INCREMENT")
                        if field.get("not_null", False):
                            command.append("NOT NULL")
                        if field.default is not None:
                            if is_str(field.default):
                                command.append(f"DEFAULT '{field.default}'")
                            else:
                                command.append(f"DEFAULT {field.default}")
                        sql += " ".join(command) + ","
                    if len(primary_key) > 0:
                        sql += f"PRIMARY KEY ({','.join(primary_key)}))"
                    else:
                        sql = sql.strip(",") + ")"
                    sql += f"ENGINE=InnoDB DEFAULT CHARSET={charset}"
                    cursor.execute(sql)
                    conn.commit()
                    self.logger.success(f"Table '{table_name}' created")
            else:
                # check if tables exist
                self.logger.info(f"Database '{self.__cfg.backend.database.name}' already exists")
                cursor.execute(f"USE {self.__cfg.backend.database.name}")
                conn.commit()
                cursor.execute("SHOW TABLES")
                exists_table = cursor.fetchall()
                conn.commit()
                for table_name, table_config in self.__cfg.backend.database.tables.items():
                    self.logger.info(f"Checking if table '{table_name}' exists...")
                    if len(tuple(filter(lambda x: x[0] == table_name, exists_table))) > 0:
                        self.logger.info(f"Table '{table_name}' already exists")
                    else:
                        sql = f"CREATE TABLE {table_name}("
                        primary_key = []
                        for field in table_config:
                            field = ConfigDict(field)
                            command = [field.name]
                            command.append(field.dtype.upper())
                            if field.get("primary_key", False):
                                primary_key.append(field.name)
                            if field.get("auto_increment", False):
                                command.append("AUTO_INCREMENT")
                            if field.get("not_null", False):
                                command.append("NOT NULL")
                            if field.default is not None:
                                if is_str(field.default):
                                    command.append(f"DEFAULT '{field.default}'")
                                else:
                                    command.append(f"DEFAULT {field.default}")
                            sql += " ".join(command) + ","
                        if len(primary_key) > 0:
                            sql += f"PRIMARY KEY ({','.join(primary_key)}))"
                        else:
                            sql = sql.strip(",") + ")"
                        sql += f"ENGINE=InnoDB DEFAULT CHARSET={charset}"
                        cursor.execute(sql)
                        conn.commit()
                        self.logger.success(f"Table '{table_name}' created")
            cursor.close()
            conn.close()
            
            # load database API
            if self.__cfg.backend.database.connect.method == "direct":             
                db_api =  MySQLAPI(host=self.__cfg.backend.database.connect.host,
                                   port=self.__cfg.backend.database.connect.port,
                                   user=self.__cfg.backend.database.connect.username,
                                   database=self.__cfg.backend.database.name,
                                   password=self.__cfg.backend.database.connect.password,
                                   charset=self.__cfg.backend.database.connect.charset if self.__cfg.backend.database.connect.charset else "utf8",
                                   logger=self.logger)

        if self.__cfg.backend.database.backend == "sqlite":
            if self.__cfg.backend.database.connect.in_memory:
                path = ":memory:"
            else:
                path = self.__cfg.backend.database.connect.path
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            exists_table = cursor.fetchall()
            conn.commit()
            for table_name, table_config in self.__cfg.backend.database.tables.items():
                self.logger.info(f"Checking if table '{table_name}' exists...")
                if len(tuple(filter(lambda x: x[0] == table_name, exists_table))) > 0:
                    self.logger.info(f"Table '{table_name}' already exists")
                else:
                    primary_key_num = 0
                    has_auto_increment = False
                    for field in table_config:
                        field = ConfigDict(field)
                        if field.get("primary_key", False):
                            primary_key_num += 1
                        if field.get("auto_increment", False):
                            has_auto_increment = True
                    if primary_key_num > 1 and has_auto_increment:
                        self.logger.warning("SQLite does not support creating a table with multiple primary keys and "
                                            "auto increment field at the same time.")
                        raise SyntaxError("SQLite does not support creating a table with multiple primary keys and "
                                        "auto increment field at the same time.")
                    sql = f"CREATE TABLE {table_name} ("
                    primary_key = []
                    for field in table_config:
                        field = ConfigDict(field)
                        command = [field.name]
                        command.append(field.dtype.upper())
                        if field.get("primary_key", False):
                            primary_key.append(field.name)
                            if primary_key_num == 1:
                                command.append("PRIMARY KEY")
                        if field.get("auto_increment", False):
                            if field.dtype.upper() != "INTEGER" or not field.get("primary_key", False):
                                self.logger.error("AUTOINCREMENT is only allowed on an INTEGER PRIMARY KEY")
                                raise SyntaxError("AUTOINCREMENT is only allowed on an INTEGER PRIMARY KEY")
                            command.append("AUTOINCREMENT")
                        if field.get("not_null", False):
                            command.append("NOT NULL")
                        if field.default is not None:
                            if is_str(field.default):
                                command.append(f"DEFAULT '{field.default}'")
                            else:
                                command.append(f"DEFAULT {field.default}")
                        sql += " ".join(command) + ","
                    
                    if len(primary_key) > 1:
                        sql += f"PRIMARY KEY ({','.join(primary_key)}))"
                    else:
                        sql = sql.strip(",") + ")"
                    cursor.execute(sql)
                    conn.commit()
                    self.logger.success(f"Table '{table_name}' created")
            cursor.close()
            conn.close()

            # load database API
            db_api =  SQLiteAPI(db_path=self.__cfg.backend.database.connect.path, 
                                in_memory=self.__cfg.backend.database.connect.in_memory, 
                                logger=self.logger)
        
        return db_api
    
    def ping(self):
        try:
            self.api.ping()
            self.logger.success("Database ping success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to ping Database: {str(e)}")
            return False
    
    def close(self):
        self.api.close()
        self.secret.close()
        self.logger.info("Database closed")


class EmailServer:
    BACKENDS = ["smtp",]
    SIGNATURE = """<div style="font-family: Microsoft YaHei; font-size: 14px;">Thanks for using MuLingCloud</div>
                   <div style="margin-top: 10px;margin-bottom: 10px;">----</div>
                   <div style="margin-bottom: 10px;">
                        <a href="https://github.com/mulingcloud/mlcbase">
                            <img src="https://img.shields.io/badge/github_repository-888888?logo=github&logoColor=black" />
                        </a>
                        <a href="https://gitlab.com/wm-chen/mlcbase">
                            <img src="https://img.shields.io/badge/gitlab_repository-888888?logo=gitlab" />
                        </a>
                        <a href="https://gitee.com/mulingcloud/mlcbase">
                            <img src="https://img.shields.io/badge/gitee_repository-888888?logo=gitee&logoColor=C71D23" />
                        </a>
                   </div>
                   <div style="font-family: Microsoft YaHei; font-size: 16px; font-weight: bold;margin-bottom: 10px">MuLingCloud</div>
                   <div style="font-family: Microsoft YaHei; font-size: 14px; margin-bottom: 5px;">
                        <span style="font-weight: bold;">Email:</span> <a href="mailto:mulingcloud@yeah.net">mulingcloud@yeah.net</a>, 
                        <a href="mailto:mulingcloud@163.com">mulingcloud@163.com</a>
                   </div>
                   <div style="font-family: Microsoft YaHei; font-size: 14px; margin-bottom: 20px;">
                        <span style="font-weight: bold;">Office Time:</span> Asia/Shanghai, 9:00-18:00, Mon.-Fri.
                   </div>
                   <a href="https://www.mulingcloud.com" style="text-decoration: none;">
                        <img src="https://lychee.weimingchen.net:666/uploads/original/ab/f5/9b1e4627612dbd70aa62a1ae5370.png" height="50px">
                   </a>"""

    def __init__(self, config: Union[str, Path, ConfigFile], logger: Optional[Logger] = None):
        if logger is None:
            self.logger = Logger()
            self.logger.init_logger()
        else:
            self.logger = logger

        if isinstance(config, (str, Path)):
            self.__cfg = ConfigFile(config)
        else:
            self.__cfg = config

        assert self.__cfg.backend.email.backend in self.BACKENDS, \
            f"Backend {self.__cfg.backend.email.backend} is not supported"
        assert self.__cfg.backend.email.connect.method == "direct", "Only 'direct' connection methods are supported"

        self.api = self.__connect()
        
    def __connect(self):
        if self.__cfg.backend.email.backend == "smtp":
            if self.__cfg.backend.email.connect.method == "direct":
                email_server = SMTPAPI(host=self.__cfg.backend.email.connect.host,
                                       port=self.__cfg.backend.email.connect.port,
                                       name=self.__cfg.backend.email.sender_name,
                                       address=self.__cfg.backend.email.connect.address,
                                       password=self.__cfg.backend.email.connect.password,
                                       logger=self.logger)
        return email_server
    
    def ping(self):
        try:
            self.api.noop()
            self.logger.success("Email server ping success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to ping email server: {str(e)}")
            return False
    
    def close(self):
        self.api.close()


class SFTPAPI:
    def __init__(self, 
                 config: Union[str, Path, ConfigFile], 
                 logger: Optional[Logger] = None):
        if logger is None:
            self.logger = Logger()
            self.logger.init_logger()
        else:
            self.logger = logger

        if isinstance(config, (str, Path)):
            self.__cfg = ConfigFile(config)
        else:
            self.__cfg = config

        assert self.__cfg.backend.sftp is not None, "SFTP backend is not configured"

        self.api = self.__connect()

    def __connect(self):
        if self.__cfg.backend.sftp.connect.method == "direct":
            sftp = SFTP(host=self.__cfg.backend.sftp.connect.host,
                        port=self.__cfg.backend.sftp.connect.port,
                        user=self.__cfg.backend.sftp.connect.user,
                        password=self.__cfg.backend.sftp.connect.password,
                        logger=self.logger)
            self.remote_root = self.__cfg.backend.sftp.connect.remote_root
            self.remote_platform = self.__cfg.backend.sftp.connect.remote_platform
        return sftp
    
    def ping(self):
        if self.remote_root is not None:
            try:
                self.api.remote_exists(self.remote_root, self.remote_platform)
                self.logger.success("SFTP ping success")
                return True
            except Exception as e:
                self.logger.error(f"Failed to ping SFTP: {str(e)}")
        else:
            self.logger.warning("Remote root is not set, cannot ping")
        return False

    def close(self):
        self.api.close()
