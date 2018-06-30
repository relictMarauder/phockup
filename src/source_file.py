import os
from enum import Enum
from sre_parse import Pattern

from src.date import Date
from src.exif import Exif
import re


class SourceFileType(Enum):
    VIDEO = 1
    IMAGE = 2
    UNKNOWN = 3


class SourceFile:
    def __init__(self,
                 file_path: str,
                 images_output_path: (str, None) = None,
                 videos_output_path: (str, None) = None,
                 unknown_output_path: (str, None) = None,
                 date_regex: (Pattern, None) = None,
                 output_file_name_format: str = '%Y%m%d-%H%M%S',
                 dir_format: str = os.path.sep.join(['%Y', '%m', '%d'])
                 ):
        self.type = SourceFileType.UNKNOWN
        self.exif_data: Exif = Exif(file_path).data()
        self.file_path: str = file_path
        self.date_regex = date_regex
        self.images_output_path = images_output_path
        self.videos_output_path = videos_output_path
        self.unknown_output_path = unknown_output_path
        self.dir_format = dir_format
        self.output_file_name_format = output_file_name_format
        self.date: Date = None
        self.output_path: str = None
        self.skipped: bool = True
        self._target_file_name = None
        self._target_file_path = None
        self.__fill_phockup_file()

    def __fill_phockup_file(self):
        """
        Returns target file name and path
        """
        if SourceFile.__is_image(self.exif_data):
            self.date = Date(self.file_path).from_exif(self.exif_data, self.date_regex)
            output_dir = SourceFile.__get_output_dir(self.date,
                                                     self.dir_format)
            if output_dir:
                self.type = SourceFileType.IMAGE
                self.skipped = self.images_output_path is None
                self.output_path = None if self.skipped else os.path.join(self.images_output_path, output_dir)

        elif SourceFile.__is_video(self.exif_data):
            self.date = Date(self.file_path).from_exif(self.exif_data, self.date_regex)
            output_dir = SourceFile.__get_output_dir(self.date,
                                                     self.dir_format)
            if output_dir:
                self.type = SourceFileType.VIDEO
                self.skipped = self.videos_output_path is None
                self.output_path = None if self.skipped else os.path.join(self.videos_output_path, output_dir)

        if self.type == SourceFileType.UNKNOWN:
            self.skipped = self.unknown_output_path is None
            self.output_path = self.unknown_output_path

    @staticmethod
    def __is_image(exif_data: Exif) -> bool:
        """
        Use mimetype to determine if the file is an image
        """
        if exif_data and 'MIMEType' in exif_data:
            pattern = re.compile('^(image/.+|application/vnd.adobe.photoshop)$')
            if pattern.match(exif_data['MIMEType']):
                return True
        return False

    @staticmethod
    def __is_video(exif_data: Exif) -> bool:
        """
        Use mimetype to determine if the file is an image
        """
        if exif_data and 'MIMEType' in exif_data:
            pattern = re.compile('^(video/.+)$')
            if pattern.match(exif_data['MIMEType']):
                return True
        return False

    @staticmethod
    def __get_output_dir(date: Date, dir_format: str) -> (str, None):
        """
        Generate output directory path based on the extracted date and formatted using dir_format
        If date is missing from the exifdata the file is going to "unknown" directory
        """

        if date is None:
            return None
        else:
            try:
                dir_formatted = date['date'].date().strftime(dir_format)
            except:
                return None

            return dir_formatted

    def __get_file_name(self) -> str:
        """
        Generate file name based on exif data unless it is missing. Then use original file name
        """
        if self.date:
            try:
                filename = self.date['date'].strftime(self.output_file_name_format)
                if self.date['subseconds']:
                    filename += self.date['subseconds']
                return filename + os.path.splitext(self.file_path)[1]
            except:
                pass
        return os.path.basename(self.file_path)

    def target_file_name(self) -> (str, None):
        if self.skipped:
            return None
        if self._target_file_name is None:
            self._target_file_name = self.__get_file_name().lower()
        return self._target_file_name

    def target_file_path(self) -> (str, None):
        if self.skipped:
            return None
        if self._target_file_path is None:
            self._target_file_path = os.path.sep.join([self.output_path, self.target_file_name()])
        return self._target_file_path
