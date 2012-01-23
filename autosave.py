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
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.15"]


from PyQt4 import QtCore
from picard.album import Album
from picard.util import webbrowser2, format_time
from picard.ui.itemviews import BaseAction, register_album_action


class SaveMatches(BaseAction):
    NAME = "Save and remove well-identified albums"

    def callback(self, objs):
        if objs:
            self.try_save(objs[0])
            QtCore.QTimer.singleShot(0, lambda: self.callback(objs[1:]))

    def try_save(self, album):
        # We want albums only
        if not isinstance(album, Album):
            return
        print 'Looking at album ' + album.metadata['album']
        # The album has to be Complete
        if not album.is_complete():
            print 'Incomplete album'
            return
        if len(album.tracks) < 4:
            # Too few tracks to be really confident
            print 'Too few tracks'
            return
        files_to_save = []
        for track in album.tracks:
            if len(track.linked_files) != 1:
                print 'Track %s not done ' % track.metadata['title']
                return
            if track.linked_files[0].similarity < 0.9:
                print 'Track %s not similar enough ' % track.metadata['title']
                return
            files_to_save.append(track.linked_files[0])
        cancelled = [False]
        def next_action(result=None, error=None):
            if error is not None:
                print "Error!"
                print error
                cancelled[0] = True
            else:
                # How do I know if the save failed, anyway?
                print "Saved OK!"
            if files_to_save:
                print "On to save " + files_to_save[0].metadata['title']
                files_to_save.pop(0).save(next_action, self.config.setting)
            else:
                if not cancelled[0]:
                    album.tagger.remove_album(album)
                    cancelled[0] = True
                    print 'Album complete: ' + album.metadata['album']
                else:
                    print 'Saving failed: ' + album.metadata['album']
        next_action()

register_album_action(SaveMatches())

