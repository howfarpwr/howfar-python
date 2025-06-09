import os
import sys
from ..settings import HowFarSettings
from ..uf2 import convert_to_uf2


def main():
    # load default settings
    settings = HowFarSettings.defaults()

    # check command line args
    args: list[str] = sys.argv[1:]
    if len(args) == 0:
        print("howfar-configure: upload settings to HowFar", file=sys.stdout)
        print("Usage: %s d:\\optoconf.uf2 [setting=value ...]" % os.path.basename(sys.argv[0]), file=sys.stderr)
        print("Default settings:", file=sys.stderr)
        for key in settings.keys():
            print("  %s=%d" % (key, settings.get(key)), file=sys.stderr)
        sys.exit(1)

    # parse command line args
    filename = args[0]
    for arg in args[1:]:
        key, _, value = arg.partition("=")
        settings.set(key, value)

    # tell the user what's going to happen
    for key in settings.keys():
        print("%s=%s" % (key, settings.get(key)))

    # pack settings to UF2
    settings_bytes = settings.pack()
    uf2_bytes = convert_to_uf2(settings_bytes)

    # write settings to file
    open(filename, "wb").write(uf2_bytes)


if __name__ == "__main__":
    main()
