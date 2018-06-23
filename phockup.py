#!/usr/bin/env python3
import getopt
import os
import re
import sys

from src.date import Date
from src.dependency import check_dependencies
from src.help import help
from src.phockup import Phockup
from src.printer import Printer

version = '1.7.0-relict'
printer = Printer()


def main(argv):
    check_dependencies()

    move = False
    link = False
    date_regex = None
    images_output_path = None
    videos_output_path = None
    unknown_output_path = None
    log_file_name = None
    output_file_name_format = '%Y%m%d-%H%M%S'
    dir_format = os.path.sep.join(['%Y', '%m', '%d'])

    try:
        opts, args = getopt.getopt(argv[1:], "d:r:o:i:u:v:f:mlh",
                                   ["date=",
                                    "regex=",
                                    "move",
                                    "link",
                                    "help",
                                    "log-filename=",
                                    "images-output=",
                                    "videos-output=",
                                    "unknown-output=",
                                    "output-name="])
    except getopt.GetoptError:
        help(version)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help(version)
            sys.exit(2)

        if opt in ("-d", "--date"):
            if not arg:
                printer.error("Date format cannot be empty")
                sys.exit(2)
            dir_format = Date().parse(arg)

        if opt in ("-m", "--move"):
            move = True

        if opt in ("-l", "--link"):
            link = True

        if opt in ("-i", "--images-output"):
            images_output_path = arg

        if opt in ("-v", "--videos-output"):
            videos_output_path = arg

        if opt in ("-u", "--unknown-output"):
            unknown_output_path = arg

        if opt in ("-f", "--log-filename"):
            log_file_name = arg

        if opt in ("-o", "--output-name"):
            if not arg:
                printer.error("Output file name format cannot be empty")
                sys.exit(2)
            output_file_name_format = arg

        if opt in ("-r", "--regex"):
            try:
                date_regex = re.compile(arg)
            except (ValueError, TypeError):
                printer.error("Provided regex is invalid!")
                sys.exit(2)

    if link and move:
        printer.error("Can't use move and link strategy together!")
        sys.exit(1)

    if len(argv) < 2:
        help(version)
        sys.exit(2)

    return Phockup(
        argv[0],
        dir_format=dir_format,
        move=move,
        link=link,
        images_output_path=images_output_path,
        videos_output_path=videos_output_path,
        unknown_output_path=unknown_output_path,
        output_file_name_format=output_file_name_format,
        date_regex=date_regex,
        log_file_name=log_file_name
    )


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        printer.empty().line('Exiting...')
        sys.exit(0)
