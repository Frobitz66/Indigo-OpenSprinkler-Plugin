#!/usr/bin/env python3

import http.client
import json
import hashlib
import logging
import numbers
from string import Template
from datetime import datetime, timezone

logging.basicConfig(filename="OpenSprinkler.log", level=logging.DEBUG)

#
# The OpenSprinklerController class describes an OpenSprinkler "Controller" which
# derives its functions from the OpenSprinkler API.  Specifically, the
# following API functions:
# 1 Get Controller Variables            "/jc?pw=xxx"
# 2 Change Controller Variables         "/cv?pw=xxx&rsn=x&rbt=x&en=x&rd=x&re=x&update=x"
# 3 Get Options                         "/jo?pw=xxx"
# 4 Change Options                      "/co?pw=xxx&o?=x&loc=x&wtkey=x&two=x&ifkey=x&ttt=x
# 5 Set Password                        "/sp?pw=xxx&npw=xxx&cpw=xxx"
# 6 Get Station Names and Attributes    "/jn?pw=xxx"
# 7 Get Special Station Data            "/je?pw=xxx"
# 8 Change Station Names and Attributes "/cs?pw=xxx&s?=xxx&m?=xxx&i?=xxx&n?=xxx&d?=xxx&q?=xxx&p?=xxx&sid=xxx&st=xxx&sd=xxx"
# 9 Get Station Status                  "/js?pw=xxx"
# 10 Manual Station Run                  "/cm?pw=xxx&sid=xxx&en=xxx&t=xxx"
# 11 Manually Start Program              "/mp?pw=xxx&pid=xxx&uwt=x
# 12 Get Program Data                    "/jp?pw=xxx"
# 13 Change Program Data                 "/cp?pw=xxx&pid=xxx&v=[flag,days0,days1,[start0,start1,start2,start3],[dur0,dur1,dur2,...]]&name=xxx"
# 14 Delete Programs                     "/dp?pw=xxx&pid=xxx"
# 15 Move Up (re-order) Program          "/up?pw=xxx&pid=xxx"
# 16 Start Run-Once Program              "/cr?pw=xxx&t=[x,x,x,...,x,x]"
# 17 Get Log Data                        "/jl?pw=xxx&[start=xxx&end=xxx&type=xxx]||[hist=n&type=xxx]"
# 18 Delete Log Data                     "/dl?pw=xxx&day=n"
# 19 Change Javascript URL               "/cu?pw=xxx&jsp=xxx"
# 20 Get All                             "/ja?pw=xxx"
#
class OpenSprinklerController(object):
    """This class represents the Controller of an OpenSprinkler device.
    
    """
    controller_properties = []
    controller_stations = []
    controller_programs = []
    controller_enabled = False
    
    def __init__(self, myDict):
        self.controller_properties = [
            {'name':'device_time',                  'source':'settings', 'abbrev':'devt',      'val':0},
            {'name':'num_boards',                   'source':'settings', 'abbrev':'nbrd',      'val':0},
            {'name':'enabled',                      'source':'settings', 'abbrev':'en',        'val':0},
            {'name':'rain_delay',                   'source':'settings', 'abbrev':'rd',        'val':0},
            {'name':'rain_sensor_status',           'source':'settings', 'abbrev':'rs',        'val':0},
            {'name':'rain_delay_stop_time',         'source':'settings', 'abbrev':'rdst',      'val':0},
            {'name':'location',                     'source':'settings', 'abbrev':'loc',       'val':''},
            {'name':'wunderground_api_key',         'source':'settings', 'abbrev':'wtkey',     'val':''},
            {'name':'sunrise',                      'source':'settings', 'abbrev':'sunrise',   'val':0},
            {'name':'sunset',                       'source':'settings', 'abbrev':'sunset',    'val':0},
            {'name':'external_ip_address',          'source':'settings', 'abbrev':'eip',       'val':0},
            {'name':'last_weather_call',            'source':'settings', 'abbrev':'lwc',       'val':0},
            {'name':'last_successful_weather_call', 'source':'settings', 'abbrev':'lswc',      'val':0},
            {'name':'last_run_record',              'source':'settings', 'abbrev':'lrun',      'val':0},
            {'name':'weather_options',              'source':'settings', 'abbrev':'wto',       'val':{}},
            {'name':'firmware_version',             'source':'options',  'abbrev':'fwv',       'val':0},
            {'name':'firmware_minor_version',       'source':'options',  'abbrev':'fwm',       'val':0},
            {'name':'time_zone',                    'source':'options',  'abbrev':'tz',        'val':0},
            {'name':'ntp_synch_flag',               'source':'options',  'abbrev':'ntp',       'val':0},
            {'name':'use_dhcp_flag',                'source':'options',  'abbrev':'dhcp',      'val':0},
            {'name':'ip1',                          'source':'options',  'abbrev':'ip1',       'val':0},
            {'name':'ip2',                          'source':'options',  'abbrev':'ip2',       'val':0},
            {'name':'ip3',                          'source':'options',  'abbrev':'ip3',       'val':0},
            {'name':'ip4',                          'source':'options',  'abbrev':'ip4',       'val':0},
            {'name':'gw1',                          'source':'options',  'abbrev':'gw1',       'val':0},
            {'name':'gw2',                          'source':'options',  'abbrev':'gw2',       'val':0},
            {'name':'gw3',                          'source':'options',  'abbrev':'gw3',       'val':0},
            {'name':'gw4',                          'source':'options',  'abbrev':'gw4',       'val':0},
            {'name':'ntp1',                         'source':'options',  'abbrev':'ntp1',      'val':0},
            {'name':'ntp2',                         'source':'options',  'abbrev':'ntp2',      'val':0},
            {'name':'ntp3',                         'source':'options',  'abbrev':'ntp3',      'val':0},
            {'name':'ntp4',                         'source':'options',  'abbrev':'ntp4',      'val':0},
            {'name':'hp0',                          'source':'options',  'abbrev':'hp0',       'val':0},
            {'name':'hp1',                          'source':'options',  'abbrev':'hp1',       'val':0},
            {'name':'hardware_version',             'source':'options',  'abbrev':'hwv',       'val':0},
            {'name':'hardware_type',                'source':'options',  'abbrev':'hwt',       'val':0},
            {'name':'num_expansion_boards',         'source':'options',  'abbrev':'ext',       'val':0},
            {'name':'station_delay_time',           'source':'options',  'abbrev':'sdt',       'val':0},
            {'name':'master_station_1',             'source':'options',  'abbrev':'mas',       'val':0},
            {'name':'master_station_2',             'source':'options',  'abbrev':'mas2',      'val':0},
            {'name':'master_station_1_on_delay',    'source':'options',  'abbrev':'mton',      'val':0},
            {'name':'master_station_2_on_delay',    'source':'options',  'abbrev':'mton2',     'val':0},
            {'name':'master_station_1_off_delay',   'source':'options',  'abbrev':'mtof',      'val':0},
            {'name':'master_station_2_off_delay',   'source':'options',  'abbrev':'mtof2',     'val':0},
            {'name':'use_rain_sensor',              'source':'options',  'abbrev':'urs',       'val':0},
            {'name':'rain_sensor_type',             'source':'options',  'abbrev':'rso',       'val':0},
            {'name':'water_level',                  'source':'options',  'abbrev':'wl',        'val':0},
            {'name':'operation_enabled',            'source':'options',  'abbrev':'den',       'val':0},
            {'name':'ignore_password',              'source':'options',  'abbrev':'ipas',      'val':0},
            {'name':'device_id',                    'source':'options',  'abbrev':'devid',     'val':0},
            {'name':'lcd_contrast',                 'source':'options',  'abbrev':'con',       'val':0},
            {'name':'lcd_backlight',                'source':'options',  'abbrev':'lit',       'val':0},
            {'name':'lcd_dimming',                  'source':'options',  'abbrev':'dim',       'val':0},
            {'name':'boost_time',                   'source':'options',  'abbrev':'bst',       'val':0},
            {'name':'weather_adjustment_method',    'source':'options',  'abbrev':'uwt',       'val':0},
            {'name':'enable_logging',               'source':'options',  'abbrev':'lg',        'val':0},
            {'name':'fpr0',                         'source':'options',  'abbrev':'fpr0',      'val':0},
            {'name':'fpr1',                         'source':'options',  'abbrev':'fpr1',      'val':0},
            {'name':'remote_extension_mode',        'source':'options',  'abbrev':'re',        'val':0},
            {'name':'detected_extension_boards',    'source':'options',  'abbrev':'dexp',      'val':0},
            {'name':'max_extension_boards',         'source':'options',  'abbrev':'mexp',      'val':0},
            {'name':'station_names',                'source':'stations', 'abbrev':'snames',    'val':[]},
            {'name':'station_status',               'source':'status',   'abbrev':'sn',        'val':[]},
            {'name':'num_stations',                 'source':'status',   'abbrev':'nstations', 'val':0},
            {'name':'num_programs',                 'source':'programs', 'abbrev':'nprogs',    'val':0},
            {'name':'max_programs',                 'source':'programs', 'abbrev':'mnp',       'val':0},
            {'name':'max_start_times',              'source':'programs', 'abbrev':'mnst',      'val':0},
            {'name':'program_name_size',            'source':'programs', 'abbrev':'pnsize',    'val':0},
            {'name':'ntp_ipv4_address',             'source':'derived',  'formula':'', 'val':''},
            {'name':'dhcp_ipv4_address',            'source':'derived',  'formula':'', 'val':''},
            {'name':'gw_ipv4_address',              'source':'derived',  'formula':'', 'val':''},
            {'name':'port_number',                  'source':'derived',  'formula':'hp1 << 8 + hp0', 'val':0},
            {'name':'flow_pulse_rate',              'source':'derived',  'formula':'fpr1 << 8 + fpr0', 'val':''}]
        # iterate through the map. pull the value for each key. use the value to set the variable name that
        # is equal to the key and set values
        for prop in self.controller_properties:
            if prop['source'] is not 'derived':
                sourceName = prop['source']
                abbrevName = prop['abbrev']
                if sourceName in myDict:
                    if abbrevName in myDict[sourceName]:
                              prop['val'] = myDict[sourceName][abbrevName]
        try:
            # explicitly set controller_enabled
            self.controller_enabled = True if myDict['settings']['en'] else False
            # parse station information
            ir_byte  = myDict['stations']['ignore_rain'][0]
            seq_byte = myDict['stations']['stn_seq'][0]
            dis_byte = myDict['stations']['stn_dis'][0]
            spe_byte = myDict['stations']['stn_spe'][0]
            num_stations = myDict['status']['nstations']
            idx = 0
            while idx < num_stations:
                station_name  = myDict['stations']['snames'][idx]
                status        = myDict['status']['sn'][idx]
                ignore_rain   = ir_byte & 2**idx
                is_disabled   = dis_byte & 2**idx
                is_sequential = seq_byte & 2**idx
                is_special    = spe_byte & 2**idx
                this_station  = OpenSprinklerStation(station_name, status, idx, ignore_rain, is_sequential, is_disabled, is_special)
                self.controller_stations.append(this_station)
                idx += 1
            # parse program information
            num_programs = self.getProperty('num_programs')
            idx = 0
            while idx < num_programs:
                program_data = myDict['programs']['pd'][idx]
                flags = program_data[0]
                days0 = program_data[1]
                days1 = program_data[2]
                startTimes = program_data[3]
                durations = program_data[4]
                program_name = program_data[5]
                this_program = OpenSprinklerProgram(program_name, flags, days0, days1, startTimes, durations)
                self.controller_programs.append(this_program)
                idx += 1
        except:
            None
        # Hold off on derived props for now   - port_num = 'hp1' << 8 + 'hp0'  - flow_pulse_rate = 'fpr1' << 8 + 'fpr0'

    def print(self):
        """This function prints key characteristics of the Controller.
        
        """
        print('  This controller is: %s' % ('ENABLED' if self.isEnabled() else 'DISABLED'))
        print('    Firmware Version: %s' % self.getProperty('firmware_version'))
        print('   # Physical boards: %s' % self.getProperty('num_boards'))
        print('          # Stations: %s' % self.getProperty('num_stations'))
        print('     Device Location: %s' % self.getProperty('location'))
        print('  # Expansion Boards: %s' % self.getProperty('num_expansion_boards'))
        print('   Device Local Time: %s' % self.getProperty('device_time'))
        print('             Sunrise: %s' % self.getProperty('sunrise'))
        print('              Sunset: %s' % self.getProperty('sunset'))
        print('Wunderground API Key: %s' % self.getProperty('wunderground_api_key') if self.getProperty('wunderground_api_key') else 'No Weather Underground API Key')
        print(' Last Weather Update: %s' % self.getProperty('last_successful_weather_call'))
        print('     Weather Options: %s' % self.getProperty('weather_options'))
        print('  Rain Sensor Status: %s' % self.getProperty('rain_sensor_status'))
        print()


    def list(self):
        """This function pretty-prints ALL Controller Properties.
        
        """
        print('Controller Properties')
        print('%30s : ' % 'NAME','VALUE')
        for prop_item in self.controller_properties:
            print('%30s : ' % prop_item['name'], prop_item['val'])

    #
    # GETTERS
    #
    def getProperty(self, var_name):
        """This function returns the VALUE of a given Proprety.
        
        """
        for prop_item in self.controller_properties:
            if prop_item['name'] == var_name:
                return prop_item['val']
            else:
                raise UnknownPropertyError(var_name)

    def getProperties(self):
        """This function returns the VALUES of all Properties in a JSON array.
        
        """
        result = []
        for prop_item in self.controller_properties:
            result.append({'name':prop_item['name'], 'val':prop_item['val']})
        return result
        
    def getWxStatus(self):
        """This function returns the status of the last call to WeatherUnderground.
        
        If the last call to WeatherUnderground was successful, then return True.
        Otherwise, return False.
        """
        if self.getProperty('wunderground_api_key'):
            if self.getProperty('last_weather_call') != self.getProperty('last_successful_weather_call'):
                return False
            else:
                return True
        else:
            debug.error('No valid Wunderground API key found. Unable to process request.')

    def isEnabled(self):
        """This function returns the ENABLED status of the Controller.
        
        """
        return self.controller_enabled

    def getNumStations(self):
        """This function returns the number of Stations that the Controller recognizes.
        
        """
        return self.getProperty('num_stations')

    def getNumPrograms(self):
        """This function returns the number of Programs that the Controller recognizes.
        
        """
        return self.getProperty('num_programs')

    def getFirmwareVersion(self):
        """This function returns the firmware Major and Minor version as a string.
        
        """
        try:
            fv = self.getProperty('firmware_version')
            fmv = self.getProperty('firmware_minor_version')
            result = str(fv)[:1] + '.' + str(fv)[1:2] + '.' + str(fv)[2:] + ' rev. ' + str(fmv)
            logging.debug('Firmware Version = %s', fv)
            logging.debug('Firmware Minor Version = %s', fmv)
            return result
        except InvalidProperty:
            return 'Invalid Property: '
            

    def getHardwareVersion(self):
        """This fuction returns the hardware version as a string.
        
        """
        return self.getProperty('hardware_version')

    def getHardwareType(self):
        """This function returns a string describing whether the device is AC or DC powered.
        
        """
        if self.getProperty('hardware_type') == 172:
            return 'AC Powered'
        else:
            return 'DC Powered'
        
    def getStations(self):
        """This function returns an object containing all of the Controller's Stations.
        
        """
        return self.controller_stations

    def getPrograms(self):
        """This function returns an object containing all of the Controller's Programs.
        
        """
        return self.controller_programs

    #
    # SETTERS
    #
    def setProperty(self, var_name, var_value):
        """This function sets the value of a Property to a given string.
        
        """
        for prop_item in self.controller_properties:
            if prop_item['name'] == var_name:
                try:
                    prop_item['val'] = var_value
                except:
                    logging.info('Failed to set %s to %s', var_name, str(var_value))
                    return 'ERROR'

    def setName(self, p1):
        """This function sets the Controller name to the given string.
        
        """
        try:
            self.controller_name = p1
        except:
            debug.error('Failed to set controller_name')

    def setxxx(self, p1):
        try:
            self.controller_xxx = p1
        except:
            debug.error('Failed to set controller_xxx')



