import board
import time
import os
import wifi
import ssl
import socketpool
import adafruit_requests
import adafruit_ntp
import rtc
import displayio
import terminalio
from adafruit_display_text import label, wrap_text_to_lines

# configuration
URL = "https://us-central1-ucfeather.cloudfunctions.net/bq-trend-telltale"
TZ_OFFSET = -5 

# google brand color palette
G_COLORS = [0x4285F4, 0xDB4437, 0xF4B400, 0x0F9D58]

# display setup
display = board.DISPLAY
main_group = displayio.Group()
display.root_group = main_group

# white background
bg_bitmap = displayio.Bitmap(display.width, display.height, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0xFFFFFF 
main_group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

# header group
header_group = displayio.Group()
header_group.x = 10
header_group.y = 20
main_group.append(header_group)

# wrapping term label
term_label = label.Label(terminalio.FONT, text="LOADING...", color=0x000000, scale=2)
term_label.anchor_point = (0.5, 0.5)
term_label.anchored_position = (display.width // 2, display.height // 2 + 30)
term_label.line_spacing = 1.2
main_group.append(term_label)

# functions

def create_google_header(text):
    while len(header_group) > 0:
        header_group.pop()
    
    current_x = 0
    for i, char in enumerate(text):
        char_color = G_COLORS[i % len(G_COLORS)]
        
        char_label = label.Label(terminalio.FONT, text=char, color=char_color, scale=2)
        char_label.x = current_x
        header_group.append(char_label)
        
        bold_shadow = label.Label(terminalio.FONT, text=char, color=char_color, scale=2)
        bold_shadow.x = current_x + 1
        header_group.append(bold_shadow)
        
        current_x += 13 if char != " " else 8

def connect_and_sync():
    ssid = os.getenv("WIFI_SSID")
    pw = os.getenv("WIFI_PASSWORD")
    try:
        wifi.radio.connect(ssid, pw)
    except:
        wifi.radio.connect("RedRover")
    pool = socketpool.SocketPool(wifi.radio)
    ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)
    rtc.RTC().datetime = ntp.datetime
    return pool

def get_date_string():
    yesterday_seconds = time.time() - 86400
    t = time.localtime(yesterday_seconds)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[t.tm_mon-1]} {t.tm_mday:02d}'s Top Term:"

# main logic
pool = connect_and_sync()
requests = adafruit_requests.Session(pool, ssl.create_default_context())

while True:
    if wifi.radio.connected:
        create_google_header(get_date_string())
        try:
            with requests.get(URL) as response:
                if response.status_code == 200:
                    term = response.text.strip().upper()
                    wrapped_text = "\n".join(wrap_text_to_lines(term, 18))
                    term_label.text = wrapped_text
                    term_label.color = G_COLORS[int(time.monotonic()) % 4]
        except:
            term_label.text = "ERROR"
    time.sleep(3600)