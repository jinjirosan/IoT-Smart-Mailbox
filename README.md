# IoT-Smart-Mailbox a.k.a. Bernard de Brievenbuschecker

Living in an apartment is great however you don't really have a view on your mailbox which is downstairs in the lobby. So to minimize a failed trip to an empty mailbox I've created a mailbox checker.

There are two detection circtuis:
- mail-in : for any new mail a notfication is send by email and a envelope icon is displayed on the Magic Mirror.
- mail-out: so if someone from the house already pciked up the mail everyone is notified by email and the envelope icon is removed from the Magic Mirror

The mailbox is to far down (or we live to far up), there is no normal wifi connectivity. I'm using a SigFox module to send the notification to the SigFox Network which in turn sends the email/notification to us. The cool thing is, this works regardless of my house IoT is operational.

This is version 2.x utilizing an IR Break Beam circuit instead of a REED magnet contact. The mailbox has an outward going flap and the opening is just wide enough for the widest specified mail. I've had the magnet on the flap knocked off multiple times by the mailman due to bol.com book packages are exactly the width of the opening. Need something else.

# How it works

- The "mail-in" detection is a full width IR Break Beam circuit so nothing is attached on the flap and nothing is in the way of the incomming mail path.
- The "mail-out" detection is a REED magnet contact switch in the inner door. This door is large enough so this works fine.