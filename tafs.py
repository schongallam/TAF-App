#!/usr/local/bin/python
#
# Obtains TAFs (+/- METARs) from aviationweather.gov
# (C) 2022 Malcolm Schongalla
# Publicly released under the CARGO CULT SOFTWARE LICENSE VERSION 1.0.1, MAY 2022.

# Retrieves the desired data from aviationweather.gov and organizes it into a conventional presentation.
# Priority was given to minimizing HTTPS requests.  But this gives you a chunk of METARs and a chunk
# of TAFs and they are not spaced, organized, or CRLF'd appropriately for a standard pilot format.
# So a lot of the below code exists just to rectify that.

# Technical note: There is no published limit to the total number of characters in a TAF or METAR, in
# NWSI 10-813.  Individual TAF lines are limited to 69 characters, but there is no explicit limit to the
# number of lines.  Also, various worldwide TAF producers may or may not always adhere to this limit or
# other ICAO standards.  To limit the risk of buffer overflows, a limit of 1kb per station entry (TAF or
# METAR) is enfored in get_raw_text().  That function does not discriminate between TAF or METAR.

import sys, argparse, string
import urllib.request
from urllib.error import URLError, HTTPError

version = "1.0.1"

def is_valid_station(station):
    # Rules: 4 characters long; alphanumeric characters only; must start with a letter
    # does not actually check if the station identifier matches an existing ICAO station, however
    valid_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    if len(station) != 4:
        return False
    if station[0].isalpha() == False:
        return False
    for x in station[1:4]:
        if not x in valid_chars:
            return False
    return True

def get_raw_text(xml, pretty=True, strict=False):
    # The python XML processing libraries state that they are not secure against certain exploits and so were not used, even though they are an obvious option.
    # if pretty, insert newlines before each new TAF line.  pretty is overridden to false for METARs for reason in comments below
    # if strict, throw an exception for malformed XML elements
    if xml.find("<METAR>") > 0:
        pretty=False # rarely, some stations will include "TEMPO" and "BECMG" groups in METARs, which shouldn't result in CRLFs
    TAF_list = []
    while xml.find("<raw_text>") >= 0:
        start = xml.find("<raw_text")+10
        end = xml.find("</raw_text>")
        if strict:
            assert end >= start+10, "Malformed XML element <raw_text>"
        elif end < start+10:
            return TAF_list
        if end-start > 1024: end = start+1024 # see technical note above
        TAF_list.append(xml[start:end])
        xml = xml[end+11:]
    if pretty:
        make_crlf = ((" BECMG", "\r\n  BECMFG"), (" FM", "\r\n  FM"), (" PROB", "\r\n  PROB"), (" TEMPO", "\r\n  TEMPO"))
        new_TAFs = []
        for TAF in TAF_list:
            for s1, s2 in make_crlf:
                new_TAF = TAF.replace(s1, s2)
                TAF = new_TAF
            new_TAFs.append(TAF)
        TAF_list = new_TAFs
    return TAF_list
    
def get_station_from_line(line):
    if line[0:4] == "TAF ": line = line[4:]
    station = line[0:4]
    if is_valid_station(station):
        return station
    else:
        return "_ERR"

def divide_METAR_list(METAR_stations, TAF_stations):
    # This function is needed because we print solo METARs separately. So we need to identify them.
    # The affiliated list is not really used for now, but might be useful in the future.
    solo, affiliated = [], []
    for METAR_station in METAR_stations:
        if TAF_stations.__contains__(METAR_station):
            if not affiliated.__contains__(METAR_station):
                affiliated.append(METAR_station)
        else:
            if not solo.__contains__(METAR_station):
                solo.append(METAR_station)
    return solo, affiliated

def all_METARs_from_station(METARs, station, max=24):
    lines = []
    count = 0
    for METAR in METARs:
        if count >= max: break
        if METAR[0:4] == station:
            lines.append(METAR)
            count += 1
    if lines != []:
        lines.append("")
    return lines

def collect_solo_METARs(METARs, stations, max=24):
    METARs.sort()
    stations.sort()
    lines = []
    for station in stations:
        lines = lines + all_METARs_from_station(METARs, station, max)
    return lines

def get_TAF_from_station(TAFs, station):
    offset = 0 # the reason to use an offset is to preserve the original leading characters in order to
    # be true to the original data as much as possible. Some countries start TAFs with "TAF" instead of the station ICAO.
    for i in range(len(TAFs)):
        if TAFs[i][0:4] == "TAF ":
            offset=4
        if TAFs[i][0+offset:4+offset] == station:
            return TAFs[i]
    return station + " TAF not found" # shouldn't have to resort to this if we did everything else correctly

def add_METARs_to_TAFs(TAFs, TAF_stations, METARs, max_metars=24):
    lines = []
    TAFs.sort()
    TAF_stations.sort()
    METARs.sort()
    for station in TAF_stations:
        lines = lines + all_METARs_from_station(METARs, station, max_metars) + [get_TAF_from_station(TAFs, station), ""]
    return lines

