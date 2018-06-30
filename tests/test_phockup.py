import re
import shutil
import sys
import os
from datetime import datetime
from unittest.mock import call

from src.dependency import check_dependencies
from src.exif import Exif
from src.phockup import Phockup

os.chdir(os.path.dirname(__file__))


def test_check_dependencies(mocker):
    mocker.patch('shutil.which', return_value='exiftool')
    mocker.patch('sys.exit')

    check_dependencies()
    assert not sys.exit.called


def test_check_dependencies_missing(mocker):
    mocker.patch('shutil.which', return_value=None)
    mocker.patch('sys.exit')

    check_dependencies()
    sys.exit.assert_called_once_with(1)


def test_exit_if_missing_input_directory(mocker):
    mocker.patch('os.makedirs')
    mocker.patch('sys.exit')
    Phockup('in',
            images_output_path='out',
            videos_output_path='out',
            unknown_output_path='out/unknown')
    sys.exit.assert_called_once_with(1)


def test_removing_trailing_slash_for_input_output(mocker):
    mocker.patch('os.makedirs')
    mocker.patch('sys.exit')
    phockup = Phockup('in' + os.path.sep,
                      images_output_path='out' + os.path.sep,
                      videos_output_path='out' + os.path.sep,
                      unknown_output_path='out/unknown' + os.path.sep)
    assert phockup.input_path == 'in'
    assert phockup.images_output_path == 'out'
    assert phockup.videos_output_path == 'out'
    assert phockup.unknown_output_path == 'out/unknown'


def test_error_for_missing_input_dir(mocker, capsys):
    mocker.patch('sys.exit')
    if os.path.isfile('test-output.log'):
        os.remove('test-output.log')
    Phockup('in',
            images_output_path='out',
            videos_output_path='out',
            unknown_output_path='out/unknown',
            log_file_name='test-output.log')
    sys.exit.assert_called_once_with(1)
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('Input directory "in" does not exist') > 0 for item in output_log)


def test_error_for_no_write_access_when_creating_output_dir(mocker, capsys):
    mocker.patch.object(Phockup, 'walk_directory')
    mocker.patch('os.makedirs', side_effect=Exception("No write access"))
    mocker.patch('sys.exit')
    if os.path.isfile('test-output.log'):
        os.remove('test-output.log')
    Phockup('input', videos_output_path='/root/phockup', log_file_name='test-output.log')
    sys.exit.assert_called_once_with(1)
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('No write access') > 0 for item in output_log)
    Phockup('input', images_output_path='/root/phockup', log_file_name='test-output.log')
    sys.exit.assert_has_calls([call(1), call(1)])
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('No write access') > 0 for item in output_log)
    Phockup('input', unknown_output_path='/root/phockup', log_file_name='test-output.log')
    sys.exit.assert_has_calls([call(1), call(1), call(1)])
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('No write access') > 0 for item in output_log)


