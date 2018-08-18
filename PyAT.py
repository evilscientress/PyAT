#!/usr/bin/python

import serial
import re

ENABLE_DEBUGGING=False
def DEBUG(*args, **kwargs):
    if ENABLE_DEBUGGING:
        print(*args, **kwargs)

class PyAT(object):

    class AT_Command_Exception(Exception):
        """docstring for AT_Command_Exception"""
        def __init__(self):
            super(AT_Command_Exception, self).__init__()
            

    def __init__(self, port):
        super(PyAT, self).__init__()
        self.port = port
        self.ser = serial.Serial(self.port, timeout=0.5)
        self.registration_status_mode_set=False

    def close(self):
        self.ser.close()    

    def _sendcommand(self, cmd, regex=None):
        DEBUG('> %s' % cmd)
        self.ser.write((cmd + '\r\n').encode('ascii'))
        cmd_resp = None
        regex_match_result = None
        while True:
            resp = self.ser.readline().decode('ascii').strip()
            regex_match = re.match(regex, resp) if regex is not None else None
            DEBUG('< %s' % resp)
            if regex_match is not None:
                DEBUG("found regex match")
                regex_match_result = regex_match
            elif resp == cmd:
                DEBUG('found comannd echo')
            elif resp.startswith('OK'):
                DEBUG('command executed sucessfully')
                return regex_match_result
            elif resp.startswith('ERROR'):
                DEBUG('ERROR EXCECUTING COMMAND')
                raise AT_Command_Exception('Error sending command "%s": "%s"' % (cmd, resp))
            elif resp == '':
                pass
            else:
                DEBUG('WARNING Unknowen Response: "%s"' % resp)

    @classmethod
    def csq_to_dbm(cls, csq_dbm_value):
        csq_dbm_value = int(csq_dbm_value)
        if csq_dbm_value == 99:
            return None
        elif 0 <= csq_dbm_value and csq_dbm_value <= 31:
            return -113 + 2 * csq_dbm_value
        else:
            return ValueError('invalid csq_dbm_value')

    SIGNAL_RANGE_MARGINAL = 0
    SIGNAL_RANGE_OK = 1
    SIGNAL_RANGE_GOOD = 2
    SIGNAL_RANGE_EXCELLENT = 3
    SIGNAL_RANGE = {
        0:  'Marginal',
        1:  'OK',
        2:  'Good',
        3:  'Excellent',
    }
    @classmethod
    def dbm_to_range(cls, dbm):
        if dbm < -93:
            return cls.SIGNAL_RANGE_MARGINAL
        elif -93 <= dbm and dbm < -83:
            return cls.SIGNAL_RANGE_OK
        elif -83 <= dbm and dbm < -73:
            return cls.SIGNAL_RANGE_GOOD
        elif -73 <= dbm and dbm < -51:
            return cls.SIGNAL_RANGE_EXCELLENT
        else:
            return None


    def get_signal_quality(self):
        resp = self._sendcommand('AT+CSQ', r'\+CSQ: (?P<rssi>\d+),(?P<ber>\d+)')
        if resp is not None:
            return self.csq_to_dbm(resp.group('rssi'))
        else:
            raise self.AT_Command_Exception("ERROR no value returned")

    REGISTRATION_NOT_REGISTERED = 0
    REGISTRATION_REGISTERED_HOME = 1
    REGISTRATION_NOT_REGISTERED_SEARCHING = 2
    REGISTRATION_REGISTRATION_DENIED = 3
    REGISTRATION_UNKNOWN = 4
    REGISTRATION_REGISTERED_ROAMING = 5
    REGISTRATION_REGISTERED_SMS_HOME = 6
    REGISTRATION_REGISTERED_SMS_ROAMING = 7
    REGISTRATION_REGISTERED_EMERGENCY = 8
    ACCESS_TECHNOLOGY_GSM = 0
    ACCESS_TECHNOLOGY_GSM_COMPACT = 1
    ACCESS_TECHNOLOGY_UTRAN = 2
    ACCESS_TECHNOLOGY_GSM_EGPRS = 3
    ACCESS_TECHNOLOGY_UTRAN_HSDPA = 4
    ACCESS_TECHNOLOGY_UTRAN_HSUPA = 5
    ACCESS_TECHNOLOGY_UTRAN_HSDPA_HSUPA = 6
    ACCESS_TECHNOLOGY_E_UTRAN = 7
    ACCESS_TECHNOLOGY = {
        0: "GSM",
        1: "GSM Compact",
        2: "Utran",
        3: "GSM w/EGPRS",
        4: "UTRAN w/HSDPA",
        5: "UTRAN w/HSUPA",
        6: "UTRAN w/HSDPA and HSUPA",
        7: "E-UTRAN"
    }

    def get_registration_status(self):
        if not self.registration_status_mode_set:
            self._sendcommand('AT+CREG=2')
            self.registration_status_mode_set = True
        resp = self._sendcommand('AT+CREG?', r'\+CREG: (?P<type>[0-2]),(?P<stat>[0-8])(?:,"(?P<lac>[0-9a-fA-F]{1,4})","(?P<ci>[0-9a-fA-F]{1,8})"(?:,(?P<act>[0-7]))?)?')
        if resp is not None:
            return {
                'type': int(resp.group('type')),
                'stat': int(resp.group('stat')),
                'lac': resp.group('lac'),
                'lac': resp.group('ci'),
                'act': int(resp.group('act')),
                'act_name': self.ACCESS_TECHNOLOGY[int(resp.group('act'))]
            }
        else:
            raise self.AT_Command_Exception("ERROR no value returned")

    OPERATOR_MODE_AUTOMATIC = 0
    OPERATOR_MODE_MANUAL = 1
    OPERATOR_MODE_DEREGISTER = 2
    OPERATOR_MODE_SET_FORMAT_ONLY = 3
    OPERATOR_MODE_AUTOMATIC_MANUAL = 4 # try manual, if manual fails fall back to automatic
    def get_operator(self):
        resp = self._sendcommand('AT+COPS?', r'\+COPS: (?P<mode>[0-4])(?:,(?P<format>[0-2]),"(?P<oper>.{1,16})"(?:,(?P<act>[0-7]))?)?')
        if resp is not None:
            return {
                'mode': int(resp.group('mode')),
                'format': int(resp.group('format')),
                'operator': resp.group('oper'),
                'act': int(resp.group('act')),
                'act_name': self.ACCESS_TECHNOLOGY[int(resp.group('act'))]
            }
        else:
            raise self.AT_Command_Exception("ERROR no value returned")

    def set_operator(self, mode=0, operator_format=None, operator=None, act=None):
        if 0 > mode and mode > 4:
            raise KeyError('mode must be between 0-4')
        if operator is not None and operator_format is None:
            raise ValueError('error operator_format must be set if operator is set')
        if operator_format is not None and operator is None:
            if mode == 3:
                operator = ""
            else:
                raise ValueError('error operator must be set if operator_format is set and mode is not 3')
        if act is None and (operator_format is None or operator is None):
            raise ValueError('act may only be set if operator and format is set too')

        cmd = 'AT+COPS=%d' % mode
        if mode > 0:
            cmd += ',%d,%s' % (operator_format, operator)
            if act is not None:
                cmd += ',%d' % act
        self._sendcommand(cmd)

    def get_operator_name(self):
        resp = self.get_operator()
        return resp['operator']


    NETWORK_TEHCNOLOGY_INUSE=0
    NETWORK_TEHCNOLOGY_AVAILABLE=1
    NETWORK_TEHCNOLOGY_SUPPORTED=2
    def get_network_technology(self, mode=0):
        resp = self._sendcommand("AT*CNTI=%d" % mode, r'\*CNTI: [0-2],(?P<tech>.*)')
        if resp is not None:
            return resp.group('tech')
        else:
            raise self.AT_Command_Exception("ERROR no value returned")


if __name__ == "__main__":

    modem = PyAT('/dev/sierra_internal_AT')

    rssi = modem.get_signal_quality()
    print("current rssi %d (%s)" % (rssi, PyAT.SIGNAL_RANGE[PyAT.dbm_to_range(rssi)]))
    print("registration status %r" % modem.get_registration_status())
    print("get_operator %r" % modem.get_operator())
    print("get_operator_name %s" % modem.get_operator_name())
    print("get_network_technology %s" % modem.get_network_technology())

    modem.close()