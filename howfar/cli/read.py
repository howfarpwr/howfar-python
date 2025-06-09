import csv
import os
import sys
from ..database import HowFarDatabase


def main():

    args: list[str] = sys.argv[1:]
    if len(args) != 2:
        print("howfar-read: read measurement data from HowFar and output it as CSV", file=sys.stderr)
        print("Usage: %s input.uf2 output.csv" % os.path.basename(sys.argv[0]), file=sys.stderr)
        sys.exit(1)
    filename_uf2, filename_csv = args

    # read database header
    uf2_bytes = open(filename_uf2, "rb").read()
    database = HowFarDatabase(uf2_bytes)

    # write csv file
    with open(filename_csv, "w", newline="") as csvfile:
        # write CSV header
        writer = csv.writer(csvfile)
        writer.writerow(database.columns())
        # write CSV content
        for record in database.records():
            writer.writerow(record)


if __name__ == "__main__":
    main()
