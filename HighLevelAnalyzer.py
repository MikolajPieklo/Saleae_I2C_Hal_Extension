from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, ChoicesSetting

class Hla(HighLevelAnalyzer):
    device_address = StringSetting()
    address_type = ChoicesSetting(choices=('binary', 'decimal', 'hex'))
    reg_len = ChoicesSetting(choices=('8 bits', '16 bits'))
    address_offset = ChoicesSetting(choices=('0', '>>1', '<<1'))
    device_address_number = 0
    frame_time_start = 0
    is_frame_start_initialized = False
    byte_counter = 0
    reg = 0
    data = ''
    i2c_operation = ""

    result_types = {
        'read': {
            'format': 'DEV {{data.address}} READ TO REG {{data.reg}} DATA {{data.data}} LEN {{data.len}}'
        },
        'write': {
            'format': 'DEV {{data.address}} WRITE TO REG {{data.reg}} DATA {{data.data}} LEN {{data.len}}'
        },
        'mismatch': {
            'format': 'MISMATCH'
        }
    }

    def __init__(self):
        print("Settings:", self.device_address, self.address_type)

        try:
            if self.address_type == 'binary':
                self.device_address_number = int(self.device_address, 2)
            elif self.address_type == 'hex':
                self.device_address_number = int(self.device_address, 16)
            else:
                self.device_address_number = int(self.device_address)

            if self.address_offset == '>>1':
                self.device_address_number = self.device_address_number >> 1
            if self.address_offset == '<<1':
                self.device_address_number = self.device_address_number << 1
        except:
            self.device_address_number = int(self.device_address)

    def decode(self, frame: AnalyzerFrame):
        if frame.type == 'start':
            if self.is_frame_start_initialized == False:
                self.frame_time_start = frame.start_time
            return

        if frame.type == 'stop':
            if self.is_frame_start_initialized == True:
                self.is_frame_start_initialized = False
                if self.reg_len == '8 bits':
                    reg = "0x{:02X}".format(self.reg)
                elif self.reg_len == '16 bits':
                    reg = "0x{:04X}".format(self.reg)
                else:
                    return

                a = 1 if self.reg_len == '8 bits' else 2
                if self.byte_counter - a < 0:
                    byte = "-1"
                else:
                    byte = str(self.byte_counter - a)
                print('Dev: ' + str(hex(self.device_address_number))+ ' '
                      + self.i2c_operation +  " to reg:" + reg
                      + " value:" + self.data
                       +" len:" + byte)
                self.byte_counter = 0
                self.reg = 0
                data = self.data
                self.data = ''
                return AnalyzerFrame(self.i2c_operation, self.frame_time_start, frame.end_time,
                                     {'address': self.device_address, 'reg': reg, 'data': data, 'len': byte})
            return

        if frame.type == 'address':
            if frame.data['address'][0] == self.device_address_number:
                self.is_frame_start_initialized = True
                if frame.data['read'] == True:
                    self.i2c_operation = "read"
                else:
                    self.i2c_operation = "write"
            return

        if frame.type == 'data':
            if self.is_frame_start_initialized == True:
                if self.reg_len == '8 bits':
                    if self.byte_counter == 0:
                        self.reg = frame.data['data'][0]
                    else:
                        self.data += "0x{:02X}, ".format(frame.data['data'][0])
                elif self.reg_len == '16 bits':
                    if self.byte_counter == 0:
                        self.reg = frame.data['data'][0] << 8
                    elif self.byte_counter == 1:
                        self.reg |= frame.data['data'][0]
                    else:
                        if self.byte_counter < 10:
                            self.data += "0x{:02X}, ".format(frame.data['data'][0])
                        else:
                            self.data = '...'
                else:
                    return
                self.byte_counter += 1
            return
