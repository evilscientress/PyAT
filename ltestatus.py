#!/usr/bin/python

from PyAT import PyAT 

modem = PyAT('/dev/sierra_internal_AT')

rssi = modem.get_signal_quality()
rssi_range = PyAT.SIGNAL_RANGE[PyAT.dbm_to_range(rssi)]
regstatus = modem.get_registration_status()
operator = modem.get_operator()
network_tech = modem.get_network_technology()
print("%(operator_name)s  %(rssi)ddBm %(network_tech)s" % {
    'operator_name': operator['operator'],
    'rssi': rssi,
    'network_tech': network_tech,
    })

modem.close()