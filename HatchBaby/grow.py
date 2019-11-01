import pygatt
import time
import collections
import threading

class Grow(object):
  _mac_address = None
  _timeout = None
  _gatt_obj = None
  _battery_level = 0
  _num_samples = 0
  _desired_samples = 1
  _last_sample_num = None
  _tare = None
  _sample_list = None
  _active_status = None
  _hci_device = None
  _result_available = threading.Event()

  def __init__(self, mac_address, connect = True, timeout = 30, sampling_queue_size = 50, hci_device = 'hci0'):
    self._mac_address = mac_address
    self._timeout = timeout
    self._sample_list = collections.deque(maxlen = sampling_queue_size)
    self._hci_device = hci_device
    if connect:
      self.connect()

  def tare(self, sample_size = 10):
    self._result_available.clear()
    self._active_status = 'tare_started'
    self._num_samples = 0
    self._desired_samples = sample_size
    if self._sample_list.maxlen != None and sample_size > self._sample_list.maxlen:
      raise Exception("Desired sample size > sample_queue_size set in constructor")

    self._result_available.wait()
    s = 0
    for i in range(len(self._sample_list) - sample_size, len(self._sample_list)):
      s += self._sample_list[i]
    self._tare = s / sample_size
    self._active_status = None
    return self._tare

  def weigh(self, sample_size = 4, guess_tare = False):
    tare = self._tare
    self._result_available.clear()
    if tare == None:
      if guess_tare == False:
        raise Exception("You haven't tared the scale yet.  Call tare() first before weighing")
      elif sample_size + 10 > self._sample_list.maxlen:
        raise Exception("Not enough space in the sampling queue to guess the tare.  Either call tare() separately or set a higher sampling_queue_size in constructor")
      elif len(self._sample_list) < 10:
        raise Exception("Not enough samples collected yet to guess the tare.  Either call tare() separately or wait longer before weighing")
      else:
        s = 0
        for i in range(0,10):
          s += self._sample_list[i]
        tare = s / 10.0

    self._active_status = 'weigh_started'
    self._num_samples = 0
    self._desired_samples = sample_size
    self._result_available.wait()

    s = 0
    for i in range(len(self._sample_list) - sample_size,len(self._sample_list)):
      s += self._sample_list[i]
    weight = abs((s / sample_size) - tare)
    self._active_status = None
    return weight

  def weigh_grams(self, sample_size = 4, guess_tare = False):
    weight = self.weigh(sample_size = sample_size, guess_tare = guess_tare)
    return weight * 0.00855

  def weigh_pounds_ounces(self, sample_size = 4, guess_tare = False):
    weightInGrams = self.weigh_grams(sample_size = sample_size, guess_tare = guess_tare)
    totalOunces = 0.035274 * weightInGrams
    pounds = int(totalOunces / 16)
    ounces = totalOunces % 16
    return { 'pounds': pounds, 'ounces': ounces }

  def _adc_callback(self, handle, adcByteArr):
    self._last_sample_num = adcByteArr.pop()
    adcByteArr.reverse()
    weightInternal = int.from_bytes(adcByteArr, byteorder='big', signed=False)
    self._sample_list.append(weightInternal)
    if self._active_status != None:
      self._num_samples += 1

      if self._num_samples >= self._desired_samples:
        self._result_available.set()

  def connect(self):
    adapter = pygatt.GATTToolBackend(hci_device=self._hci_device)
    adapter.start()
    self._gatt_obj = adapter.connect(self._mac_address, address_type=pygatt.BLEAddressType.random, timeout=self._timeout)
    status = self._gatt_obj.char_read("02230006-5efd-47eb-9c1a-de53f7a2b232").decode("utf-8")
    if (status != 'OK'):
      raise Exception("Connected to device, but status did not read 'OK'.  Device status reads %s" % status)

    self._gatt_obj.subscribe("02230001-5efd-47eb-9c1a-de53f7a2b232", callback=self._adc_callback)

  def get_battery_level(self):
    if self._gatt_obj == None:
      raise Exception('Could not get battery level.  Have you not connected yet?')

    self._battery_level = self._gatt_obj.char_read("00002a19-0000-1000-8000-00805f9b34fb")[0]
    return self._battery_level
