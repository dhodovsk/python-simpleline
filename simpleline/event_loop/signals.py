# Set of default signals used inside of widgets.
#
# Copyright (C) 2017  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Author(s): Jiri Konecny <jkonecny@redhat.com>
#

from simpleline.event_loop import AbstractSignal
from sys import exc_info


class ExceptionSignal(AbstractSignal):
    """Emit this signal when exception raised.

    This class must be created inside of catch handler or `exception_info` must be specified in creation process.
    """

    def __init__(self, source, exception_info=None):
        """Create exception signal with higher priority (-20) than other signals.

        :param source: source of this signal
        :type source: class which emits this signal

        :param exception_info: if specified raise your exception, otherwise create exception here;
                               to create exception here it needs to be created inside of catch handler
        :type exception_info: output of `sys.exc_info()` method
        """
        self.source = source
        self.priority = -20
        if exception_info:
            self.exception_info = exception_info
        else:
            self.exception_info = exc_info()


class InputReadySignal(AbstractSignal):
    """Input from user is ready for processing."""

    def __init__(self, source):
        self.source = source


class RenderScreenSignal(AbstractSignal):
    """Render UIScreen to terminal."""
    pass
