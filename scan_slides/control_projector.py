import time
import gpiozero.pins


class Projector(object):
    def __init__(self, raspi_name='raspberrypi'):
        FORWARD_PIN = 20
        BACKWARD_PIN = 21
        STATUS_PIN = 16
        self.finished = False
        self.bswitch = gpiozero.DigitalOutputDevice(
            gpiozero.pins.pigpiod.PiGPIOPin(BACKWARD_PIN, host=raspi_name),
            active_high=False, initial_value=False)
        self.fswitch = gpiozero.DigitalOutputDevice(
            gpiozero.pins.pigpiod.PiGPIOPin(FORWARD_PIN, host=raspi_name),
            active_high=False, initial_value=False)
        self.status = gpiozero.Button(
           gpiozero.pins.pigpiod.PiGPIOPin(STATUS_PIN, host=raspi_name),
           pull_up=False)
        self.status.when_released = self.step_finished

    def step_finished(self):
        self.finished = True
        print("finished")

    def step(self, switch):
        self.finished = False
        switch.blink(0.5, n=1)
        dt = 0.0
        while not self.finished:
            step = 0.1
            time.sleep(step)
            dt += step
        print(dt)

    def forward(self):
        self.step(self.fswitch)

    def backward(self):
        self.step(self.bswitch)

    def close(self):
        self.bswitch.close()
        self.fswitch.close()
        self.status.close()
