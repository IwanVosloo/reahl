# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The Reahl context utilities."""

from __future__ import print_function, unicode_literals, absolute_import, division

import inspect
import contextlib


class NoContextFound(Exception):
    pass

class NoContext(object):
    def __getattr__(self, name):
        raise NoContextFound('An attempt was made to access %s on the context, but not context was present in the call stack' % name)



class ExecutionContext(object):
    """Most code execute "in the scope of" some ExecutionContext. Such code can obtain
       the current ExecutionContext by calling ExecutionContext.get_context. The ExecutionContext
       of code comprises of: the current Configuration for all components, the current UserSession,
       and a SystemControl.
    
       .. attribute:: config
       
       .. attribute:: session
       
       .. attribute:: system_control
    """

    @classmethod
    def for_config_directory(cls, config_directory):
        from reahl.component.config import StoredConfiguration # Here, to avoid circular dependency
        
        config = StoredConfiguration(config_directory)
        config.configure()
        new_context = cls()
        new_context.config = config
        return new_context

    @classmethod
    def get_context_id(cls):
        """Returns a unique, hashable identifier identifying the current call context."""
        return cls.get_context().id

    @classmethod
    def get_context(cls):
        """Returns the current call context, or :class:`NoContext` if there is none."""
        no_context = NoContext()
        context = no_context
        f = inspect.currentframe()
        while context is no_context and f:
            candidate = f.f_locals.get('__reahl_context__', None)
            if isinstance(candidate, ExecutionContext):
                context = candidate
            to_delete = f
            f = f.f_back
            del to_delete
        return context

    def __init__(self, parent_context=None):
        self.parent_context = parent_context or self.get_context()
        self.id = (self.parent_context.id if isinstance(self.parent_context, ExecutionContext) else id(self))

    def install(self, stop=None):
        f = inspect.currentframe()
        i = 0
        if not stop:
            def stop(ff):
                return i >= 1
        while not stop(f):
            calling_frame = f.f_back
            i += 1
            del f
            f = calling_frame
        calling_frame.f_locals['__reahl_context__'] = self
        del calling_frame
        return self

    @property
    def interface_locale(self):
        """Returns a string identifying the current locale."""
        session = getattr(self, 'session', None)
        if not session:
            return 'en_gb'
        return self.session.get_interface_locale()

    def __enter__(self):
        assert None, 'Fuck'
