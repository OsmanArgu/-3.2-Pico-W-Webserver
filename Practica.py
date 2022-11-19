import rp2
import network
import ubinascii
from machine import Pin,PWM
import urequests as requests
import time
from secrets import secrets
import socket
import utime

# Set country to avoid possible errors
rp2.country('DE')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# If you need to disable powersaving mode
# wlan.config(pm = 0xa11140)

# See the MAC address in the wireless chip OTP
mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
print('mac = ' + mac)

# Other things to query
# print(wlan.config('channel'))
# print(wlan.config('essid'))
# print(wlan.config('txpower'))

# Load login data from different file for safety reasons
ssid = secrets['ssid']
pw = secrets['pw']

wlan.connect(ssid, pw)

# Wait for connection with 10 second timeout
timeout = 10
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    timeout -= 1
    print('Waiting for connection...')
    time.sleep(1)

# Define blinking function for onboard LED to indicate error codes    
def blink_onboard_led(num_blinks):
    led = machine.Pin('LED', machine.Pin.OUT)
    for i in range(num_blinks):
        led.on()
        time.sleep(.2)
        led.off()
        time.sleep(.2)
    
# Handle connection error
# Error meanings
# 0  Link Down
# 1  Link Join
# 2  Link NoIp
# 3  Link Up
# -1 Link Fail
# -2 Link NoNet
# -3 Link BadAuth

wlan_status = wlan.status()
blink_onboard_led(wlan_status)

if wlan_status != 3:
    raise RuntimeError('Wi-Fi connection failed')
else:
    print('Connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    
# Function to load in html page    
def get_html(html_name):
    with open(html_name, 'r') as file:
        html = file.read()
        
    return html

# HTTP server with socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('Listening on', addr)
led = machine.Pin('LED', machine.Pin.OUT)

#Servo
servo = PWM(Pin(0))
servo.freq(50)

#LED
rojo = Pin(18,Pin.OUT)
verde = Pin(19,Pin.OUT)
azul = Pin(20,Pin.OUT)
#BUZZER
buzzer = Pin(21,Pin.OUT)
# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('Client connected from', addr)
        r = cl.recv(1024)
        # print(r)
        
        r = str(r)
        #Codigo Motor
        led_on = r.find('?led=on')
        led_off = r.find('?led=off')
        print('led_on = ', led_on)
        print('led_off = ', led_off)
        
        led_ON = r.find('?led=ON')
        led_OFF = r.find('?led=OFF')
        print('led_ON = ', led_ON)
        print('led_OFF = ', led_OFF)
        
        if led_on > -1:
            led.value(1)
            servo.duty_u16(1311)
            time.sleep(0.5)
            
        if led_off > -1:
            led.value(1)
            servo.duty_u16(7864)
            time.sleep(0.5)
            
        #Codigo Alarma
            
        if led_OFF >-1:
            rojo.off()
            verde.off()
            azul.off()
            buzzer.off()
        
        if led_ON >-1:
            
            rojo.off()
            verde.on()
            for i in range (3):
                buzzer.on()
                utime.sleep_ms(500)
                buzzer.off()
                utime.sleep_ms(500)
            verde.off()
            azul.on()
            for i in range (5):
                buzzer.on()
                utime.sleep_ms(100)
                buzzer.off()
                utime.sleep_ms(100)
            azul.off()
            rojo.on()
            utime.sleep_ms(3000)
            
        response = get_html('index.html')
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()
        
    except OSError as e:
        cl.close()
        print('Connection closed')
