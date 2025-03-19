# DeskNote
What if you save your notes right on your wallpaper? This is the most useful for people who dislike note-taking apps or physical sticky notes but still want a fast and efficient method to create reminders accessible at all time.

To install, download the installer here: https://drive.google.com/drive/folders/1YfAqej3imlihzKzzOfLjFZvYfQn_TWwQ?usp=sharing

The original code is posted as DeskNote.py. Any preferred icons for the app could be saved as Icon.ico in the same directory with the .py file. You can compile it however you want. For example:
```
pyinstaller --onefile --windowed --icon=Icon.ico DeskNote.py
```
DeskNote COMMANDS (V1.0):

Commands are beginned with `/`. 

`/date `,`/time`, and `/now` to specify the date and/or time at the momment of submission

All notes will be logged into daily_note>note_log.txt file in the app directory by default, with date and time of the log. To prevent logging, use `/nolog`

To add on to the existing DeskNote, include `/continue` in the new text. 

To remove specific lines in the existing DeskNote, include `/strip{keyword}` with `keyword` being a unique word/phrase in that line. This function only works if the existing DeskNote was logged as the most recent note and `/continue` is mentioned in the text. 

`/textbf{text}`, `/textit{text}`, and `/underline{text}` to format any `text`. 
