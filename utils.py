import logging


class logger:
    def __init__(self, name, to_file=False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if to_file:
            file_handler = logging.FileHandler('log.txt', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.debug('Logger initialized')

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)


def _hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h * 6.)  # XXX assume int() truncates!
    f = (h * 6.) - i
    p, q, t = v * (1. - s), v * (1. - s * f), v * (1. - s * (1. - f))
    i %= 6
    if i == 0:
        return 255 * v, 255 * t, 255 * p
    if i == 1:
        return 255 * q, 255 * v, 255 * p
    if i == 2:
        return 255 * p, 255 * v, 255 * t
    if i == 3:
        return 255 * p, 255 * q, 255 * v
    if i == 4:
        return 255 * t, 255 * p, 255 * v
    if i == 5:
        return 255 * v, 255 * p, 255 * q


if __name__ == '__main__':
    logger = logger('test', to_file=True)
    logger.debug('Testing debug')
    logger.info('Testing info')
    logger.warning('Testing warning')
    logger.error('Testing error')
    logger.critical('Testing critical')
