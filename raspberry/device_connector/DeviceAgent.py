class deviceAgent(object):
    def __init__(self, ipaddress):
        self.ipaddress = ipaddress
        pass

    def readData(self):
        pass
    
    def writeData(self, payload):
        pass

    def sendData(self):
        """
        Send the data to the resource catalog
        """
        
        pass



class DeviceAgentCSV(deviceAgent):
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

        file = self.input_file_path + '\\' + self.input_file_name + '.' + self.input_file_extension  # Build the final path
        data_raw = str(self.readFile(file))    # read the data from the file, return a string. The cast to string is unecessary
        data_list = data_raw.split(self.separator)         # split the file csv by its separator
        # The order of the parameters is specified by the documentation. The file CSV is formatted in a certain way


        # We need to associate the value to the parameter: the order is ID; N; P; K;
        i = 0
        for value in data_list:
            information[self.variables[i]] = value
            i+=1

        # return super().readData()
        return information
        
    

    def readFile(self, file):
        with open(file, 'r') as input_file:
            input_data = input_file.readlines()[-1]
        return input_data
