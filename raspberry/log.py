import datetime

class Logs (object):
    """
    Print log files into the "logs" directory. 
    """
    def __init__(self):
        pass
    
    def log(source, msg):
        with open('/home/pi/smart_IoT-Vertical-Farm/logs/logs.trace', 'a') as log_file:
            log_file.write(f'[{str(datetime.datetime.now())}]  -   [{source}] {msg}\n')
    def error(source, msg):
        with open('/home/pi/smart_IoT-Vertical-Farm/logs/errorlog.trace', 'a') as errors:
            errors.write(f'[{str(datetime.datetime.now())}]  -   [{source}] {msg}\n')

    def cleanLogs():
        """
        Methods to clean all the log
        """
        with open('/home/pi/smart_IoT-Vertical-Farm/logs/logs.trace', 'w') as log_file:
            log_file.write(f'[{str(datetime.datetime.now())}]  -   Start logging \n')
        with open('/home/pi/smart_IoT-Vertical-Farm/logs/errorlog.trace', 'w') as log_file:
            log_file.write(f'[{str(datetime.datetime.now())}]  -   Start logging \n')