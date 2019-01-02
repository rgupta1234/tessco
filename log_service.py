import logging
import arrow


class LogService:
    logger = None

    def __init__(self, log_path, client_tpid, log_level):
        self.logger = logging.getLogger('VMI Application Log')
        handler = logging.FileHandler(filename=log_path + client_tpid + '_' + str(arrow.now().format('MM-DD-YYYY'))
                                               + '.log')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.logger.addHandler(hdlr=handler)
        self.logger.setLevel(level=self._get_log_level(log_level=log_level))

    @staticmethod
    def _get_log_level(log_level):
        return {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'NOTSET': logging.NOTSET
        }.get(log_level, logging.DEBUG)