def main(selfname, argv):
    parser = argparse.ArgumentParser(prog=selfname, description="Version {} - Retrieve TAFs and/or METARs from aviationweather.gov".format(version))
    parser.add_argument("stations", metavar="XXXX", nargs="+", help="4-character station ICAO [A..Z,a..z,0..9] (wildcards not supported)")
    parser.add_argument("-T", "--TAF_hours", dest="TAF_hours", type=int, default=24, metavar="1-24", help="Max number of hours prior to look for TAFs. Default=24")
    parser.add_argument("-M", "--METAR_hours", dest="METAR_hours", type=int, default=24, metavar="1-24", help="Max number of hours prior to look for METARs. Default=24")
    parser.add_argument("-C", "--METAR_count", dest="METAR_count", type=int, default=0, metavar="0-24", help="If you want METARs for each station, set a max number. Default=0 (no METARs fetched)")
    parser.add_argument("-m", "--METAR_only", dest="METAR_only", default=False, action="store_true", help="Get METARs only (no TAFs). If set, If set, at least 1 METAR per station is requested.")
    parser.add_argument("-i", "--ignore", dest="ignore_malformed_IDs", default=False, action="store_true", help="Ignore malformed station IDs (default is abort)")
    args = parser.parse_args()

    # reassign names purely for convenience
    stations = args.stations
    TAF_hours = args.TAF_hours
    METAR_hours = args.METAR_hours
    METAR_count = args.METAR_count
    METAR_only = args.METAR_only
    ignore_malformed_IDs = args.ignore_malformed_IDs

    # need to validate and prepare the station identifiers into a standardized string format
    stations = stations[0:51] # keeps the station list under an arbitrary 256-character limit
    stations = [station[:4].upper() for station in stations]  # Not required, but for convention & readability
    _stations = []
    station_rules = "  Must consist of 4 characters, A..Z, a..z, 0..9, and start with a letter."
    for station in stations:
        if is_valid_station(station):
            _stations.append(station)
        elif not ignore_malformed_IDs:
            print("Invalid station ID." + station_rules)
            parser.print_usage()
            parser.exit(2)
    if len(_stations) == 0:
        print("No valid stations provided." + station_rules)
        parser.print_usage()
        parser.exit(2)
    station_string = ','.join(_stations)
    stations = _stations # all valid and ready to go into a URL

    # URL_root used in this basic format for getting both TAFs and METARs
    URL_root = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource={data_source}&requesttype=retrieve&format=xml&hoursBeforeNow={hours_before_now}&mostRecentForEachStation={mRFES}&stationString={station_string}"


    # Make the HTTPS request for TAFs, if indicated
    TAFs, TAF_station_list = [], []
    TAF_count = 0
    if not METAR_only:
        TAF_hours = 1 if TAF_hours < 1 else 24 if TAF_hours > 24 else TAF_hours
        data_source = "tafs"
        hours_before_now = str(TAF_hours)
        most_recent_only = "true"
        URL_TAF = URL_root.format(data_source=data_source, hours_before_now=hours_before_now, mRFES=most_recent_only, station_string=station_string)
        try:
            response = urllib.request.urlopen(URL_TAF)
            TAF_xml = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print("HTTP Error, ", e.code, e.reason)
        except urllib.error.URLError as e:
            print("URL Error, ", e.reason)
        else: #There are lots of other errors to try catching but I'm not going down that rabbit hole right now
            TAFs = get_raw_text(TAF_xml)
            TAF_count = len(TAFs)
            if TAF_count > 0:
                for line in TAFs:
                    station = get_station_from_line(line)
                    if not TAF_station_list.__contains__(station):
                        TAF_station_list.append(station)
    else:
        if METAR_count < 1: # it may be 0 by default, this ensures a sensible data request
            METAR_count = 1

    # Make the HTTPS request for METARs, if indicated
    METARs, METAR_station_list = [], []
    # METAR_count (the max number requested, initially) is used slightly differently than TAF_count (the number received)
    # You can't limit the number of METARs received, so instead we later limit the number we print
    if METAR_count > 0:
        # 24 picked as a commonsense limit, though with multiple station IDs it will still flood the screen.
        METAR_count = 24 if METAR_count > 24 else METAR_count
        METAR_hours = 1 if METAR_hours < 1 else 24 if METAR_hours > 24 else METAR_hours
        data_source = "metars"
        hours_before_now = str(METAR_hours)
        most_recent_only = "false" if METAR_count > 1 else "true" # METAR_count is either 1 or >1, we know
        URL_METAR = URL_root.format(data_source=data_source, hours_before_now=hours_before_now, mRFES=most_recent_only, station_string=station_string)
        try:
            response = urllib.request.urlopen(URL_METAR)
            METAR_xml = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print("HTTP Error, ", e.code, e.reason)
            METAR_count = 0
        except urllib.error.URLError as e:
            print("URL Error, ", e.reason)
            METAR_count = 0
        else:
            METARs = get_raw_text(METAR_xml, pretty=False)
            if len(METARs) > 0:
                for line in METARs:
                    station = get_station_from_line(line)
                    if not METAR_station_list.__contains__(station):
                        METAR_station_list.append(station)
    else:
        METAR_count = 0 # just in case user is being tricky and set it <0

    # Sort and print results
    solo_METAR_stations,_ = divide_METAR_list(METAR_station_list, TAF_station_list)
    for line in collect_solo_METARs(METARs, solo_METAR_stations, max=METAR_count): print(line)
    annotated_TAFs = add_METARs_to_TAFs(TAFs, TAF_station_list, METARs, max_metars=METAR_count)
    for line in annotated_TAFs: print(line)

# TODO:
#  Make the http request error catching more robust

if __name__ == "__main__":
    main(sys.argv[0][sys.argv[0].rfind('/')+1:], sys.argv[1:])