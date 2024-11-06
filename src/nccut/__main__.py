import re
import argparse
import os
from progress.bar import ChargingBar
bar = ChargingBar("Loading App", max=3)
bar.next()
from nccut.nccut import NcCut
bar.next()


def run():
    """
    Runs app with command line. Can also specify file to load and configuration file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-file', nargs='?', default=None, help="File path for image or NetCDF file")
    parser.add_argument('-config', nargs='?', default=None, help="File path for config file: 'nccut_config.toml'")
    args = parser.parse_args()
    file = args.file
    config = args.config
    if file:
        if not os.path.isfile(file):
            print("ERROR: File Not Found")
            return
        elif len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', str(file))) > 0:
            print("ERROR: Invalid File Name")
            return
        elif not os.path.splitext(file)[1] in [".jpg", ".jpeg", ".png", ".nc"]:
            print("ERROR: File not an Image or NetCDF File")
            return
    if config:
        if not os.path.isfile(config):
            print("ERROR: Config File Not Found")
            return
        elif len(re.findall(r'[^A-Za-z0-9_:\\.\-/]', str(file))) > 0:
            print("ERROR: Invalid Config File Path")
            return
        elif not os.path.basename(config) == "nccut_config.toml":
            print("ERROR: File Passed is not NcCut Config File (file must be named 'nccut_config.toml)")
            return
    bar.next()
    bar.finish()
    NcCut(file=file, config=config).run()


if __name__ == "__main__":
    run()
