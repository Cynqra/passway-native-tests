"""Configure the explicitly selected test AVD; never alter other devices."""
import os
import pathlib
import re


def configure(home, name):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
        raise ValueError('Invalid test AVD name')
    path = pathlib.Path(home) / (name + '.avd') / 'config.ini'
    settings = {'hw.lcd.width': '540', 'hw.lcd.height': '1200',
                'hw.lcd.density': '220', 'showDeviceFrame': 'no'}
    lines = [line for line in path.read_text().splitlines()
             if line.split('=', 1)[0].strip() not in settings]
    path.write_text('\n'.join(lines + [k + '=' + v for k, v in settings.items()]) + '\n')
    print(f'Configured {name}: physical 540x1200 at 220 dpi')


if __name__ == '__main__':
    configure(os.environ['ANDROID_AVD_HOME'],
              os.environ.get('PASSWAY_AVD_NAME', 'passway-native'))
