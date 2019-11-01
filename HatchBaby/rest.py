import pygatt
from enum import IntEnum

class RestSongs(IntEnum):
  none = 0
  heartbeat = 1
  stream = 2
  white_noise = 3
  laundry = 4
  ocean = 5
  street_noise = 6
  rain = 7
  birds = 9
  crickets = 10
  go_to_sleep_song = 11
  twinkle_twinkle_song = 13
  rockabye_baby_song = 14

# part of this is derived from https://github.com/Marcus-L/m4rcus.HatchBaby.Rest/tree/master/m4rcus.HatchBaby.Rest
class Rest(object):
  _mac_address = None
  _timeout = None
  _gatt_obj = None
  _active_status = None
  _hci_device = None
  [_song, _volume] = [None, None]
  [_red, _green, _blue, _brightness] = [None, None, None, None]
  _power = None

  def __init__(self, mac_address, connect = True, timeout = 30, hci_device = 'hci0'):
    self._mac_address = mac_address
    self._timeout = timeout
    self._hci_device = hci_device
    if connect:
      self.connect()

  def connect(self):
    adapter = pygatt.GATTToolBackend(hci_device=self._hci_device)
    adapter.start()
    self._gatt_obj = adapter.connect(self._mac_address, address_type=pygatt.BLEAddressType.random, timeout=self._timeout)
    self.update_status()

  def update_status(self):
    if self._gatt_obj == None:
      raise Exception('Could not update status.  Have you not connected yet?')

    status_bytearray = self._gatt_obj.char_read("02260002-5efd-47eb-9c1a-de53f7a2b232")
    self._command_num = int.from_bytes(status_bytearray[4:5], byteorder='big', signed=False)
    [self._red, self._green, self._blue, self._brightness] = status_bytearray[6:10]
    [self._song, self._volume] = status_bytearray[11:13]
    self._power = (status_bytearray[14] ^ 0xdf) > 0

  def _send_command(self, command, values):
    if self._gatt_obj == None:
      raise Exception('Could not update status.  Have you not connected yet?')
    byte_array = bytearray(command.encode())
    for v in values:
      byte_array.extend(bytearray("{:02x}".format(v).encode()))
    self._gatt_obj.char_write('02240002-5efd-47eb-9c1a-de53f7a2b232',byte_array)

  def set_volume(self, volume):
    self._send_command('SV', [volume])

  def set_powered(self, power_on=True):
    command_value = 1 if power_on else 0
    self._send_command('SI', [command_value])

  def turn_on(self):
    self.set_powered(True)

  def turn_off(self):
    self.set_powered(False)

  def set_color(self, red, green, blue, brightness = 255):
    self._send_command('SC',[red, green, blue, brightness])

  def set_color_rainbow(self, brightness = 255):
    self._send_command('SC', [254, 254, 254, brightness])

  def set_song(self, song, volume=None):
    if volume != None:
      self.set_volume(volume)
    self._send_command('SN', [song])
