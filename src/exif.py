import json
import shlex
from subprocess import check_output, CalledProcessError


class Exif(object):
    def __init__(self, file):
        self.file = file

    def write_created_date(self, date):
        try:
            data = check_output(
                'exiftool -d "%%Y-%%m-%%d%%H:%%M:%%S" -CreateDate="%s" -overwrite_original "%s"' % (
                    date.strftime('%Y-%m-%d%H:%M:%S'), self.file),
                shell=True).decode('UTF-8')

        except (CalledProcessError, UnicodeDecodeError):
            return False

        return True

    def data(self):
        try:
            data = check_output('exiftool -time:all -mimetype -j "%s"' % self.file, shell=True).decode('UTF-8')
            exif = json.loads(data)[0]
        except (CalledProcessError, UnicodeDecodeError) as error:
            return None

        return exif