#
# The OpenSprinklerStation class describes an OpenSprinkler "Station" which 
# derives its functions from the OpenSprinkler API. Specifically, the
# following API functions:
#  Get Station Names  "/jn?pw=xxx"
#  Get Station Status "/js?pw=xxx"
#
# The OpenSprinklerStation class represents a single "Station" and contains
# only the information relevant to a single "Station".
#
class OpenSprinklerStation(object):
    station_name = ''
    status = 0
    station_id = 0
    ignore_rain_flag = 0
    is_sequential_flag = 0
    is_disabled_flag = 0
    is_special_flag = 0

    def __init__(self, sname, sstatus, sid, sirf, sseqf, sdisf, sspef):
        try:
            self.station_name = sname
            self.status = sstatus
            self.station_id = sid
            self.ignore_rain_flag = sirf
            self.is_sequential_flag = sseqf
            self.is_disabled_flag = sdisf
            self.is_special_flag = sspef
        except:
            None

    def refresh(self):
        """This function queries the device for the status of the current Station.

        We fetch the device attributes (ip & port) along with the device password
        from the OpenSprinkler object that acts as an ancestor to this Station object.
        """
        stationDict = OpenSprinkler.read('js')
        for element in stationDict:
            print(element)

    def turnOn(self, duration):
        """This function tells the current Station to turn on for a given integer duration.
        
        """
        # send the command immediately and update the status
        # /cm?pw=xxx&sid=xxx&en=xxx&t=xxx
        try:
            cmd = 'sid='+str(self.station_id)+'&en=1&t='+str(duration)
            #^send(cmd)
            #update_status()
        except:
            None

    def turnOff(self):
        """This function tells the current Station to turn off immediately.
        
        """
        None

    def print(self):
        """This function prints the status of the current station.
        
        """
        print('  Station: %i' % self.station_id)
        print('     Name: %s' % self.station_name)
        print('   Status: %s' % self.status)
        print(' Ignore Rain: %s' % self.ignore_rain_flag)
        print(' Sequential: %s' % self.is_sequential_flag)
        print(' Disabled: %s' % self.is_disabled_flag)
        print(' Special: %s' % self.is_special_flag)
        print()

    #
    # GETTERS
    #
    def getName(self):
        """This function returns the name of the current Station as a string.
        
        """
        return self.station_name

    def getStatus(self):
        """This function returns the status of the current Station as an integer.
        
        """
        return self.status
    
    def getIgnoreRainFlag(self):
        """This function returns the ignore_rain_flag of the current Station as an integer.
        
        """
        return self.ignore_rain_flag

    def getSequentialFlag(self):
        """This function returns the is_sequential_flag of the current Station as an integer.
        
        """
        return self.is_sequential_flag

    def getDisabledFlag(self):
        """This function returns the is_disabled_flag of the current Station as an integer.
        
        """
        return self.is_disabled_flag

    def getSpecialFlag(self):
        """This function returns the is_special_flag of the current Station as an integer.
        
        """
        return self.is_special_flag

    #
    # SETTERS
    #
    def setName(self, station_name):
        """This function sets the name of the current Station to a given string.
        
        """
        none

       
