import DeviceAgent
import json
import datetime
import sys
sys.path.insert(0,'/home/pi/smart_IoT-Vertical-Farm')
from log import Logs

class DeviceAgentCSV(DeviceAgent.deviceAgent):
    def __init__(self, variables, input_file_name, input_file_path, input_file_extension='csv', separator=';', ipaddress = '127.0.0.1'):
        super().__init__(ipaddress)
        self.input_file_name = input_file_name
        self.input_file_path = input_file_path
        self.input_file_extension = input_file_extension
        self.separator = separator
        self.variables = variables


    def readData(self):
        """
        Returns a dictionary with the variable and its value (key:value)
        """
        information = {}

        file = self.input_file_path + '/' + self.input_file_name + '.' + self.input_file_extension  # Build the final path
        Logs.log("DEVICE AGENT CSV", f"Reading file {str(file)}")
        # self.writeLog('Read file ' + str(file))
        data_raw = str(self.readFile(file))    # read the data from the file, return a string. The cast to string is unecessary
        Logs.log("DEVICE AGENT CSV", f"Find the following data: {str(data_raw)}")
        # self.writeLog('Find the following data: ' + str(data_raw))
        data_list = data_raw.split(self.separator)         # split the file csv by its separator
        # The order of the parameters is specified by the documentation. The file CSV is formatted in a certain way

        # We need to associate the value to the parameter: the order is ID; N; P; K;
        i = 0
        for value in data_list:
            information[self.variables[i]] = value.strip()
            i+=1

        # return super().readData()
        return information
        
    
    # def writeLog(self, msg):
    #     with open('logs/logs.trace', 'a') as log:
    #         log.write(f'[{str(datetime.datetime.now())}]  - [DEVICE AGENT CSV]: {msg} \n')
        
    def readFile(self, file):
        try:
            with open(file, 'r') as input_file:
                input_data = input_file.readlines()[-1]
            return input_data
        except:
            Logs.error("DEVICE AGENT CSV", "Error during reading configuration file" )



# if __name__ == '__main__':
#     variables = ['ID', 'Nitrogen', 'Phosphorus', 'Potassium', 'Timestamp']   # Following the documentation of the "sensor" we made.
#     file_path = 'sensors\\npk_sensors'
#     file_name = 'sensor_1'

#     npk = DeviceAgentCSV(variables, file_name, file_path)   # Takes in input the variables to assign and the file to read

#     print(npk.readData())