# IoT-Smart-Mailbox a.k.a. Bernard de Brievenbuschecker

Living in an apartment is great however you don't really have a view on your mailbox which is downstairs in the lobby. So to minimize a failed trip to an empty mailbox I've created a mailbox checker.

There are two detection circtuis:
- mail-in : for any new mail a notfication is send by email and a envelope icon is displayed on the Magic Mirror.
- mail-out: so if someone from the house already pciked up the mail everyone is notified by email and the envelope icon is removed from the Magic Mirror

The mailbox is to far down (or we live to far up), there is no normal wifi connectivity. I'm using a SigFox module to send the notification to the SigFox Network which in turn sends the email/notification to us. The cool thing is, this works regardless of my house IoT is operational.

The mailbox has an outward going flap and the opening is just wide enough for the widest specified mail. I've had the magnet (hardware platform 1.x) on the flap knocked off multiple times by the mailman due to bol.com book packages are exactly the width of the opening. Need something else.
~~This is version 2.x utilizing an IR Break Beam circuit instead of a REED magnet contact.~~ 

This is version 3.x utilizing a VCNL4040 Proximity Sensor on the floor of the mailbox.

# How it works

- The "mail-in" detection is a proximity sensor circuit mounted in the middle of the floor of the mailbox so nothing is attached on the flap and nothing is in the way of the incomming mail path. When a letter or package is dropped, the distance to the proximity sensor is shortened and an alert is sent.
- The "mail-out" detection is a REED magnet contact switch in the inner door. This door is large enough so this works fine.

# The platform

Hardware platform  
* Pimoroni Pici Lipo
* Dual ARM Cortex M0+ running at up to 133Mhz
* VCNL4040 Proximity sensor
* LPWAN SFM10R1 SigFox Module
* REED switch (inner door)
 
Power              
* 3.7v - 4400 mAh (dual 18650) LiPo

Codebase           
* MicroPython 1.22

# Console log

## For incoming mail:
```
Mail has been detected!
Battery Voltage: 4.11V, Percentage: 92%
Initiating Sigfox Transmission...
Sending to Sigfox:
Payload: 015c03
  - Mail Detected: Yes
  - Mail Collected: No
  - Battery Percentage: 92%
  - Proximity: 1
  - Charging: Yes
Command to be sent: AT$SF=015c03

Response after send: OK
Sigfox message sent successfully.
```

## For picking up mail
```
Door opened! Detected change on pin: Pin(GPIO8, mode=IN, pull=PULL_UP)
Initiating Sigfox Transmission...
Sending to Sigfox:
Payload: 00e301
  - Mail Detected: No
  - Mail Collected: Yes
  - Battery Percentage: 99%
  - Proximity: 0
  - Charging: Yes
Command to be sent: AT$SF=00e301

Response after send: OK
Sigfox message sent successfully.
Mail detection reset.
Door closed! Detected change on pin: Pin(GPIO8, mode=IN, pull=PULL_UP)
```