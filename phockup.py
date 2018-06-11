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

version = '1.6.4-relict'
printer = Printer()


def main(argv):
    check_dependencies()

    move = False
    link = False
    date_regex = None
    only_images = False
    only_videos = False
    output_file_name_format = '%Y%m%d-%H%M%S'
    dir_format = os.path.sep.join(['%Y', '%m', '%d'])

    try:
        opts, args = getopt.getopt(argv[2:], "d:r:mlhiv",
                                   ["date=", "regex=", "move", "link", "help", "only-images", "only-videos"])
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
            dir_format = Date().parse(arg)

        if opt in ("-m", "--move"):
            move = True
            printer.line("Using move strategy!")

        if opt in ("-l", "--link"):
            link = True
            printer.line("Using link strategy!")

        if opt in ("-i", "--only-images"):
            only_images = True
            printer.line("Process only images with meta-information!")

        if opt in ("-v", "--only-videos"):
            only_videos = True
            printer.line("Process only images with meta-information!")

        if opt in ("-o", "--output-name"):
            output_file_name_format = arg
            printer.line("OutputFileName format: %s" % output_file_name_format)

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
        argv[0], argv[1],
        dir_format=dir_format,
        move=move,
        link=link,
        only_images=only_images,
        only_videos=only_videos,
        output_file_name_format=output_file_name_format,
        date_regex=date_regex
    )


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        printer.empty().line('Exiting...')
        sys.exit(0)