#
# The OpenSprinklerProgram class describes and OpenSprinkler "Program" which
# derives its functions from the OpenSprinkler API. Specifically, the
# the following API functions:
#  Get Program Data  "/jp?pw=xxx"
#
class OpenSprinklerProgram(object):
    week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    program_name = ''
    program_enabled = False
    program_use_weather_adjustment = False
    program_restriction = ''
    program_schedule_type = ''
    program_start_time_type = ''
    program_schedule = []
    program_fixed_start_times = []
    program_repeating_start_times = []
    program_schedule = []
    program_zone_durations = []

    def __init__(self, pname, flags, days0, days1, sTimes, durs):
        logging.debug("class:OpenSprinklerProgram method:__init__ vars:(pname:%s flags:%s days0:%s days1:%s sTimes:%s durs:%s)",
                      pname, flags, days0, days1, sTimes, durs)
        try:
            self.setName(pname)
            self.setEnabled(True if flags & 1 else False)
            self.setWxAdjustment(True if flags & 2  else False)
            self.setRestrictions('Odd' if flags & 4 else 'Even' if flags & 8 else 'None')
            self.setScheduleType('Weekday' if not ((flags & 16) or (flags & 32)) else 'Interval')
            self.setStartTimeType('Fixed' if flags & 64 else 'Repeating')
            self.setSchedule(self.getScheduleType(), days0, days1)
            self.setStartTimes(self.getStartTimeType(), sTimes)
            self.setDurations(durs)
            logging.debug('Finished initializing OpenSprinklerProgram object')
        except:
            logging.error('Error: Could not initialize OpenSprinklerProgram object')

    #
    # GETTERS
    #
    def getName(self):
        return self.program_name

    def getEnabled(self):
        return self.program_enabled

    def getWxAdjustment(self):
        return self.program_use_weather_adjustment

    def getStartTimeType(self):
        return self.program_start_time_type

    def getStartTimes(self):
        if len(self.program_fixed_start_times) > 0:
            return self.program_fixed_start_times
        else:
            return self.program_repeating_start_times

    def getScheduleType(self):
        return self.program_schedule_type

    def getSchedule(self):
        return self.program_schedule

    def getDurations(self):
        return self.program_zone_durations

    # Special Getter to return the entire program structure
    def getProgram(self):
        None

    # Special Getter to print the entire program structure
    def print(self):
        print('\tProgram Name: %s' % self.getName())
        print('\t     Enabled: %s' % self.getEnabled())
        x = self.getStartTimes()
        print('\t    Start at: %s minutes %s %s' % (x[0]['offset'], 'before' if x[0]['sign']=='minus' else 'after', x[0]['basis']))
        if self.getScheduleType() == 'Weekday':
            print('\t      Run on:', end='')
            for day in self.getSchedule():
                print(' %s' % list(day.keys())[0] if day[list(day.keys())[0]]==True else '', end='')
            print(' ')
        else:
            print('\t         Run: every %s days starting in %s days'
                  % (self.getSchedule()[0]['interval'], self.getSchedule()[0]['delay']))
        print('\t       Zones:', end='')
        is_first = True
        for idx,zone in enumerate(self.getDurations()):
            if is_first:
                if zone > 0:
                    print(' Run Zone %s for %s seconds' % (idx, zone))
                    is_first = False
            else:
                if zone > 0:
                    print('\t\t      Run Zone %s for %s seconds' % (idx,zone))
        print(' ')
        
    #
    # SETTERS
    #
    def setName(self,progname):
        try:
            self.program_name = progname
            logging.debug('Set program_name=%s', progname)
        except:
            logging.error('Error: Could not set program name')

    def setEnabled(self,is_enabled):
        try:
            self.program_enabled = is_enabled
            logging.debug('Set program_enabled=%s', is_enabled)
        except:
            logging.error('Error: Could not set program state')

    def setWxAdjustment(self,wxadj):
        try:
            self.program_use_weather_adjustment = wxadj
            logging.debug('Set program_use_weather_adjustment=%s', wxadj)
        except:
            logging.error('Error: Could not set program weather adjustment')
            
    def setRestrictions(self, restriction):
        try:
            self.program_restriction = restriction
            logging.debug('Set program_restriction=%s', restriction)
        except:
            logging.error('Error: Could not set program restriction')
            
    def setScheduleType(self, stype):
        try:
            self.program_schedule_type = stype
            logging.debug('Set program_schedule_type=%s', stype)
        except:
            logging.error('Error: Could not set program schedule type')

    def setStartTimeType(self,timetype):
        try:
            self.program_start_time_type = timetype
            logging.debug('Set program_start_time_type=%s', timetype)
        except:
            logging.error('Error: Could not set program start time type')

    def setSchedule(self, pstype, d0, d1):
        if pstype == 'Weekday':
            self.setWeekdaySchedule(d0)
        else:
            self.setIntervalSchedule(d1, d0)

    def setWeekdaySchedule(self, d0):
        schedule = []
        for day in (day for day in enumerate(self.week)):
            # Fetch the position of the day in the week
            day_index = day[0]
            day_name = day[1]
            is_scheduled = True if (d0 & (2**day_index)) else False
            try:
                schedule.append({day_name:is_scheduled})
                logging.debug('Added element to schedule')
            except:
                logging.error('Error: Could not add element to schedule')
        try:
            self.program_schedule = schedule
            logging.debug('Set program_schedule=%s', str(schedule))
        except:
            logging.error('Error: Could not set program_schedule')

    def setIntervalSchedule(self, d0, d1):
        # Interval Day schedules
        schedule = []
        schedule.append({'interval': d1, 'delay': d0})
        try:
            self.program_schedule = schedule
            logging.debug('Set program_schedule=%s', str(schedule))
        except:
            logging.error('Error: Could not set program_schedule')
            
    def setStartTimes(self, psttype, sTimes):
        if psttype == 'Fixed':
            self.setFixedStartTimes(sTimes)
        else:
            self.setRepeatingStartTimes(sTimes)

    def setFixedStartTimes(self, startTimes):
        self.program_fixed_start_times = []
        self.program_repeating_start_times = []
        for sTime in sTimes:
            if sTime > 0:
                try:
                    self.program_fixed_start_times.append(sTime)
                    logging.debug('Added start_time %s to program_fixed_start_times', str(sTime))
                except:
                    logging.error('Error: Could not set fixed start time')
        
    def setRepeatingStartTimes(self, sTimes):
        self.program_fixed_start_times = []    # disable fixed start times
        self.program_repeating_start_times = [] # flush repeating start times
        for sTime in sTimes:
            if sTime > 0:
                # Flowers 12318 <> Sunset -30min
                if sTime & 0x2000: # bit 14 set => sunrise
                    start_basis = 'Sunset'
                elif sTime & 0x1000: # bit 13 set => sunset
                    start_basis = 'Sunrise'
                else: # neither bit set => midnight
                    start_basis = 'Midnight'
                sign = 'plus' if sTime & 0x800 else 'minus'
                offset = sTime & 0x7ff
                start_time={'basis':start_basis, 'sign':sign, 'offset':offset}
                try:
                    self.program_repeating_start_times.append(start_time)
                    logging.debug('Added start_time %s to program_repeating_start_times', str(start_time))
                except:
                    logging.error('Error: Could not set repeating start time')

    def setDurations(self, durations):
        try:
            self.program_zone_durations = durations
            logging.debug('Set program_zone_durations=%s', durations)
        except:
            logging.error('Error: Could not set program durations')
            

