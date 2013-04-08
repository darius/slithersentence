import logging

def set_up_logger(logging_flag):
    '''Setting up of logger is moved to this method for neatness.'''
    # Set the logging level; standard choices: 
    # DEBUG, INFO, WARN, ERROR, CRITICAL. Our default is WARN.
    log_levels = {
            '-d': logging.DEBUG,
            '-i': logging.INFO,
            '-e': logging.ERROR,
            '-c': logging.CRITICAL}
    if logging_flag in log_levels:
        the_level = log_levels[logging_flag]
    else:
        the_level = logging.WARN
    #
    # Set the application name and logger configuration.
    # We don't want the .py extension.
    app_name = __file__.split('.')[0]
    logging.basicConfig(
            format='%(asctime)s (' + app_name + '.%(funcName)s:%(lineno)d) '
                '%(levelname)s: %(message)s', 
            datefmt='%Y%d%m_%H:%M:%S_%Z', 
            filename=app_name+'.log',
            level=the_level)
