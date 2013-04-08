import logging

def set_up_logger(app_name, logging_flag):
    '''Set the logging level from a command-line switch. Default WARN.'''
    log_levels = {
            '-d': logging.DEBUG,
            '-i': logging.INFO,
            '-e': logging.ERROR,
            '-c': logging.CRITICAL}
    the_level = log_levels.get(logging_flag, logging.WARN)

    logging.basicConfig(
            format='%(asctime)s (' + app_name + '.%(funcName)s:%(lineno)d) '
                '%(levelname)s: %(message)s', 
            datefmt='%Y%d%m_%H:%M:%S_%Z', 
            filename=app_name+'.log',
            level=the_level)

def percentage(numerator, denominator):
    '''Return numerator/denominator as a percentage (no decimals).'''
    if 0 == denominator:
        return 0               # XXX better to make this float('nan')?
    else:
        return round(100 * numerator / denominator)