class OpenSprinkler(object):
    """Class representing an OpenSprinkler device.
    
    """
    controller = OpenSprinklerController                         # Defines the primary controller
    pwdDigest = ''
    tgtHost = '127.0.0.1'
    tgtPort = 8080
    
    # Initialize the instantiated OpenSprinkler object
    def __init__(self, hostName, hostPort, userPass):
        logging.debug('Log Started: %s' % datetime.utcnow().strftime('%c'))
        try:
            self.tgtHost = hostName                                  # Store the device hostname
            self.tgtPort = hostPort                                  # Store the device port
            pwdHash = hashlib.md5()
            pwdHash.update(userPass.encode('utf-8'))                 # Encrypt the device password
            self.pwdDigest = pwdHash.hexdigest()                     # Encode and store the encrypted password for use in the URI
            logging.debug('Initialization of OpenSprinkler object complete:')
            logging.debug('\tHost Name = %s' % self.tgtHost)
            logging.debug('\tHost Port = %s' % self.tgtPort)
            logging.debug('\tPassword encrypted and saved.')
        except:
            logging.debug('Initialization of OpenSprinkler object failed:')
            logging.debug('\tReason = %s' % 'fred')
            print('Initialization of the OpenSprinkler object failed.')
            print('...exiting...')
            exit()

    def executeCommand(self, cmd, *args):
        """Function to read from the OpenSprinkler device using the OS API."""
        logging.debug('OpenSprinkler.executeCommand')
        logging.debug('\tcmd = %s' % cmd)
        try:
            commandArguments = ''
            retVal = ''
            for arg in args:
                commandArguments = '&'+str(arg)
            if commandArguments is not '':
                logging.debug('\tcommandArguments = %s' % commandArguments)
            # parse the cmd and inject the hashed password in digest form
            URITemplate = Template('/${APIVerb}?pw=${DigestPassword}${APIArguments}')
            URIString = URITemplate.substitute(APIVerb=cmd,
                                               DigestPassword=self.pwdDigest,
                                               APIArguments=commandArguments)
            logging.debug('\tURIString = %s' % URIString)
            OSConnection = http.client.HTTPConnection(self.tgtHost, self.tgtPort)
            OSConnection.request('GET', URIString)
            OSConnectionResponse = OSConnection.getresponse()
            rawResult = OSConnectionResponse.read().decode('utf-8')
            retVal = json.loads(rawResult)
            headers = OSConnectionResponse.getheaders()
            code = OSConnectionResponse.status
            reason = OSConnectionResponse.reason
            OSResult = OSConnectionResponse.read().decode('utf-8')
            logging.debug('\tConnection Response Headers: %s' % str(headers))
            logging.debug('\tRaw Result: %s' % str(rawResult))
            logging.debug('\tConnection Response Code: %s' % str(code))
            logging.debug('\tConnection Response Reason: %s' % str(reason))
            logging.debug('\tOS Result Code: %s' % str(OSResult))
            OSConnection.close()
            logging.debug('\tResulting JSON Value: %s' % str(retVal))
            if code != '200':
                print('HTTP Error encountered')
                print('Unauthorized')
                raise OS_UnauthorizedException()
            elif result['retVal'] == 3:
                raise OpenSprinklerMismatchException()
            elif result['retVal'] == 16:
                raise OpenSprinklerDataMissingException()
            elif result['retVal'] == 17:
                raise OpenSprinklerValueOutOfRangeException()
            elif result['retVal'] == 18:
                raise OpenSprinklerDataFormatException()
            elif result['retVal'] == 19:
                raise OpenSprinklerRFCodeException()
            elif result['retVal'] == 32:
                raise OpenSprinklerPageNotFoundException()
            elif result['retVal'] == 48:
                raise OpenSprinklerNotPermittedException()
            else:
                return retVal
        except OS_Exception as err:
            logging.error('Error reading from OpenSprinkler')
            logging.error(err)


    def getController(self):
        """Return an OpenSprinklerController object for the Controller of this device.
        
        """
        try:
            JSONDictionary = self.executeCommand('ja')
            self.controller = OpenSprinklerController(JSONDictionary)
            return self.controller
        except:
            logging.error('Error returning Controller object')

    def getStations(self):
        """Return an array of OpenSprinklerStation objects for the Controller of this device.
        
        """
        stations = []
        if self.controller:
            stations = self.controller.getStations()
        else:
            stations = []
        return stations

    def getPrograms(self):
        """Return an array of OpenSprinklerProgram objects for the Controller of this device.
        
        """
        programs = []
        if self.controller:
            programs = self.controller.getPrograms()
        else:
            programs = []
        return programs

    def startProgram(self, programReference, *wxFlag):
        """Function to start a specific program.
        
        The program can be referenced by number or name.
        The use weather station data flag can be True or False (defaults to True) and is optional.
        """
        referenceValid = False
        if isinstance(programReference, numbers.Number):
            if programReference <= self.controller.getNumPrograms():
                referenceValid = True
                pid=programReference
        elif isinstance(programReference, string.String):
            programName = programReference
            # Verify reference exists
        if not wxFlag:
            uwt = 0
        else:
            uwt = 1
        if referenceValid:
            # Tell the device to start a valid Program
            self.write('mp', 'pid=%s' % pid, 'uwt=%s' % uwt)

    def startStation(self, stationReference, t_minutes):
        """Function to start a specific Station for a specific duration.
        
        """
        referenceValid = False
        if isinstance(stationReference, numbers.Number):
            if not self.controller.getStations()[stationReference].getDisabledFlag():
                sid=stationReference
                en=1
                t=t_minutes*60
            else:
                logging.debug('The selected Station is disabled.')
        if referenceValid:
            # Tell the device to start a valid Station
            self.write('cm', 'sid=%s' % sid, 'en=%s' % en, 't=%s' % t)




