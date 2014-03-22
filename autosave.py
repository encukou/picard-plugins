# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Save Matches"
PLUGIN_AUTHOR = u"Petr Viktorin"
PLUGIN_DESCRIPTION = """<p>Save only those albums that were very confidently identified, and remove them from the list.</p>

<p>
Perfect when tagging a giant collection for the first time: cluster everything,
look everything up, then use this to save the albums that were looked up
with confidence.
</p>

<p>
Only saves &amp; removes albums with 4 tracks or more, where each track has more than
90% similarity to the original metadata.
</p>

<p>
<em>Usage:</em> Select all albums in the right pane, then choose Plugins/Save and remove
well-identified albums from the context menu.
</p>
"""
PLUGIN_VERSION = "0.2"
PLUGIN_API_VERSIONS = ["0.15"]

import functools

from PyQt4 import QtCore
from picard.album import Album
from picard.util import webbrowser2, format_time, thread
from picard.ui.itemviews import BaseAction, register_album_action


class SaveMatches(BaseAction):
    NAME = "Save and remove well-identified albums"

    def callback(self, albums):
        """Save all eligible albums from objs"""
        if albums:
            self.process(albums[0])
            QtCore.QTimer.singleShot(0, lambda: self.callback(albums[1:]))

    def is_album_eligible(self, album):
        """Return True if the album is well-identified"""
        print 'Looking at album ' + album.metadata['album']
        if not isinstance(album, Album):
            print 'Not an album'
            return False
        # The album has to be Complete
        if not album.is_complete():
            print 'Incomplete album'
            return False
        if len(album.tracks) < 4:
            # Too few tracks to be really confident
            print 'Too few tracks'
            return False
        files_to_save = []
        for track in album.tracks:
            if len(track.linked_files) != 1:
                print 'Track %s not done ' % track.metadata['title']
                return False
            if track.linked_files[0].similarity < 0.9:
                print 'Track %s not similar enough ' % track.metadata['title']
                return False
        return True

    def process(self, album):
        if not self.is_album_eligible(album):
            return
        # We'll keep a set of all the files we need to process.
        # Then, when a file is saved, it is removed from the set and
        # if the set becomes empty, the album is removed.

        # Build the set
        files_to_save = set()
        for track in album.tracks:
            files_to_save.update(track.linked_files)

        # Kick off saving
        for file_to_save in files_to_save:
            file_to_save._saving_finished = functools.partial(
                file_saving_finished,
                file_to_save, files_to_save, album,
                file_to_save._saving_finished)
            print "On to save " + file_to_save.metadata['title']
            file_to_save.save()


def file_saving_finished(file, files, album, original_saving_finished,
                         result=None, error=None):
    """Un-monkeypatch _saving_finished, and remove album if done"""
    file._saving_finished = original_saving_finished
    original_saving_finished(result, error)
    if not error:
        files.discard(file)
        if not files:
            album.tagger.remove_album(album)
            print 'Album complete: ' + album.metadata['album']
    else:
        print 'Error saving file "%s", will not remove album' % (
            file.metadata['title'])


register_album_action(SaveMatches())
