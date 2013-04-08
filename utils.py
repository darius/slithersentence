import logging

def set_up_logger(app_name, logging_flag):
    '''Setting up of logger is moved to this method for neatness.'''
    # Set the logging level; standard choices: 
    # DEBUG, INFO, WARN, ERROR, CRITICAL. Our default is WARN.
    log_levels = {
            '-d': logging.DEBUG,
            '-i': logging.INFO,
            '-e': logging.ERROR,
            '-c': logging.CRITICAL}
    the_level = log_levels.get(logging_flag, logging.WARN)
    #
    # Set the logger configuration.
    logging.basicConfig(
            format='%(asctime)s (' + app_name + '.%(funcName)s:%(lineno)d) '
                '%(levelname)s: %(message)s', 
            datefmt='%Y%d%m_%H:%M:%S_%Z', 
            filename=app_name+'.log',
            level=the_level)
