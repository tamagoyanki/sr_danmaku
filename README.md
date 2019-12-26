# Showroom Comments Danmaku Recorder
Record [SHOWROOM](https://www.showroom-live.com/) live comments and save them as a danmaku (弾幕 / bullets) subtitle (***`.ass`***) file.
Danmaku subtitles are those bullet-like flying through screen comments. They can ususally be seen on websites like [niconico](https://www.nicovideo.jp/) and [bilibili](https://www.bilibili.com/). 
The saved ***`.ass`*** subtitle file can then be watched with the recorded Showroom video file.

## Installation
1. Install Python 3.x from [Python.org](https://www.python.org/downloads/)

2. Install other required packages:
```
pip install -r requirements.txt
```

## Usage

1. Edit the file ***`rooms.ini`*** to remove example rooms, and add the rooms you want to monitor and record comments.  
2. Run the program:
```
python sr_danmaku.py
```

When program is running, you can enter the following command:
```
- Type "h" or "help" for help.
- Type "q" or "quit" to quit.
- Type "s" or "status" to view status.
- Type "c" or "comment" to turn on/off showing comments.
```

3. If the program is already recording rooms, but you need to emergently record a new room.
You can run another instance of the program with **`-u`** option.
Suppose the room url is `https://www.showroom-live.com/ROOM_URL_KEY`:
```
python sr_danmaku.py -u https://www.showroom-live.com/ROOM_URL_KEY
```
Or
```
python sr_danmaku.py -u ROOM_URL_KEY
```
This will ignore ***`rooms.ini`*** and only record comments from one room.

4. When a live is finished, the recorded comments will be converted to danmaku subtitle, and saved as a ***`.ass`*** file under the folder ***`comments`***.

5. If the danmaku subtitles are not synchronized with the recorded showroom video. You can use [Aegisub Advanced Subtitle Editor](http://www.aegisub.org/) to edit the subtitle ***`.ass`*** file. Using Aegisub you can batch remove subtitles or batch time shift subtitles to synchronize with the video.

## Pack the program to a stand-alone Windows executable .EXE file
1. Install the latest version of PyInstaller which is compatible with Python 3.8:
```
pip install https://github.com/pyinstaller/pyinstaller/archive/develop.tar.gz
```
2. Run:
```
pyinstaller -F .\sr_danmaku.py
```
3. Find ***`sr_danmaku.exe`*** in the produced ***`dist`*** folder. 
Move it and place it with ***`sr_danmaku.ini`*** and ***`room.ini`*** in the same folder, and you're done.
You can double click ***`sr_danmaku.exe`*** to run.


## Known Issues

1. On Windows 10, when you mouse click on the Command Prompt window, the program will freeze. To make it run again, you need to press Esc or right click the mouse or you can type a command. To solve this problem, make sure you disable the QuickEdit mode of Command Prompt: Right click on the top bar of Command Prompt, select ***`Properties`*** (or ***`Defaults`*** if you want to make the change once for all). Then under the ***`Options`*** tab, uncheck ***`QuickEdit Mode`*** and click ***`OK`***. For more details, please see the following link: [Why is my command prompt freezing on Windows 10?](https://stackoverflow.com/questions/33883530/why-is-my-command-prompt-freezing-on-windows-10)


-----------------------------------------------------------------------
## Links
- [Showroom Live Watcher](https://github.com/wlerin/showroom) : records Showroom live streams.

- [Showroom Comment and Gift Viewer](http://sr-viewer.sacra.co/) (Japanese): view the comments and gifts, and be able to read the comments out loud.

- [Showroom Comment Viewer](http://sr-com.net/comment_viewer/pc/) (Japanese): fancy comments and gifts viewer

- [Showroom Rokugatch](https://www.skypower.xyz/showroom_rokugatch.html) (Japanese): Showroom recorder. Can be set up to work with Haishin Kakuninkun.

- [Haishin Kakuninkun](https://www.skypower.xyz/haishin_kakuninkun.html) (Japanese): informs you when a room is on live. Can be set up to call Showroom Rokugatch to record the live.

- [Showroom Toolbox](https://chrome.google.com/webstore/detail/showroom-toolbox/jlelpggiclkhdadagnbdjblokcnnhanl) : chrome extension, provides useful tools for watching showroom.

- [Showroom Sukosuko Tool](https://chrome.google.com/webstore/detail/showroom-%E3%81%99%E3%81%93%E3%81%99%E3%81%93%E3%83%84%E3%83%BC%E3%83%AB/ohfkmalmidmhailhaiifeplheagoopap) (Japanese): chrome extension, provides useful tools for watching showroom.

- [ShowRoomViewer](http://iroiro.konjiki.jp/) ([download page](http://iroiro.konjiki.jp/tool.html)) (Japanese): provides overall information for rooms. 


