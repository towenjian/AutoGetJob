import os
import sys
import tomllib
import tomli_w
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime

log_dir = '../logs'


class ColoredFormatter(logging.Formatter):
    """
    一个自定义的Formatter，为日志级别名称和消息主体添加颜色。
    """
    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'

    # 基础格式字符串
    BASE_FORMAT = '[%(asctime)s][%(name)s][%(levelname)s]: %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        super().__init__(fmt=self.BASE_FORMAT, datefmt=self.DATE_FORMAT)

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        original_levelname = record.levelname
        if log_color:
            record.levelname = f"{log_color}{original_levelname}{self.RESET}"
        record.levelname = original_levelname
        colored_levelname = f"{log_color}{original_levelname}{self.RESET}"
        base_log = logging.Formatter(self.BASE_FORMAT, self.DATE_FORMAT).format(record)
        colored_log = base_log.replace(original_levelname, colored_levelname, 1)
        message_start_index = colored_log.find(': ') + 2
        return colored_log[:message_start_index] + log_color + colored_log[message_start_index:] + self.RESET

def setup_logging(level=logging.INFO):
    os.makedirs(log_dir, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    colored_formatter = ColoredFormatter()
    handler.setFormatter(colored_formatter)
    FILE_FORMAT = '[%(asctime)s][%(name)s][%(levelname)s]: %(message)s'
    FILE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    file_formatter = logging.Formatter(FILE_FORMAT, datefmt=FILE_DATE_FORMAT)

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, f'{today}.log'),
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    # 设置文件处理器的格式
    file_handler.setFormatter(file_formatter)

    # 清除旧的处理器并添加新的
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)


setup_logging()


class Config:
    config_all = tomllib.load(open('../config.toml', 'rb'))
    def __init__(self, name):
        self.name = name
        self.config = Config.config_all.get(name, None)

    def save(self):
        # 检查与主配置的配置项是否一致
        for k, v in self.config.items():
            if k not in Config.config_all[self.name]:
                Config.config_all[self.name][k] = v
                logging.info(f"Add new config item {k} to {self.name}")
        Config.save_config()

    def __getitem__(self, item):
        if self.config is None:
            raise KeyError(f"Config {self.name} not found")
        return self.config[item]

    def __setitem__(self, key, value):
        if self.config is None:
            raise KeyError(f"Config {self.name} not found")
        self.config[key] = value

    def __contains__(self, item):
        if self.config is None:
            return False
        return item in self.config

    @staticmethod
    def save_config():
        with open('../config.toml', 'wb') as f:
            tomli_w.dump(Config.config_all, f)