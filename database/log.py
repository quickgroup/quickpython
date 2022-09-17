

def get_logger():
    from quickpython.component.log import LoggingManger
    return LoggingManger.getLogger(LoggingManger.DATABASE)