def test_walking_directory():
    shutil.rmtree('output', ignore_errors=True)
    Phockup('input',
            date_regex=re.compile(
                '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
            images_output_path=os.path.join('output', 'images'),
            videos_output_path=os.path.join('output', 'videos'),
            unknown_output_path=os.path.join('output', 'unknown'))
    dir1 = 'output/images/2017/01/01'
    dir12 = 'output/images/2017/10/06'
    dir2 = 'output/videos/2017/01/01'
    dir3 = 'output/unknown'
    assert os.path.isdir(dir1)
    assert os.path.isdir(dir12)
    assert os.path.isdir(dir2)
    assert os.path.isdir(dir3)
    assert len([name for name in os.listdir(dir1) if os.path.isfile(os.path.join(dir1, name))]) == 2
    assert len([name for name in os.listdir(dir12) if os.path.isfile(os.path.join(dir12, name))]) == 1
    assert len([name for name in os.listdir(dir2) if os.path.isfile(os.path.join(dir2, name))]) == 1
    assert len([name for name in os.listdir(dir3) if os.path.isfile(os.path.join(dir3, name))]) == 1
    shutil.rmtree('output', ignore_errors=True)


def test_walking_directory_without_images():
    shutil.rmtree('output', ignore_errors=True)
    Phockup('input',
            date_regex=re.compile(
                '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
            images_output_path=None,
            videos_output_path=os.path.join('output', 'videos'),
            unknown_output_path=os.path.join('output', 'unknown'))
    dir1 = 'output/images/2017/01/01'
    dir12 = 'output/images/2017/10/06'
    dir2 = 'output/videos/2017/01/01'
    dir3 = 'output/unknown'
    assert not os.path.isdir(dir1)
    assert not os.path.isdir(dir12)
    assert os.path.isdir(dir2)
    assert os.path.isdir(dir3)
    assert len([name for name in os.listdir(dir2) if os.path.isfile(os.path.join(dir2, name))]) == 1
    assert len([name for name in os.listdir(dir3) if os.path.isfile(os.path.join(dir3, name))]) == 1
    shutil.rmtree('output', ignore_errors=True)


def test_walking_directory_without_videos():
    shutil.rmtree('output', ignore_errors=True)
    Phockup('input',
            date_regex=re.compile(
                '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
            images_output_path=os.path.join('output', 'images'),
            videos_output_path=None,
            unknown_output_path=os.path.join('output', 'unknown'))
    dir1 = 'output/images/2017/01/01'
    dir12 = 'output/images/2017/10/06'
    dir2 = 'output/videos/2017/01/01'
    dir3 = 'output/unknown'
    assert os.path.isdir(dir1)
    assert os.path.isdir(dir12)
    assert not os.path.isdir(dir2)
    assert os.path.isdir(dir3)
    assert len([name for name in os.listdir(dir1) if os.path.isfile(os.path.join(dir1, name))]) == 2
    assert len([name for name in os.listdir(dir12) if os.path.isfile(os.path.join(dir12, name))]) == 1
    assert len([name for name in os.listdir(dir3) if os.path.isfile(os.path.join(dir3, name))]) == 1
    shutil.rmtree('output', ignore_errors=True)


def test_walking_directory_without_unknown():
    shutil.rmtree('output', ignore_errors=True)
    Phockup('input',
            date_regex=re.compile(
                '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
            images_output_path=os.path.join('output', 'images'),
            videos_output_path=os.path.join('output', 'videos'),
            unknown_output_path=None)
    dir1 = 'output/images/2017/01/01'
    dir12 = 'output/images/2017/10/06'
    dir2 = 'output/videos/2017/01/01'
    dir3 = 'output/unknown'
    assert os.path.isdir(dir1)
    assert os.path.isdir(dir12)
    assert os.path.isdir(dir2)
    assert not os.path.isdir(dir3)
    assert len([name for name in os.listdir(dir1) if os.path.isfile(os.path.join(dir1, name))]) == 2
    assert len([name for name in os.listdir(dir12) if os.path.isfile(os.path.join(dir12, name))]) == 1
    assert len([name for name in os.listdir(dir2) if os.path.isfile(os.path.join(dir2, name))]) == 1
    shutil.rmtree('output', ignore_errors=True)


def test_process_file_with_filename_date(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg"
    }
    Phockup('input',
            date_regex=re.compile(
                '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown').process_file("input/date_20170101_010101.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    shutil.rmtree('output', ignore_errors=True)


def test_process_link_to_file_with_filename_date(mocker):
    if os.name != 'nt':
        shutil.rmtree('output', ignore_errors=True)
        mocker.patch.object(Phockup, 'check_directories')
        mocker.patch.object(Phockup, 'walk_directory')
        Phockup('input',
                images_output_path='output',
                videos_output_path='output',
                unknown_output_path='output/unknown').process_file("input/link_to_date_20170101_010101.jpg")
        assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
        shutil.rmtree('output', ignore_errors=True)


def test_process_broken_link(mocker, capsys):
    shutil.rmtree('output', ignore_errors=True)
    if os.path.isfile('test-output.log'):
        os.remove('test-output.log')
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    phockup = Phockup('input',
                      images_output_path='output',
                      videos_output_path='output',
                      unknown_output_path='output/unknown')

    phockup.log = phockup.setup_logger('test-output.log')
    phockup.process_file("input/not_a_file.jpg")
    phockup.log.handlers = []
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('skipped, no such file or directory') > 0 for item in output_log)
    shutil.rmtree('output', ignore_errors=True)


def test_process_broken_link_move(mocker, capsys):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    phockup = Phockup('input',
                      images_output_path='output',
                      videos_output_path='output',
                      unknown_output_path='output/unknown',
                      move=True)
    if os.path.isfile('test-output.log'):
        os.remove('test-output.log')
    phockup.log = phockup.setup_logger('test-output.log')
    phockup.process_file("input/not_a_file.jpg")
    phockup.log.handlers = []
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('skipped, no such file or directory') > 0 for item in output_log)
    shutil.rmtree('output', ignore_errors=True)


def test_process_image_exif_date(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    Phockup('input',
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown').process_file("input/exif.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    shutil.rmtree('output', ignore_errors=True)


def test_process_image_xmp(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    Phockup('input',
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown').process_file("input/xmp.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg.xmp")
    shutil.rmtree('output', ignore_errors=True)


def test_process_image_xmp_noext(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    Phockup('input',
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown').process_file("input/xmp_noext.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.xmp")
    shutil.rmtree('output', ignore_errors=True)


def test_process_image_unknown(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg"
    }
    Phockup('input',
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown').process_file("input/unknown.jpg")
    assert os.path.isfile("output/unknown/unknown.jpg")
    shutil.rmtree('output', ignore_errors=True)


def test_process_other(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    Phockup('input',
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown').process_file("input/other.txt")
    assert os.path.isfile("output/unknown/other.txt")
    shutil.rmtree('output', ignore_errors=True)


def test_process_move(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg"
    }
    phockup = Phockup('input',
                      date_regex=re.compile(
                          '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
                      images_output_path='output',
                      videos_output_path='output',
                      unknown_output_path='output/unknown'
                      , move=True)
    open("input/tmp_20170101_010101.jpg", "w").close()
    open("input/tmp_20170101_010101.xmp", "w").close()
    phockup.process_file("input/tmp_20170101_010101.jpg")
    phockup.process_file("input/tmp_20170101_010101.xmp")
    assert not os.path.isfile("input/tmp_20170101_010101.jpg")
    assert not os.path.isfile("input/tmp_20170101_010101.xmp")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.xmp")
    shutil.rmtree('output', ignore_errors=True)


def test_process_link(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg"
    }
    phockup = Phockup('input',
                      date_regex=re.compile(
                          '.*[_-](?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})'),
                      images_output_path='output',
                      videos_output_path='output',
                      unknown_output_path='output/unknown'
                      , link=True)
    open("input/tmp_20170101_010101.jpg", "w").close()
    open("input/tmp_20170101_010101.xmp", "w").close()
    phockup.process_file("input/tmp_20170101_010101.jpg")
    phockup.process_file("input/tmp_20170101_010101.xmp")
    assert os.path.isfile("input/tmp_20170101_010101.jpg")
    assert os.path.isfile("input/tmp_20170101_010101.xmp")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.xmp")
    shutil.rmtree('output', ignore_errors=True)
    os.remove("input/tmp_20170101_010101.jpg")
    os.remove("input/tmp_20170101_010101.xmp")


def test_process_exists_same(mocker, capsys):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    phockup = Phockup(
        'input',
        images_output_path='output',
        videos_output_path='output',
        unknown_output_path='output/unknown')
    phockup.log = phockup.setup_logger('test-output.log')
    phockup.process_file("input/exif.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101.jpg")
    phockup.process_file("input/exif.jpg")
    phockup.log.handlers = []
    output_log = [line.rstrip('\n') for line in open('test-output.log')]
    os.remove('test-output.log')
    assert any(item.find('skipped, duplicated file') > 1 for item in output_log)
    shutil.rmtree('output', ignore_errors=True)


def test_process_same_date_different_files_rename(mocker):
    shutil.rmtree('output', ignore_errors=True)
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    phockup = Phockup('input',
                      images_output_path='output',
                      videos_output_path='output',
                      unknown_output_path='output/unknown')
    phockup.process_file("input/exif.jpg")
    mocker.patch.object(Exif, 'data')
    Exif.data.return_value = {
        "MIMEType": "image/jpeg",
        "CreateDate": "2017:01:01 01:01:01"
    }
    phockup.process_file("input/date_20170101_010101.jpg")
    assert os.path.isfile("output/2017/01/01/20170101-010101-002.jpg")
    shutil.rmtree('output', ignore_errors=True)


def test_process_skip_xmp(mocker):
    # Assume no errors == skip XMP file
    mocker.patch.object(Phockup, 'check_directories')
    mocker.patch.object(Phockup, 'walk_directory')
    phockup = Phockup('input',
                      images_output_path='output',
                      videos_output_path='output',
                      unknown_output_path='output/unknown')
    phockup.process_file("skip.xmp")


def test_process_delete_empty_input_folder():
    shutil.rmtree('output', ignore_errors=True)
    shutil.rmtree('input_ignored', ignore_errors=True)
    os.mkdir('input_ignored')
    os.mkdir('input_ignored/empty_dir')
    Phockup('input_ignored',
            move=True,
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown')
    assert not os.path.exists("input_ignored/empty_dir")
    shutil.rmtree('output', ignore_errors=True)
    shutil.rmtree('input_ignored', ignore_errors=True)


def test_process_skip_ignored_file():
    shutil.rmtree('output', ignore_errors=True)
    shutil.rmtree('input_ignored', ignore_errors=True)
    os.mkdir('input_ignored')
    open("input_ignored/.DS_Store", "w").close()
    Phockup('input_ignored',
            images_output_path='output',
            videos_output_path='output',
            unknown_output_path='output/unknown')
    assert not os.path.isfile("output/unknown/.DS_Store")
    shutil.rmtree('output', ignore_errors=True)
    shutil.rmtree('input_ignored', ignore_errors=True)
