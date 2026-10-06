# The private network for the phone: your steps (docs/PHONE-PLAN.md section 7)

Written with release 1.0.16. Everything here is yours to do; I never set up networking (`CLAUDE.md`). Do them in
this order, after 1.0.16 is your everyday JARVIS (step 5 of the plan). Send a photo when a step is done.

## 1. Tailscale on the PC (jonny account, about ten minutes)

1. In a browser: tailscale.com > Get started. Create an account (sign in with Google, Apple, Microsoft or GitHub).
   The Personal plan is free for personal use; read the current terms as you sign up.
2. Download Tailscale for Windows from the same site, run the installer, sign in with that account when it asks.
3. Tailscale's icon appears near the clock. Click it: it shows "Connected" and **this PC's name** (for example
   `thegrizzlybear`) and its address (starts with `100.`). Write the name down; the phone will type it.
4. Leave Tailscale running. It starts with Windows from now on.

## 2. Tailscale on the iPhone (five minutes)

1. App Store > search Tailscale > Get. Open it, sign in with the **same account** as on the PC.
2. Allow it to add a VPN configuration when iOS asks (that is how Tailscale works; it only routes traffic to your own
   devices).
3. The app lists your devices: the PC should be there with a green dot. Leave the switch at the top on.

## 3. Keep the PC awake

Windows Settings > System > Power & battery (or Power) > Screen and sleep: "When plugged in, put my device to sleep
after" = **Never**. The screen may still turn off; that is fine. JARVIS keeps running.

## 4. The switch on the PC (after the 1.0.16 update)

1. JARVIS > Settings > Devices > **Private network**: turn the switch on. Port 8790 unless something else on the PC
   uses it (JARVIS says so if the port cannot be opened).
2. The line under it turns green and says where the door is: the address and the name to type into the phone. If it
   says Tailscale is not running or not signed in, fix that first (step 1).
3. Nothing else changes: JARVIS on the PC keeps working exactly as before, and nothing is open to the internet.

## 5. Pair the phone (phone app installed, section 3 of phone/ios/README.md)

1. PC: Settings > Devices, name `Jonny's iPhone`, kind phone, **PAIR A DEVICE**. An eight-digit code shows for five
   minutes.
2. Phone: the PC's Tailscale name (or its 100. address), port 8790, the code, PAIR.
3. PC: in the phone's row tick **microphone** and **speakers**; tick **May save memories and tasks** if you want the
   phone to be able to save things (decision D2 of the plan).
4. Phone, Ask screen: the state reads STANDING BY and the readouts fill in. Ask something.

## 6. Away from home

Wi-Fi off, cellular on, Tailscale on in the phone's Tailscale app: the phone reaches the PC the same way. If the Ask
screen says CORE NOT REACHED: check Tailscale on the phone (connected?), on the PC (connected? the PC awake?), and the
switch in Settings > Devices (on, green line?).
