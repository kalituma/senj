import logging

logger_level_map = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def print_log_attrs(self, level):
    for attr in self.__dict__:
        if attr not in ['_listeners', '_counter', '_logger', '__len__']:
            self._logger.log(level, f'({self.__class__.__name__}) {attr} : {getattr(self, attr)}')

class Logger:
    _instance = None

    def __new__(cls, log_level, log_file_path):
        if cls._instance is None:
            assert log_file_path is not None, 'Log file path is required at the first time of logger initialization'
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.setup_logger(log_level, log_file_path)
        return cls._instance

    def setup_logger(self, logging_level, log_file_path):
        assert logging_level in logger_level_map.keys(), f'Invalid logging level: {logging_level}'

        self.logger = logging.getLogger('senj')
        self.logger.setLevel(logger_level_map[logging_level])

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger_level_map[logging_level])

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logger_level_map[logging_level])

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, level, msg):
        level = level.lower()
        log_method = getattr(self.logger, level)
        log_method(msg)

    @classmethod
    def get_logger(cls, log_level='debug', log_file_path:str=None):
        return cls(log_level, log_file_path)