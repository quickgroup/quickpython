

def get_logger():
    import logging
    logger = logging.getLogger(str(__name__).split('.')[0] + ".database")
    return logger