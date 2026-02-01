import board
import time
import os
import wifi
import ssl
import socketpool
import adafruit_requests
import displayio
import terminalio
from adafruit_display_text import label

# --- Configuration ---
# Ensure these match your Cloud Function URL
URL = "https://us-central1-ucfeather.cloudfunctions.net/bq-trend-telltale"

# Google Brand Colors
G_BLUE = 0x4285F4
G_RED = 0xEA4335
G_YELLOW = 0xFBBC05
G_GREEN = 0x34A853

# --- Display Setup ---
display = board.DISPLAY
# The Reverse TFT is 240x135. We rotate if necessary, 
# but default is usually correct for the 'Reverse' layout.
main_group = displayio.Group()
display.root_group = main_group

# 1. Background (Black for high contrast)
bg_bitmap = displayio.Bitmap(display.width, display.height, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0x000000
main_group.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

# 2. Header Label: "{DATE}'s Top Term:"
header_label = label.Label(terminalio.FONT, text="", color=G_BLUE)
header_label.anchor_point = (0.5, 0)
header_label.anchored_position = (display.width // 2, 15)
header_label.scale = 1
main_group.append(header_label)

# 3. Term Label: The actual BigQuery result
term_label = label.Label(terminalio.FONT, text="LOADING...", color=G_YELLOW)
term_label.anchor_point = (0.5, 0.5)
term_label.anchored_position = (display.width // 2, display.height // 2 + 15)
term_label.scale = 2 # Initial scale
main_group.append(term_label)

# --- Helper Functions ---
def get_date_string():
    """Returns a string like 'Feb 01'"""
    t = time.localtime()
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[t.tm_mon-1]} {t.tm_mday:02d}"

def update_telltale(requests_session):
    print("Updating...")
    try:
        # 1. Update Date Header
        header_label.text = f"{get_date_string()}'s Top Term:"
        
        # 2. Fetch from Cloud Function
        with requests_session.get(URL) as response:
            if response.status_code == 200:
                term = response.text.strip().upper()
                
                # 3. Smart Scaling (Avoid text clipping)
                if len(term) > 15:
                    term_label.scale = 1
                elif len(term) > 8:
                    term_label.scale = 2
                else:
                    term_label.scale = 3
                
                term_label.text = term
                # Change color every update for variety
                term_label.color = [G_RED, G_YELLOW, G_GREEN][time.monotonic_ns() % 3]
            else:
                term_label.text = "HTTP ERR"
                term_label.color = G_RED
    except Exception as e:
        print(f"Error: {e}")
        term_label.text = "WIFI RECONNECTING"
        term_label.color = G_RED

# --- Network Initialization ---
print("Connecting to WiFi...")
wifi.radio.connect(os.getenv("WIFI_SSID"), os.getenv("WIFI_PASSWORD"))
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# --- Execution Loop ---
while True:
    update_telltale(requests)
    
    # Wait for 1 hour (3600 seconds)
    # The display stays on while the chip 'sleeps' in this loop
    time.sleep(3600)