class OS_Exception(Exception):
    """Base class for exceptions in this module."""
    pass

class OS_UnknownPropertyError(OS_Exception):
    """Exception raised for invalid property references.
    
    Attributes:
       propertyReferenced -- name of property referenced
       message -- explanation of the error
    """
    def __init__(self, propertyReferenced, *message):
        self.propertyReferenced = propertyReferenced
        self.message = message

    def __str__(self):
        return str('UnknownPropertyError - %s can not be found.' % self.propertyReferenced)

class OS_UnauthorizedException(OS_Exception):
    """Exception raised for missing or incorrect password."""
    def __init__(self):
        self.message = 'Unauthorized User Error - The password is either missing or incorrect.'
        
    def __str__(self):
        return self.message

class OS_MismatchException(OS_Exception):
    """Exception raised when new password and confirmation password do not match."""
    def __init__(self):
        self.message = 'Password Mismatch Error - The new password and confirmation password do not match.'

    def __str__(self):
        return self.message

class OS_DataMissingException(OS_Exception):
    """Exception raised when required parameters are missing."""
    def __init__(self):
        self.message = 'Missing Required Parameters Error - Incorrect or missing parameters for the given command.'

    def __str__(self):
        return self.message

class OS_ValueOutOfRangeException(OS_Exception):
    """Exception raised when a required parameter value is out of range."""
    def __init__(self):
        self.message = 'Value out of Range Error - The value for the given parameter is out of range.'

    def __str__(self):
        return self.message

