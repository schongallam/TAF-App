# tafs.py

tafs.py was developed with Python 3.8.10. It is a script to obtain aviation weather data (TAFs and METARs) from aviationweather.gov.  It accepts a few options and prints the results to stdout.

## usage:
```usage:

$ tafs.py [OPTIONS] ICAO1 [ICAO2 ICAO3 ...]

ICAOx                           A 4-character ICAO station identifier (usually an aerodrome or other recognized
                                weather station)

optional arguments:
  -h, --help                    show this help message and exit
  -T 1-24,  --TAF_hours 1-24    Max number of hours prior to look for TAFs. Default=24
  -M 1-24, --METAR_hours 1-24   Max number of hours prior to look for METARs. Default=24
  -C 1-24, --METAR_count 0-24   If you want METARs for each station, set a max number. Default=0 (no METARs fetched)
  -m, --METAR_only              Get METARs only (no TAFs). If set, at least 1 METAR per station is requested.
  -i, --ignore                  Ignore malformed station IDs (default is abort)
```

## tips

Station IDs consist of exactly 4 alphanumeric characters, always starting with a letter.  Lowercase is recognized, but uppercase is used by convention.
You can list up to 51 station IDs (arbitrary limit to prevent excessively-long URL strings)
The number of METARs per station is set arbitrarily to 24, commensurate with anticipated usage, and in the interest of avoiding excessive screen flooding and, generally managing data volume.

## examples

```
$ ./tafs.py KBOS KJFK  # Get the most recent TAFs each from Boston and JFK
KBOS 232105Z 2321/2424 33008KT P6SM FEW050
  FM240600 35005KT P6SM SKC
  FM241200 34005KT P6SM BKN035
  FM241600 19006KT P6SM SCT250

KJFK 232030Z 2321/2424 33010KT P6SM SKC
  FM240200 36007KT P6SM SKC
  FM240900 VRB05KT P6SM SKC
  FM241700 18006KT P6SM BKN250


$ ./tafs.py -C 3 KSCH KALB  # Get the 3 most recent METARs and TAFs (if available. KSCH has no TAF.)
KSCH 230045Z 00000KT 15SM CLR 01/M05 A3017
KSCH 230250Z 00000KT 15SM CLR M01/M05 A3014 RMK LAST
KSCH 231245Z 00000KT 15SM CLR M03/M05 A3017 RMK FIRST

KALB 230051Z 00000KT 10SM FEW080 FEW250 01/M05 A3017 RMK AO2 SLP220 T00061050
KALB 230151Z COR 17005KT 10SM FEW250 02/M05 A3015 RMK AO2 SLP213 T00221050
KALB 230251Z 15006KT 10SM BKN150 02/M05 A3014 RMK AO2 SLP209 T00221050 56015

KALB 231720Z 2318/2418 28008G15KT P6SM SCT035
  FM240100 00000KT P6SM BKN035
  FM241500 17004KT P6SM SCT035

$ ./tafs.py -m -M 3 -C 6 KCOS KDEN  # For each station, get up to 6 METARs only (no TAFs), but only from within the last 3 hours
KCOS 232154Z 04021G27KT 10SM SCT170 BKN250 11/M18 A2984 RMK AO2 PK WND 04027/2153 SLP105 T01111183
KCOS 232254Z 01011KT 10SM SCT170 BKN250 08/M18 A2988 RMK AO2 PK WND 04027/2156 SLP132 VIRGA NW T00831183
KCOS 232354Z 01015KT 10SM SCT160 BKN250 08/M17 A2992 RMK AO2 SLP151 VIRGA W-NW T00781167 10150 20078 53028

KDEN 232153Z 35008KT 10SM FEW090 SCT150 BKN200 09/M12 A2987 RMK AO2 SLP104 T00891122
KDEN 232253Z 36008KT 10SM FEW090 BKN140 BKN200 08/M09 A2991 RMK AO2 SLP118 VIRGA T00831089
KDEN 232353Z 36011KT 10SM FEW090 BKN140 BKN200 05/M08 A2995 RMK AO2 SLP137 T00501078 10111 20050 53027

```

## releases

1.0 Initial release

1.0.1 minor fixes
-1kb buffer limit per TAF or METAR
-passed argv[0] to main() as compact representation

## dependencies
sys
argparse
string
urllib.request
urllib.error
