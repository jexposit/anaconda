#
# Base object of all payload handlers.
#
# Copyright (C) 2018 Red Hat, Inc.
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
from abc import ABCMeta, abstractmethod

from pyanaconda.core.signal import Signal
from pyanaconda.modules.common.errors.payload import IncompatibleSourceError, SourceSetupError
from pyanaconda.modules.common.base import KickstartBaseModule

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)


class PayloadHandlerBase(KickstartBaseModule, metaclass=ABCMeta):
    """Base class for all the payload handler modules.

    This will contain all API specific to payload handlers which will be called
    by the base payload module.
    """
    def __init__(self):
        super().__init__()
        self._sources = []
        self.sources_changed = Signal()

    @property
    @abstractmethod
    def supported_source_types(self):
        """Get list of supported source types.

        :return: list of supported source types
        :rtype: [values from payload.base.constants.SourceType]
        """
        pass

    @property
    def sources(self):
        """Get list of sources attached to this payload handler.

        :return: list of source objects attached to this handler
        :rtype: [instance of PayloadSourceBase class]
        """
        return self._sources

    def set_sources(self, sources):
        """Set a new list of sources to this payload handler.

        Before setting the sources, please make sure the sources are not initialized otherwise
        the SourceSetupError exception will be raised. Payload have to cleanup after itself.

        ..NOTE:
        The SourceSetupError is a reasonable effort to solve the race condition. However,
        there is still a possibility that the task to initialize sources (`SetupSourcesWithTask()`)
        was created with the old list but not run yet. In that case this check will not work and
        the initialization task will run with the old list.

        :param sources: set a new sources
        :type sources: instance of pyanaconda.modules.payload.base.source_base.PayloadSourceBase
        :raise: IncompatibleSourceError when source is not a supported type
                SourceSetupError when attached sources are initialized
        """
        # TODO: Add test for this when there will be public API
        for source in sources:
            if source.type not in self.supported_source_types:
                raise IncompatibleSourceError("Source type {} is not supported by this handler."
                                              .format(source.type))

        if any(source.is_ready() for source in self.sources):
            raise SourceSetupError("Can't change list of sources if there is at least one source "
                                   "initialized! Please tear down the sources first.")

        self._sources = sources
        log.debug("New sources %s was added.", sources)
        self.sources_changed.emit()

    def has_source(self):
        """Check if any source is set.

        :return: True if source object is set
        :rtype: bool
        """
        return bool(self.sources)

    @abstractmethod
    def publish_handler(self):
        """Publish object on DBus and return its path.

        :returns: path to this handler
        :rtype: string
        """
        pass