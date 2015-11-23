# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2015 Daniel Schadt
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""pdf.js integration for qutebrowser."""

import os

from qutebrowser.browser import webelem
from qutebrowser.utils import utils


class PDFJSNotFound(Exception):

    """Raised when no pdf.js installation is found."""

    pass


def generate_pdfjs_page(url):
    """Return the html content of a page that displays url with pdfjs.

    Returns a string.

    Args:
        url: The url of the pdf as QUrl.
    """
    viewer = get_pdfjs_res('web/viewer.html').decode('utf-8')
    script = _generate_pdfjs_script(url)
    html_page = viewer.replace(
        '</body>', '</body><script>{}</script>'.format(script)
    )
    return html_page


def _generate_pdfjs_script(url):
    """Generate the script that shows the pdf with pdf.js.

    Args:
        url: The url of the pdf page as QUrl.
    """
    return (
        'PDFJS.getDocument("{url}").then(function(pdf) {{\n'
        '    PDFView.load(pdf);\n'
        '}});'
    ).format(url=webelem.javascript_escape(url.toString()))


def fix_urls(asset):
    """Take a html page and replace each relative URL wth an absolute.

    This is specialized for pdf.js files and not a general purpose function.

    Args:
        asset: js file or html page as string.
    """
    new_urls = {
        'viewer.css': 'qute://pdfjs/web/viewer.css',
        'compatibility.js': 'qute://pdfjs/web/compatibility.js',
        'locale/locale.properties':
            'qute://pdfjs/web/locale/locale.properties',
        'l10n.js': 'qute://pdfjs/web/l10n.js',
        '../build/pdf.js': 'qute://pdfjs/build/pdf.js',
        'debugger.js': 'qute://pdfjs/web/debugger.js',
        'viewer.js': 'qute://pdfjs/web/viewer.js',
        'compressed.tracemonkey-pldi-09.pdf': '',
        './images/': 'qute://pdfjs/web/images/',
        '../build/pdf.worker.js': 'qute://pdfjs/build/pdf.worker.js',
        '../web/cmaps/': 'qute://pdfjs/web/cmaps/',
    }
    for original, new in new_urls.items():
        asset = asset.replace(original, new)
    return asset


SYSTEM_PDFJS_PATHS = [
    '/usr/share/pdf.js/',  # Debian pdf.js-common
    '/usr/share/javascript/pdf/',  # Debian libjs-pdf
]


def get_pdfjs_res(path):
    """Get a pdf.js resource in binary format.

    Args:
        path: The path inside the pdfjs directory.
    """
    path = path.lstrip('/')
    content = None

    # First try a system wide installation
    # System installations might strip off the 'build/' or 'web/' prefixes.
    # qute expects them, so we need to adjust for it.
    names_to_try = [path, path[path.index('/')+1:]]
    for system_path in SYSTEM_PDFJS_PATHS:
        content = _read_from_system(system_path, names_to_try)
        if content is not None:
            break

    # Fallback to bundled pdf.js
    if content is None:
        res_path = '3rdparty/pdfjs/{}'.format(path)
        try:
            content = utils.read_file(res_path, binary=True)
        except FileNotFoundError:
            raise PDFJSNotFound

    try:
        # Might be script/html or might be binary
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        return content
    text_content = fix_urls(text_content)
    return text_content.encode('utf-8')


def _read_from_system(system_path, names):
    """Try to read a file with one of the given names in system_path.

    Each file in names is considered equal, the first file that is found
    is read and its binary content returned.

    Returns None if no file could be found

    Args:
        system_path: The folder where the file should be searched.
        names: List of possible file names.
    """
    for name in names:
        try:
            with open(os.path.join(system_path, name), 'rb') as f:
                return f.read()
        except OSError:
            continue
    return None
