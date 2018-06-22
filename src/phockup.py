#!/usr/bin/env python3
import filecmp
import hashlib
import os
import re
import shutil
import sys
import logging

from src.date import Date
from src.exif import Exif

ignored_files = (".DS_Store", "Thumbs.db")


class Phockup():
    def __init__(self, input_path, **args):
        self.log = self.setup_logger()
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
            self.log.info("All files are processed.")
            self.log.handlers = []
        except Exception as ex:
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
            handler = logging.FileHandler('log.txt', mode='w')
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
            files.sort()
            for filename in files:
                if filename in ignored_files:
                    continue

                file = os.path.join(root, filename)
                self.process_file(file)

            if self.move and len(os.listdir(root)) == 0:
                # remove all empty directories in PATH
                self.log.info('Deleting empty dirs in path: {}'.format(root))
                os.removedirs(root)

    @staticmethod
    def checksum(file):
        """
        Calculate checksum for a file.
        Used to match if duplicated file name is actually a duplicated file
        """

        block_size = 65536
        sha256 = hashlib.sha256()
        with open(file, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()

    @staticmethod
    def is_image(mime_type):
        """
        Use mimetype to determine if the file is an image
        """
        pattern = re.compile('^(image/.+|application/vnd.adobe.photoshop)$')
        if pattern.match(mime_type):
            return True
        return False

    @staticmethod
    def is_video(mime_type):
        """
        Use mimetype to determine if the file is an video
        """
        pattern = re.compile('^(video/.+)$')
        if pattern.match(mime_type):
            return True
        return False

    def get_output_dir(self, date=None, output_path=None, unknown_output_path=None):
        """
        Generate output directory path based on the extracted date and formatted using dir_format
        If date is missing from the exifdata the file is going to "unknown" directory
        """
        if output_path is None:
            self.log.error("The output file is not defined")
            raise Exception()

        if date is None:
            if unknown_output_path is None:
                return None
            path = [unknown_output_path]
        else:
            try:
                path = [output_path, date['date'].date().strftime(self.dir_format)]
            except:
                if unknown_output_path is None:
                    return None
                path = output_path

        full_path = os.path.sep.join(path)

        if not os.path.isdir(full_path):
            os.makedirs(full_path)

        return full_path

    def get_file_name(self, file, date):
        """
        Generate file name based on exif data unless it is missing. Then use original file name
        """
        try:
            filename = date['date'].strftime(self.output_file_name_format)
            if date['subseconds']:
                filename += date['subseconds']
            return filename + os.path.splitext(file)[1]
        except:
            return os.path.basename(file)

    def is_file_must_be_processed(self, exif_data):
        is_known_type = False
        if exif_data \
                and 'MIMEType' in exif_data \
                and self.is_video(exif_data['MIMEType']):
            is_known_type = True
            if self.videos_output_path is None:
                self.log.info(' => skipped, output path for video file type is not defined')
                return False

        if exif_data \
                and 'MIMEType' in exif_data \
                and self.is_image(exif_data['MIMEType']):
            is_known_type = True
            if self.images_output_path is None:
                self.log.info(' => skipped, output path for image file type is not defined')
                return False

        if not is_known_type:
            if self.unknown_output_path is None:
                self.log.info(' => skipped, output path for unknown file type is not defined')
                return False

        return True

    def process_file(self, file):
        """
        Process the file using the selected strategy
        If file is .xmp skip it so process_xmp method can handle it
        """
        if str.endswith(file, '.xmp'):
            return None
        log_line = file

        exif_data = Exif(file).data()

        if not self.is_file_must_be_processed(exif_data):
            return

        output, target_file_name, target_file_path = self.get_file_name_and_path(file, exif_data)

        suffix = 1
        target_file = target_file_path

        while True:
            if os.path.isfile(target_file):
                if filecmp.cmp(file, target_file):
                    # if self.checksum(file) == self.checksum(target_file):
                    if self.move:
                        os.remove(file)
                        self.log.info(log_line + ' => remove, duplicated file')
                    else:
                        self.log.info(log_line + ' => skipped, duplicated file')
                    break
            else:
                if self.move:
                    try:
                        shutil.move(file, target_file)
                    except FileNotFoundError:
                        self.log.info(log_line + ' => skipped, no such file or directory')
                        break
                elif self.link:
                    os.link(file, target_file)
                else:
                    try:
                        shutil.copy2(file, target_file)
                    except FileNotFoundError:
                        self.log.info(log_line + ' => skipped, no such file or directory')
                        break

                self.log.info(log_line + (' => %s' % target_file))
                self.process_xmp(file, target_file_name, suffix, output)
                break

            suffix += 1
            target_split = os.path.splitext(target_file_path)
            target_file = "%s-%03d%s" % (target_split[0], suffix, target_split[1])

    def get_file_name_and_path(self, file, exif_data):
        """
        Returns target file name and path
        """
        date = None
        if exif_data \
                and 'MIMEType' in exif_data \
                and self.images_output_path is not None \
                and self.is_image(exif_data['MIMEType']):
            date = Date(file).from_exif(exif_data, self.date_regex)
            output = self.get_output_dir(date=date,
                                         output_path=self.images_output_path,
                                         unknown_output_path=self.unknown_output_path)
        elif exif_data \
                and 'MIMEType' in exif_data \
                and self.videos_output_path is not None \
                and self.is_video(exif_data['MIMEType']):
            date = Date(file).from_exif(exif_data, self.date_regex)
            output = self.get_output_dir(date=date,
                                         output_path=self.videos_output_path,
                                         unknown_output_path=self.unknown_output_path)
        else:
            output = self.get_output_dir(output_path=self.unknown_output_path,
                                         unknown_output_path=self.unknown_output_path)

        target_file_name = self.get_file_name(file, date).lower() if date else os.path.basename(file)
        target_file_path = os.path.sep.join([output, target_file_name])

        return output, target_file_name, target_file_path

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
