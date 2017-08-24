# Glib event queue used by Simpleline application.
#
# This class is thread safe.
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

from collections import namedtuple

from simpleline.event_loop import AbstractEventLoop, ExitMainLoop
from simpleline.event_loop.signals import ExceptionSignal

import gi
gi.require_version("GLib", "2.0")

from gi.repository import GLib
from simpleline.logging import get_simpleline_logger

log = get_simpleline_logger()

CallbackArgs = namedtuple("CallbackArgs", ["signal", "source", "handlers"])


__all__ = ["GLibEventLoop"]


class GLibEventLoop(AbstractEventLoop):

    def __init__(self):
        super().__init__()
        # Create first loop
        loop = GLib.MainLoop()
        self._event_loops = [EventLoopData(loop)]
        log.debug("GLib event loop is used!")

    @property
    def active_main_loop(self):
        """Return GLib mainloop object."""
        return self._event_loops[-1].loop

    def register_signal_source(self, signal_source):
        """Register source of signal for actual event queue.

        :param signal_source: Source for future signals.
        :type signal_source: `simpleline.render.ui_screen.UIScreen`
        """
        super().register_signal_source(signal_source)
        loop_data = self._event_loops[-1]
        loop_data.sources.add(signal_source)

    def enqueue_signal(self, signal):
        """Enqueue new event for processing.

        :param signal: signal which you want to add to the event queue for processing
        :type signal: instance based on AbstractEvent class
        """
        super().enqueue_signal(signal)
        loop_data = self._find_loop_data_for_source(signal.source)
        self._register_handlers_to_loop(loop_data.loop, signal)

    def _find_loop_data_for_source(self, source):
        """Find event loop belonging to this signal source."""
        for loop_data in reversed(self._event_loops):
            if source in loop_data.sources:
                return loop_data

        return self._event_loops[-1]

    def _register_handlers_to_loop(self, event_loop, signal):
        """Register handlers to the event loop."""
        context = event_loop.get_context()
        handlers = []

        if type(signal) in self._handlers:
            handlers = self._handlers[type(signal)]
        elif type(signal) is ExceptionSignal:
            handlers = [self._raise_exception]

        # GLib event source which contains handler callback
        # Every source can hold only one callback
        source = GLib.idle_source_new()
        source.set_priority(signal.priority)
        data = CallbackArgs(signal, source, handlers)

        source.set_callback(self._run_handlers, data)
        # attach source to the event loop
        source.attach(context)

    def _run_handlers(self, data):
        """Run handlers attached to this signal and clean source afterwards."""
        signal = data.signal
        source = data.source
        handlers = data.handlers

        try:
            for handler in handlers:
                handler.callback(signal, handler.data)
        except ExitMainLoop:
            self._quit_all_loops()

        # based on GLib documentation we should clean source
        # source will be removed from event loop context this way
        source.destroy()

        self._mark_signal_processed(signal)

    def _raise_exception(self, data):
        signal = data.signal
        self._quit_all_loops()

        raise signal.exception_info[0] from signal.exception_info[1]

    def _quit_all_loops(self):
        for loop_data in reversed(self._event_loops):
            loop_data.loop.quit()

    def run(self):
        """Starts the event loop."""
        super().run()
        if len(self._event_loops) != 1:
            raise ValueError("Can't run event loop multiple times.")

        self._event_loops[0].loop.run()
        log.debug("Main loop ended. Running callback if set.")

        if self._quit_callback:
            cb = self._quit_callback.callback
            cb(self._quit_callback.args)

    def execute_new_loop(self, signal):
        """Starts the new event loop and pass `signal` in it.

        This is required for processing a modal screens.

        :param signal: signal passed to the new event loop
        :type signal: `AbstractSignal` based class
        """
        super().execute_new_loop(signal)

        new_context = GLib.MainContext()
        new_loop = GLib.MainLoop(new_context)
        loop_data = EventLoopData(new_loop)
        self._event_loops.append(loop_data)

        self.enqueue_signal(signal)
        new_loop.run()

    def close_loop(self):
        """Close active event loop.

        Close an event loop created by the `execute_new_loop()` method.
        """
        super().close_loop()
        old_loop_data = self._event_loops.pop()
        old_loop_data.loop.quit()

    def process_signals(self, return_after=None):
        """This method processes incoming async messages.

        Process signals enqueued by the `self.enqueue_signal()` method. Call handlers registered to the signals by
        the `self.register_signal_handler()` method.

        When `return_after` is specified then wait to the point when this signal is processed.
        NO warranty that this method will return immediately after the signal was processed!

        Without `return_after` parameter this method will return after all queued signals with the highest priority
        will be processed.

        The method is NOT thread safe!

        :param return_after: Wait on this signal to be processed.
        :type return_after: Class of the signal.
        """
        super().process_signals(return_after)
        loop_data = self._event_loops[-1]

        if return_after is not None:
            ticket_id = self._register_wait_on_signal(return_after)

            while not self._check_if_signal_processed(return_after, ticket_id):
                self._iterate_event_loop(loop_data.loop)

        else:
            self._iterate_event_loop(loop_data.loop)

    def _iterate_event_loop(self, event_loop):
        context = event_loop.get_context()
        # This is useful for tests
        wait_on_timeout = False
        context.iteration(wait_on_timeout)


class EventLoopData(object):

    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.sources = set()