class OS_DataFormatException(OS_Exception):
    """Exception raised when parameter data does not match the required format."""
    def __init__(self):
        self.message = 'Data Format Error - The provided data does not match the required format.'

    def __str__(self):
        return self.message

class OS_RFCodeException(OS_Exception):
    """Exception raised when RF code does not match the required format."""
    def __init__(self):
        self.message = 'RF Code Error - The RF Code specified does not match the required format.'

    def __str__(self):
        return self.message

class OS_PageNotFoundException(OS_Exception):
    """Exception raised when a page is not found or the requested file is missing."""
    def __init__(self):
        self.message = 'Page Not Found - The page was not found or the requested file was missing.'

    def __str__(self):
        return self.message

class OS_NotPermittedException(OS_Exception):
    """Exception raised when an operation can not be performed on the requested station."""
    def __init__(self):
        self.message = 'Operation Not Permitted - The operation can not be performed on the requested station.'

    def __str__(self):
        return self.message

    
if __name__ == "__main__":
    ######################################################################################                
    # The fun begins here
    fred = OpenSprinkler('10.0.1.31', '8080', 'abc123')
    fredController = fred.getController()
    print('CONTROLLER INFORMATION\n')
    fredController.printController()
    fredPrograms = fredController.getPrograms()
    print('PROGRAM INFORMATION\n')
    for program in fredPrograms:
        program.printProgram()

    #fredStations = fredController.getStations()
    #print "The Controller " + fredController.get('operation_enabled')

    #fredController.listProperties()
    #print(fredController.getAllProperties())
    #print(fredController.getProperty('num_boards'))
