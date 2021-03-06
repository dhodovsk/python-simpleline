# Helper functions for the test classes.
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

from simpleline import App
from simpleline.global_configuration import DEFAULT_WIDTH


class UtilityMixin(object):

    def calculate_separator(self, width=DEFAULT_WIDTH):
        separator = "\n".join(2 * [width * "="])
        separator += "\n"  # print adds another newline
        return separator

    def create_output_with_separators(self, screens_text):
        msg = ""
        for screen_txt in screens_text:
            msg += self.calculate_separator()
            msg += screen_txt + "\n\n"

        return msg

    def schedule_screen_and_run(self, screen):
        App.initialize()
        App.get_scheduler().schedule_screen(screen)
        App.run()
