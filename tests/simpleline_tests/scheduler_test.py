# Screen scheduler test classes.
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

import unittest
from unittest import mock

from simpleline.event_loop.main_loop import MainLoop
from simpleline.render.screen import UIScreen
from simpleline.render.screen_scheduler import ScreenScheduler
from simpleline.render.screen_stack import ScreenStack, ScreenStackEmptyException


class Scheduler_TestCase(unittest.TestCase):

    def setUp(self):
        self.stack = None
        self.scheduler = None

    def create_scheduler_with_stack(self):
        self.stack = ScreenStack()
        self.scheduler = ScreenScheduler(event_loop=mock.MagicMock(), scheduler_stack=self.stack)

    def pop_last_item(self, remove=True):
        return self.stack.pop(remove)

    def test_create_scheduler(self):
        scheduler = ScreenScheduler(MainLoop())
        self.assertTrue(type(scheduler._screen_stack) is ScreenStack)

    def test_scheduler_quit_screen(self):
        def test_callback():
            pass
        scheduler = ScreenScheduler(MainLoop())
        self.assertEqual(scheduler.quit_screen, None)
        scheduler.quit_screen = test_callback
        self.assertEqual(scheduler.quit_screen, test_callback)

    def test_nothing_to_render(self):
        self.create_scheduler_with_stack()

        self.assertTrue(self.scheduler.nothing_to_render)
        self.assertTrue(self.stack.empty())

        self.scheduler.schedule_screen(UIScreen())
        self.assertFalse(self.scheduler.nothing_to_render)
        self.assertFalse(self.stack.empty())

    def test_schedule_screen(self):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        self.scheduler.schedule_screen(screen)
        test_screen = self.pop_last_item(False)
        self.assertEqual(test_screen.ui_screen, screen)
        self.assertEqual(test_screen.args, None)  # empty field - no arguments
        self.assertFalse(test_screen.execute_new_loop)

        # Schedule another screen, new one will be added to the bottom of the stack
        new_screen = UIScreen()
        self.scheduler.schedule_screen(new_screen)
        # Here should still be the old screen
        self.assertEqual(self.pop_last_item().ui_screen, screen)
        # After removing the first we would find the second screen
        self.assertEqual(self.pop_last_item().ui_screen, new_screen)

    def test_replace_screen_with_empty_stack(self):
        self.create_scheduler_with_stack()

        with self.assertRaises(ScreenStackEmptyException):
            self.scheduler.replace_screen(UIScreen())

    def test_replace_screen(self):
        self.create_scheduler_with_stack()

        old_screen = UIScreen()
        screen = UIScreen()
        self.scheduler.schedule_screen(old_screen)
        self.scheduler.replace_screen(screen)
        self.assertEqual(self.pop_last_item(False).ui_screen, screen)

        new_screen = UIScreen()
        self.scheduler.replace_screen(new_screen)
        self.assertEqual(self.pop_last_item().ui_screen, new_screen)
        # The old_screen was replaced so the stack is empty now
        self.assertTrue(self.stack.empty())

    def test_replace_screen_with_args(self):
        self.create_scheduler_with_stack()

        old_screen = UIScreen()
        screen = UIScreen()
        self.scheduler.schedule_screen(old_screen)
        self.scheduler.replace_screen(screen, "test")
        test_screen = self.pop_last_item()
        self.assertEqual(test_screen.ui_screen, screen)
        self.assertEqual(test_screen.args, "test")
        # The old_screen was replaced so the stack is empty now
        self.assertTrue(self.stack.empty())

    def test_switch_screen_with_empty_stack(self):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        self.scheduler.push_screen(screen)
        self.assertEqual(self.pop_last_item().ui_screen, screen)

    def test_switch_screen(self):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        new_screen = UIScreen()

        self.scheduler.schedule_screen(screen)
        self.scheduler.push_screen(new_screen)

        test_screen = self.pop_last_item()
        self.assertEqual(test_screen.ui_screen, new_screen)
        self.assertEqual(test_screen.args, None)
        self.assertEqual(test_screen.execute_new_loop, False)

        # We popped the new_screen so the old screen should stay here
        self.assertEqual(self.pop_last_item().ui_screen, screen)
        self.assertTrue(self.stack.empty())

    def test_switch_screen_with_args(self):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        self.scheduler.push_screen(screen, args="test")
        self.assertEqual(self.pop_last_item(False).ui_screen, screen)
        self.assertEqual(self.pop_last_item().args, "test")

    @mock.patch('simpleline.render.screen_scheduler.ScreenScheduler._draw_screen')
    def test_switch_screen_modal_empty_stack(self, _):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        self.scheduler.push_screen_modal(screen)
        self.assertEqual(self.pop_last_item().ui_screen, screen)

    @mock.patch('simpleline.render.screen_scheduler.ScreenScheduler._draw_screen')
    def test_switch_screen_modal(self, _):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        new_screen = UIScreen()
        self.scheduler.schedule_screen(screen)
        self.scheduler.push_screen_modal(new_screen)

        test_screen = self.pop_last_item()
        self.assertEqual(test_screen.ui_screen, new_screen)
        self.assertEqual(test_screen.args, None)
        self.assertEqual(test_screen.execute_new_loop, True)

    @mock.patch('simpleline.render.screen_scheduler.ScreenScheduler._draw_screen')
    def test_switch_screen_modal_with_args(self, _):
        self.create_scheduler_with_stack()

        screen = UIScreen()
        self.scheduler.push_screen_modal(screen, args="test")
        self.assertEqual(self.pop_last_item(False).ui_screen, screen)
