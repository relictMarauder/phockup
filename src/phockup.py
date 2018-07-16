#!/usr/bin/env python3
import filecmp
import hashlib
import os
import shutil
import sys
import logging
from src.exif import Exif
from src.source_file import SourceFile, SourceFileType

ignored_files = (".DS_Store", "Thumbs.db")
ignored_folders = (".@__thumb")


class Phockup():
    def __init__(self, input_path, **args):
        self.log = self.setup_logger(args.get('log_file_name', None))
        self.counter_all_files = 0
        self.counter_video_files = 0
        self.counter_image_files = 0
        self.counter_unknown_files = 0
        self.counter_duplicates = 0
        self.counter_processed_files = 0
        self.log.info("Start processing....")
        input_path = os.path.expanduser(input_path)

        if input_path.endswith(os.path.sep):
            input_path = input_path[:-1]

        self.images_output_path = self.get_path_param('images_output_path', args)
        self.videos_output_path = self.get_path_param('videos_output_path', args)
        self.unknown_output_path = self.get_path_param('unknown_output_path', args)

        self.input_path = input_path

        self.dir_format = args.get('dir_format', os.path.sep.join(['%Y', '%m', '%d']))
        self.move = args.get('move', False)
        self.link = args.get('link', False)
        self.output_file_name_format = args.get('output_file_name_format', '%Y%m%d-%H%M%S')
        self.date_regex = args.get('date_regex', None)
        self.log_config()
        try:
            self.log.info("Checking directories...")
            self.check_directories()
            self.log.info("Processing files...")
            self.walk_directory()
            self.log.info(
                "All files are processed: %d duplicates from %d files" % (
                    self.counter_duplicates, self.counter_processed_files))
            self.log.info("Processed images: %d, videos: %d, unknown %d from %d" % (
                self.counter_image_files, self.counter_video_files, self.counter_unknown_files, self.counter_all_files))
            self.log.handlers = []
        except Exception as ex:
            self.log.exception(ex, exc_info=True)
            self.log.handlers = []
            sys.exit(1)

    def log_config(self):
        self.log.info('Config:')
        if self.images_output_path is None:
            self.log.info("Skip processing images with meta-information")
        else:
            self.log.info("Output path for images with meta-information: %s" % self.images_output_path)

        if self.videos_output_path is None:
            self.log.info("Skip processing videos with meta-information")
        else:
            self.log.info("Output path for videos with meta-information: %s" % self.videos_output_path)

        if self.unknown_output_path is None:
            self.log.info("Skip processing unknown files")
        else:
            self.log.info("Output path for unknown: %s" % self.unknown_output_path)

        if self.date_regex:
            self.log.info("The reg exp for timestamp retrieving: %s" % self.date_regex)

        self.log.info("OutputFileName format: %s" % self.output_file_name_format)

        self.log.info("OutputDir format: %s" % self.dir_format)

        if self.link:
            self.log.info("Using link strategy!")

        if self.move:
            self.log.info("Using move strategy!")

    def setup_logger(self, log_file_name=None):
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        screen_handler = logging.StreamHandler(stream=sys.stdout)
        screen_handler.setFormatter(formatter)

        if log_file_name is not None:
            handler = logging.FileHandler(log_file_name, mode='a')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.addHandler(screen_handler)
        return logger

    def get_path_param(self, param_name, params):
        path = params.get(param_name, None)
        path = None if path is None else os.path.expanduser(path)
        if path is not None and path.endswith(os.path.sep):
            return path[:-1]
        return path

    def check_directories(self):
        """
        Check if input and output directories exist.
        If input does not exists it exits the process
        If output does not exists it tries to create it or exit with error
        """
        if not os.path.isdir(self.input_path) or not os.path.exists(self.input_path):
            self.log.error('Input directory "%s" does not exist or cannot be accessed' % self.input_path)
            raise Exception()

        if self.videos_output_path is not None and not os.path.exists(self.videos_output_path):
            self.log.info('Output directory for videos "%s" does not exist, creating now' % self.videos_output_path)
            try:
                os.makedirs(self.videos_output_path)
            except Exception as ex:
                self.log.error('Cannot create output directory for videos files. No write access!')
                raise ex

        if self.images_output_path is not None and not os.path.exists(self.images_output_path):
            self.log.info('Output directory for images "%s" does not exist, creating now' % self.images_output_path)
            try:
                os.makedirs(self.images_output_path)
            except Exception as ex:
                self.log.error('Cannot create output directory for images files. No write access!')
                raise ex

        if self.unknown_output_path is not None and not os.path.exists(self.unknown_output_path):
            self.log.info(
                'Output directory for unknown files "%s" does not exist, creating now' % self.unknown_output_path)
            try:
                os.makedirs(self.unknown_output_path)
            except Exception as ex:
                self.log.error('Cannot create output directory for unknown files. No write access!')
                raise ex

    def walk_directory(self):
        """
        Walk input directory recursively and call process_file for each file except the ignored ones
        """
        for root, dirs, files in os.walk(self.input_path):
            if os.path.basename(root) in ignored_folders:
                self.log.info("skip folder: '%s' " % root)
                continue

            files.sort()
            for filename in files:
                if filename in ignored_files:
                    self.log.info("skip file: '%s' " % filename)
                    continue

                file_path = os.path.join(root, filename)
                self.process_file(file_path)

            if self.move and len(os.listdir(root)) == 0:
                # remove all empty directories in PATH
                self.log.info('Deleting empty dirs in path: {}'.format(root))
                os.removedirs(root)

    def process_file(self, file_path: str):
        """
        Process the file using the selected strategy
        If file is .xmp skip it so process_xmp method can handle it
        """
        if str.endswith(file_path, '.xmp'):
            return None
        log_line = file_path

        phockup_file = SourceFile(
            output_file_name_format=self.output_file_name_format,
            dir_format=self.dir_format,
            date_regex=self.date_regex,
            images_output_path=self.images_output_path,
            videos_output_path=self.videos_output_path,
            unknown_output_path=self.unknown_output_path,
            file_path=file_path
        )
        if phockup_file.type == SourceFileType.UNKNOWN:
            self.counter_unknown_files += 1
        elif phockup_file.type == SourceFileType.VIDEO:
            self.counter_video_files += 1
        elif phockup_file.type == SourceFileType.IMAGE:
            self.counter_image_files += 1
        self.counter_all_files += 1

        if phockup_file.skipped:
            self.log.info(log_line + " => skipped, the output dir for %s is not defined" % phockup_file.type.name)
            return

        if not os.path.isdir(phockup_file.output_path):
            os.makedirs(phockup_file.output_path)
        self.counter_processed_files += 1

        suffix = 0
        base_target_file_path = phockup_file.target_file_path()
        target_file_path = base_target_file_path
        while True:
            if os.path.isfile(target_file_path):
                if os.path.getsize(file_path) == os.path.getsize(target_file_path) \
                        and filecmp.cmp(file_path, target_file_path):
                    # if self.checksum(file) == self.checksum(target_file):
                    self.counter_duplicates += 1
                    if self.move:
                        os.remove(file_path)
                        self.log.info(log_line + " => remove, duplicated file('%s')" % target_file_path)
                    else:
                        self.log.info(log_line + " => skipped, duplicated file ('%s')" % target_file_path)
                    break
            else:
                if self.move:
                    try:
                        shutil.move(file_path, target_file_path)
                    except FileNotFoundError:
                        self.log.info(log_line + ' => skipped, no such file or directory')
                        break
                elif self.link:
                    os.link(file_path, target_file_path)
                else:
                    try:
                        shutil.copy2(file_path, target_file_path)
                    except FileNotFoundError:
                        self.log.info(log_line + ' => skipped, no such file or directory')
                        break

                self.log.info(log_line + (' => %s' % target_file_path))
                self.process_xmp(file_path, phockup_file.target_file_name(), suffix, phockup_file.output_path)
                break

            suffix += 1
            target_split = os.path.splitext(base_target_file_path)
            target_file_path = "%s-%03d%s" % (target_split[0], suffix, target_split[1])

    def process_xmp(self, file, file_name, suffix, output):
        """
        Process xmp files. These are meta data for RAW images
        """
        xmp_original_with_ext = file + '.xmp'
        xmp_original_without_ext = os.path.splitext(file)[0] + '.xmp'

        suffix = '-%s' % suffix if suffix > 1 else ''

        if os.path.isfile(xmp_original_with_ext):
            xmp_original = xmp_original_with_ext
            xmp_target = '%s%s.xmp' % (file_name, suffix)
        elif os.path.isfile(xmp_original_without_ext):
            xmp_original = xmp_original_without_ext
            xmp_target = '%s%s.xmp' % (os.path.splitext(file_name)[0], suffix)
        else:
            xmp_original = None
            xmp_target = None

        if xmp_original:
            xmp_path = os.path.sep.join([output, xmp_target])
            self.log.info('%s => %s' % (xmp_original, xmp_path))

            if self.move:
                shutil.move(xmp_original, xmp_path)
            elif self.link:
                os.link(xmp_original, xmp_path)
            else:
                shutil.copy2(xmp_original, xmp_path)
