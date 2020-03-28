#!/bin/bash

EXPORT_SCRIPT=$HOME/Projects/Notes/Bear-Markdown-Export/bear_export_sync.py
CLEAN_SCRIPT=$HOME/Projects/Notes/notetools/note_janitor.py
EXPORT_LOCATION=$HOME/Work/BearNotes
WEB_NOTES=$HOME/Work/WebNotes
PUBLISH_SCRIPT=$HOME/Projects/Notes/notetools/note_publisher.py
NOTETOWER=$HOME/Projects/Notes/notetower
NOTE_SITE=$HOME/Projects/Notes/note-site

source ~/.bash_profile
echo "doing first export"
python $EXPORT_SCRIPT
echo "running link janitor"
rm $EXPORT_LOCATION/Untitled.md
nvm use 12
# note-link-janitor $EXPORT_LOCATION
echo "running clean script"
python $CLEAN_SCRIPT $EXPORT_LOCATION
echo "running sync"
python $EXPORT_SCRIPT
cp $EXPORT_LOCATION $WEB_NOTES
python $PUBLISH_SCRIPT $WEB_NOTES
cd $NOTETOWER
nvm use 10
yarn run updateNotes
