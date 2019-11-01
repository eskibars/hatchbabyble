import HatchBaby
import PySimpleGUI as sg
from pprint import pprint

device_mac = 'EF:92:F2:1B:5C:44'

growdevice = HatchBaby.Grow(device_mac, connect=False)

taringLayout = [ [ sg.Text('Connecting...', key='status', font=('Helvetica', 20)) ] ]
window = sg.Window('Starting Up...', taringLayout)
window.Finalize()
growdevice.connect()
window['status'].Update('Connected!  Taring...')
growdevice.tare()
window.Close()

weighingLayout = [
                   [ sg.Text('Place baby on the scale to weigh', font=('Helvetica', 25), justification='center') ],
                   [ sg.RealtimeButton('Tare', font=('Helvetica', 20)),
                     sg.Text('Weighing...', key='weight', font=('Helvetica', 22), justification='center', size=(20,2)),
                     sg.RealtimeButton('Exit', font=('Helvetica', 20)) ]
                 ]
window = sg.Window('Weighing Baby', weighingLayout, default_button_element_size=(12,1), auto_size_buttons=False)
while True:
  event, values = window.Read(timeout=1)

  try:
    if event == 'Tare':
      print('Taring')
      window.Element('weight').Update('Taring...')
      growdevice.tare()
    elif event in (None, 'Exit'):
      break
    else:
      weight = growdevice.weigh_pounds_ounces()
      window.Element('weight').Update('{0} lbs {1:.1f} oz'.format(weight['pounds'], weight['ounces']))
  except Exception as e:
    pprint(e)

print('Exiing')
window.Close()
