#!/usr/bin/python

from PyAT import PyAT

modem = PyAT('/dev/sierra_internal_AT')
SYMBOL = ''
rssi = modem.get_signal_quality()
if rssi is None:
    print ('%s no signal' % SYMBOL)
else:
    rssi_range = PyAT.dbm_to_range(rssi)
    rssi_range_name = PyAT.SIGNAL_RANGE[rssi_range]
    regstatus = modem.get_registration_status()
    operator = modem.get_operator()
    network_tech = modem.get_network_technology()
    print("%(symbol)s %(roaming)s'%(operator_name)s' %(rssi)s %(network_tech)s" % {
        'symbol': SYMBOL,
        'roaming': 'R! ' if regstatus['stat'] == PyAT.REGISTRATION_REGISTERED_ROAMING else '',
        'operator_name': operator['operator'],
        'rssi': (str(rssi) + 'dBm'),
        'network_tech': network_tech,
    })

if rssi is None or rssi_range == 0:
    print('#ff0000')
elif rssi_range == 1:
    print('#ff7f00')
elif rssi_range == 2:
    print('#ffff00')
elif rssi_range == 3:
    print('#00ff00')

modem.close()
