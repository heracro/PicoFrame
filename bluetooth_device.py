import bluetooth
import random
import struct
import time
from machine import Pin

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

# For the characteristic

_PICOFRAME_CHARACTERISTIC_UUID = bluetooth.UUID('00001002-0000-1000-8000-00805F9B34FB')
_PICOFRAME_DESCRIPTOR_UUID = bluetooth.UUID('00001003-0000-1000-8000-00805F9B34FB')

_PICOFRAME_DESCRIPTOR = (
    _PICOFRAME_CHARACTERISTIC_UUID,
    _FLAG_READ | _FLAG_WRITE | _FLAG_NOTIFY,

)

# Custom name
_PICOFRAME_CHARACTERISTIC = (
    _PICOFRAME_CHARACTERISTIC_UUID,
    _FLAG_READ | _FLAG_WRITE | _FLAG_NOTIFY,
    (_PICOFRAME_DESCRIPTOR,)
)

# For the service
_PICOFRAME_SERVICE_UUID = bluetooth.UUID('00001001-0000-1000-8000-00805F9B34FB')

_PICOFRAME_SERVICE = (_PICOFRAME_SERVICE_UUID, (_PICOFRAME_CHARACTERISTIC,))

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)


def advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
    payload = bytearray()

    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value

    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)),
    )

    if name:
        name_bytes = bytes(name, "utf-8")
        _append(_ADV_TYPE_NAME, name_bytes)

    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)

    if appearance:
        _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))
    print(name)
    return payload


class BluetothDevice:
    def __init__(self, ble, name="Pico"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        ((self._handle_tx, self._handle_rx),
         (self._picoframe_characteristic, self._picoframe_descriptor,)) = self._ble.gatts_register_services(
            (_UART_SERVICE, _PICOFRAME_SERVICE), )

        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback


def demo():
    led_onboard = Pin("LED", Pin.OUT)
    ble = bluetooth.BLE()
    bluetooth_device = BluetothDevice(ble)

    def on_rx(v):
        print("RX", v)

    bluetooth_device.on_write(on_rx)

    i = 0
    while True:
        if bluetooth_device.is_connected():
            led_onboard.on()
            for _ in range(3):
                data = str(i) + "_"
                print("TX", data)
                bluetooth_device.send(data)
                i += 1
        time.sleep_ms(100)


if __name__ == "__main__":
    demo()






