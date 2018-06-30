import os
import re
from datetime import datetime
from src.date import Date
from src.exif import Exif
from src.source_file import SourceFile, SourceFileType

os.chdir(os.path.dirname(__file__))


def test_image_file_with_exif_date(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")
    file_path = os.path.join("input", "exif.jpg")
    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=None,
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.IMAGE
    assert source_file.target_file_name() == '2017-01-01_010101.jpg'
    assert source_file.target_file_path() == os.path.join(images_output_path, '2017', '01', '2017-01-01_010101.jpg')
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=None,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.IMAGE
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped


def test_video_file_with_exif_date(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")
    file_path = os.path.join("input", "exif.mp4")
    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=None,
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.VIDEO
    assert source_file.target_file_name() == '2017-01-01_010101.mp4'
    assert source_file.target_file_path() == os.path.join(videos_output_path, '2017', '01', '2017-01-01_010101.mp4')
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=None,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.VIDEO
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped


def test_image_file_without_exif_date_with_parsable_name(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")
    file_path = os.path.join("input", "date_20170101_010101.jpg")
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg"
    }
    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=re.compile(
            'invalid regexp'),
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=re.compile(
            'invalid regexp'),
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=re.compile(
            '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.IMAGE
    assert source_file.target_file_name() == '2017-01-01_010101.jpg'
    assert source_file.target_file_path() == os.path.join(images_output_path, '2017', '01', '2017-01-01_010101.jpg')
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=re.compile(
            '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=None,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.IMAGE
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped


def test_video_file_without_exif_date_with_parsable_name(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")
    file_path = os.path.join("input", "date_20170101_010101.jpg")
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "video/mp4"
    }
    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d %H:%M:%S",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d %H:%M:%S",
        date_regex=re.compile(
            'invalid regexp'),
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d %H:%M:%S",
        date_regex=re.compile(
            'invalid regexp'),
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=re.compile(
            '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.VIDEO
    assert source_file.target_file_name() == '2017-01-01_010101.jpg'
    assert source_file.target_file_path() == os.path.join(videos_output_path, '2017', '01', '2017-01-01_010101.jpg')
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=re.compile(
            '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=None,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.VIDEO
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped


def test_image_file_without_exif_date(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")
    file_path = os.path.join("input", "exif.jpg")
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg"
    }

    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.skipped
    assert source_file.target_file_path() is None


def test_video_file_without_exif_date(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")
    file_path = os.path.join("input", "exif.mp4")
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "video/mp4"
    }

    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.skipped
    assert source_file.target_file_path() is None


def test_existed_unknown_file_with_parsable_name(mocker):
    unknown_output_path = os.path.join("output", "unknown")
    images_output_path = os.path.join("output", "images")
    videos_output_path = os.path.join("output", "videos")

    file_path = os.path.join("input", "date_20170101_010101.jpg")
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
    }
    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=re.compile(
            '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        output_file_name_format="%Y-%m-%d_%H%M%S",
        date_regex=re.compile(
            '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
        dir_format="%Y" + os.sep + "%m",
        videos_output_path=videos_output_path,
        images_output_path=images_output_path,
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped


def test_existed_unknown_file(mocker):
    unknown_output_path = "output"
    file_path = os.path.join("input", "other.txt")
    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path="output",
        images_output_path="output",
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    """
     Output dir for unknown files is not defined
     target fileName and filePath is None
    """
    unknown_output_path = None
    source_file = SourceFile(
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped

    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path="output",
        images_output_path="output",
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped


def test_not_existed_file(mocker):
    """
      target file path for not existed file is unknown_output_path/fileName
    """

    """
     filePath is a fileName     
    """
    unknown_output_path = "output"
    file_path = "don_t_existed.file"
    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path="output",
        images_output_path="output",
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == file_path
    assert source_file.target_file_path() == os.path.join(unknown_output_path, file_path)
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == file_path
    assert source_file.target_file_path() == os.path.join(unknown_output_path, file_path)
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert  source_file.skipped
    """
     filePath is a path     
    """
    file_path = os.path.join("inputTest", "don_t_existed.file")
    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=None,
        images_output_path=None,
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    source_file = SourceFile(
        unknown_output_path=unknown_output_path,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() == os.path.basename(file_path)
    assert source_file.target_file_path() == os.path.join(unknown_output_path, os.path.basename(file_path))
    assert not source_file.skipped

    """
     Output dir for unknown files is not defined
     target fileName and filePath is None
    """
    source_file = SourceFile(
        output_file_name_format="'%Y-%m-%d %H:%M:%S'",
        date_regex=None,
        dir_format="%Y/%m",
        videos_output_path=None,
        images_output_path=None,
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
    assert source_file.skipped

    source_file = SourceFile(
        unknown_output_path=None,
        file_path=file_path
    )
    assert source_file.type == SourceFileType.UNKNOWN
    assert source_file.target_file_name() is None
    assert source_file.target_file_path() is None
