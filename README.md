# blinky-pico

Pulls a JSON configuration file from a http server (https not supported) and based on the
configuration data displays animations on a neopixel strip.

Runs under Micropython on a Pico-W.

Requires a `config.json` on the device:

```json
{
  "ssid": "My Wifi SSID",
  "password": "My Wifi password",
  "config": "http://where.to.pull.the/config.json",
  "leds": <how many leds>
}
```

Also copy the `code.py` and `blinky` directory onto the device. It should run on boot and after each
run through the animation will pull any new config file.

Understanding the config format is currently left as an exercise, it is parsed in [blinky/animation.py](blinky/animation.py)

The `test` script runs the animation in CPython on a regular computer displaying the LEDs as lines
of coloured asterisks.
