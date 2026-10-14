import pathlib,os
p=pathlib.Path(os.environ['ANDROID_AVD_HOME'])/'passway-native.avd/config.ini'
settings={'hw.lcd.width':'540','hw.lcd.height':'1200','hw.lcd.density':'220','showDeviceFrame':'no'}
lines=[x for x in p.read_text().splitlines() if x.split('=',1)[0] not in settings]
p.write_text('\n'.join(lines+[k+'='+v for k,v in settings.items()])+'\n')
print('Physical display configured to 540x1200 at 220 dpi for every Android user')
