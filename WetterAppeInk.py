"""
eInk-Wetterstation
Copyright 2021, K.N.
https://github.com/hilfriedhartwich/eInk-Wetterstation/

GNU/GPL v3
Stand: 20.05.2021
"""

import time
import requests
from datetime import datetime
import os
import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0373 import Adafruit_IL0373
from adafruit_epd.il91874 import Adafruit_IL91874  # pylint: disable=unused-import
from adafruit_epd.il0398 import Adafruit_IL0398  # pylint: disable=unused-import
from adafruit_epd.ssd1608 import Adafruit_SSD1608  # pylint: disable=unused-import
from adafruit_epd.ssd1675 import Adafruit_SSD1675  # pylint: disable=unused-import
from adafruit_epd.ssd1680 import Adafruit_SSD1680  # pylint: disable=unused-import
from adafruit_epd.ssd1681 import Adafruit_SSD1681  # pylint: disable=unused-import


# Rahmendaten
api_key = "heirmusseinapikeystehen" # Hier den OpenWeatherMap API-Key eintragen
city_name = "Berlin" # Hier den Namen der gewünschten Stadt eintragen


# Zeitumrechner
def UNIX2TTMMJJHHMM(rohzeit):
    zeitangabe = time.strftime("%d.%m.%Y, %H:%M", time.localtime(rohzeit)) + ' Uhr'
    return zeitangabe

def UNIX2HHMM(rohzeit):
    zeitangabe = time.strftime("%H:%M", time.localtime(rohzeit))
    return zeitangabe

# Umlaute entfernen
def wegmitdenumlauten(inputstring):

    inputstring = inputstring.lower()
    
    outputstring = ''
    
    for buchstabe in inputstring:
        if buchstabe == 'ä':
            outputstring += 'ae'
        elif buchstabe == 'ö':
            outputstring += 'oe'
        elif buchstabe == 'ü':
            outputstring += 'ue'
        elif buchstabe == 'ß':
            outputstring += 'ss'                
        else:
            outputstring += buchstabe

    return outputstring

# Zeit in Worten
utabelle = {
    1: 'eins', 13: 'eins',
    2: 'zwei', 14: 'zwei',
    3: 'drei', 15: 'drei',
    4: 'vier', 16: 'vier',
    5: 'fuenf', 17: 'fuenf',
    6: 'sechs', 18: 'sechs',
    7: 'sieben', 19: 'sieben',
    8: 'acht', 20: 'acht',
    9: 'neun', 21: 'neun',
    10: 'zehn', 22: 'zehn',
    11: 'elf', 23: 'elf',
    12: 'zwoelf', 24: 'zwoelf', 0: "zwoelf"
    }

def zeitinworten(zeitstempel):
    
    minute = int(time.strftime("%M", time.localtime(zeitstempel)))
    stunde = int(time.strftime("%H", time.localtime(zeitstempel)))

    # Ganze Stunde 1/2
    if minute < 8:
        if stunde == 1:
            uhrzeit = 'ein Uhr'
        elif stunde == 24:
            uhrzeit = 'Mitternacht'
        else:
            uhrzeit = f'{utabelle[stunde]} Uhr'

    else:
        # Stunde anpassen
        stunde += 1

        if stunde > 24:
            stunde -= 24       

        # Ganze Stunde 2/2
        if minute >= 53:
            if stunde == 1:
                uhrzeit = 'ein Uhr'
            elif stunde == 24:
                uhrzeit = 'Mitternacht'
            else:
                uhrzeit = f'{utabelle[stunde]} Uhr'

        # viertel
        elif minute >= 8 and minute < 23:
            uhrzeit = f'viertel {utabelle[stunde]}'

        # halb
        elif minute >= 23 and minute < 38:
             uhrzeit = f'halb {utabelle[stunde]}'

        # dreiviertel
        elif minute >= 38 and minute < 53:
            uhrzeit = f'dreiviertel {utabelle[stunde]}'

    return uhrzeit


def wetter():
    #Datenabruf
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city_name}&units=metric&appid={api_key}&lang=de'
    res = requests.get(url)
    data = res.json()

    # Abgerufene Rohdaten anzeigen
    #from pprint import pprint
    #pprint(data)


    # Display leeren
    #os.system('clear')

    # Sonnenaufgang
    sunrise = int(data['city']['sunrise'])

    # Sonnenuntergang
    sunset = int(data['city']['sunset'])

    # Orstangaben
    ortsname = data['city']['name']
    ortsid = data['city']['id']

    # Ausgabe Heute
    datum = datetime.now().strftime('%d.%m.%Y')
    statuszeile = f'Es ist {zeitinworten(time.time())} am {datum}'
    

    #MiniMax Zukunft
    mintemp = 100
    maxtemp = -100
    maxzeit = 0
    maxwind = 0

    for x in range(len(data['list'])):
        maxzeit = data['list'][x]['dt']

        if round(data['list'][x]['main']['temp']) > maxtemp:
            maxtemp = round(data['list'][x]['main']['temp'])

        if round(data['list'][x]['main']['temp']) < mintemp:
            mintemp = round(data['list'][x]['main']['temp'])

        if round(data['list'][x]['wind']['speed']) > maxwind:
            maxwind = round(data['list'][x]['wind']['speed'])

    # Berechnung Zeitraum der Prognose
    jetzt = time.time()
    zeitraum_sekunden = maxzeit - jetzt
    zeitraum = round(zeitraum_sekunden / 60 / 60 / 24) # Umrechnung von Sekunden in Tage


    # Vorhersage
    vorhersage_header = f'Wettervorhersage {wegmitdenumlauten(ortsname)}:'

    vorhersage = ''
    for x in range(8):
    
        # Zeitpunkt
        zeitpunkt = UNIX2HHMM(data['list'][x]['dt'])

        # Temperatur
        temperatur = round(data['list'][x]['main']['temp'])

        # Beschreibung
        inworten_roh = data['list'][x]['weather'][0]['description'].lower()
        inworten = wegmitdenumlauten(inworten_roh)       

        # Windgeschwindigkeit
        wind = round(data['list'][x]['wind']['speed'])

        # Ausgabe
        vorhersage += f'{zeitpunkt} {temperatur:>2.0f}C {wind:>2.0f}km/h {inworten}\n'
    

    # Ausgabe
    vorhersage_weit = f'{zeitraum} Tage: {mintemp}C bis {maxtemp}C, max. {maxwind}km/h'
    tageslicht = f'Hell von {zeitinworten(sunrise)} bis {zeitinworten(sunset)}'

    wettervorhersage = f'{statuszeile}\n\n{vorhersage_header}\n{vorhersage}\n{vorhersage_weit}\n{tageslicht}'
    return wettervorhersage
    


################################
#      Ab hier Anzeige         #
################################


spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)

# give them all to our drivers
print("Creating display")
display = Adafruit_SSD1675(122, 250,        # 2.13" HD mono display
    spi,
    cs_pin=ecs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
)

display.rotation = 3

while True:
    # clear the buffer
    print("Clear buffer")
    display.fill(Adafruit_EPD.WHITE)
    display.pixel(10, 100, Adafruit_EPD.BLACK)

    wettervorhersage = wetter()
    print("Draw text")
    display.text(f'{wettervorhersage}', 5, 5, Adafruit_EPD.BLACK)
    display.display()        
        
    print('Warten, biis zur nächsten Runde')
    time.sleep(200) # Zeit in Sekunden bis zur nächsten Aktualisierung
