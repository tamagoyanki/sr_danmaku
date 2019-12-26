import os
import time
import datetime
import threading
import json
import math
import random
import logging

from json import JSONDecodeError
from argparse import ArgumentParser

# requirements.txt
import pytz
import requests
import websocket

from websocket import WebSocketConnectionClosedException


# from bs4 import BeautifulSoup


def getLives():
    # disable logging from 'requests'
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    rand = int(random.random() * 1000)
    sr_onlives_url = 'https://www.showroom-live.com/api/live/onlives' + '?' + str(rand)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    try:
        r = requests.get(sr_onlives_url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error('Connection error')
        return [], []

    if r.status_code != 200:
        logging.error('Failed to get lives info: {} - {}'.format(r.status_code, r.reason))
        return [], []

    try:
        data = json.loads(r.text)
    except JSONDecodeError as e:
        logging.error('Failed to get lives info: broken message, JSON decode error: {}'.format(e))
        return [], []

    room_all = []
    pop_room = []  # for Popularity

    for category in data["onlives"]:
        # 0, Popularity
        # 704, MEN'S
        # 801, Taiwan
        # 102, Idol
        # 103, Talent Model
        # 101, Music
        # 104, Voice Actors & Anime
        # 105, Comedians/Talk Show
        # 107, Virtual
        # 703, Karaoke
        # 200, Non-Professionals
        # 701, DOB (date of birth)

        genre_id = category["genre_id"]
        if genre_id == 801 or genre_id == 701 or genre_id == 703 or genre_id == 704:
            # skip Taiwan, DOB, Karaoke, and MEN'S, these are duplicates
            continue

        lives = category["lives"]

        for room in lives:
            if room.get("room_url_key") is None:
                continue

            # {
            #     "room_url_key": "LOVE_ANNA_YAMAMOTO",
            #     "official_lv": 1,
            #     "sub_name": "857 days in a row",
            #     "color": "#ebcd00",
            #     "follower_num": 16613,
            #     "started_at": 1577193934,
            #     "live_id": 8394483,
            #     "is_follow": false,
            #     "streaming_url_list": [
            #         {
            #             "is_default": true,
            #             "url": "https://hls-cdn12-showroom.cdn-dena.com/liveedge/6d7f825dab7553ddae4339050225437d72ec22b7f58bdaf344d8fa22baa98ba3_low/playlist.m3u8",
            #             "label": "low spec",
            #             "id": 4,
            #             "type": "hls",
            #             "quality": 100
            #         }
            #     ],
            #     "live_type": 0,
            #     "tags": [],
            #     "image": "https://image.showroom-live.com/showroom-prod/image/room/cover/65f47a30a49a50542a6290a93dfff4beb327b9d1268489245ec068a7e6330330_s.png?v=1575199996",
            #     "view_num": 1350,
            #     "genre_id": 102,
            #     "main_name": "山本 杏奈（=LOVE）",
            #     "cell_type": 102,
            #     "bcsvr_key": "8016f3:LyTkjap9",
            #     "room_id": 105923
            # }

            if genre_id == 0:  # popular rooms
                pop_room.append(room)
            else:
                room_all.append(room)

            # print(room)
            # print(json.dumps(room, indent=2, ensure_ascii=False))
    return room_all, pop_room


def convert_comments_to_danmaku(startTime, commentList,
                                fontsize=18, fontname='MS PGothic', alpha='1A',
                                width=640, height=360):
    """
    Convert comments to danmaku (弾幕 / bullets) subtitles

    :param startTime: comments recording start time (timestamp in milliseconds)
    :param commentList: list of showroom messages
    :param fontsize = 18
    :param fontname = 'MS PGothic'
    :param alpha = '1A'     # transparency '00' to 'FF' (hex string)
    :param width = 640      # video screen height
    :param height = 360     # video screen width

    :return a string of danmaku subtitles
    """

    # slotsNum: max number of comment line vertically shown on screen
    slotsNum = math.floor(height / fontsize)
    travelTime = 8 * 1000  # 8 sec, bullet comment flight time on screen

    # ass subtitle file header
    danmaku = "[Script Info]\n"
    danmaku += "ScriptType: v4.00+\n"
    danmaku += "Collisions: Normal\n"
    danmaku += "PlayResX: " + str(width) + "\n"
    danmaku += "PlayResY: " + str(height) + "\n\n"
    danmaku += "[V4+ Styles]\n"
    danmaku += "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    danmaku += "Style: danmakuFont, " + fontname + ", " + str(fontsize) + \
               ", &H00FFFFFF, &H00FFFFFF, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0.00, 0.00, 1, 1, 0, 2, 20, 20, 20, 0\n\n"
    danmaku += "[Events]\n"
    danmaku += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

    # each comment line on screen can be seen as a slot
    # each slot will be filled with the time which indicates when the bullet comment will disappear on screen
    # slot[0], slot[1], slot[2], ...: for the comment lines from top to down
    slots = []
    for i in range(slotsNum):
        slots.append(0)

    previousTelop = ''

    for data in commentList:
        m_type = str(data['t'])
        if m_type != '1' and m_type != '8':
            # not a comment and not a telop
            continue

        comment = ''
        if m_type == '8':  # telop
            telop = data['telop']
            if telop is not None and telop != previousTelop:
                previousTelop = telop
                # show telop as a comment
                comment = 'Telop: 【' + telop + '】'
            else:
                continue

        else:  # comment
            comment = data['cm']

        # compute current relative time
        t = data['received_at'] - startTime

        # find available slot vertically from up to down
        selectedSlot = 0
        isSlotFound = False
        for j in range(slotsNum):
            if slots[j] <= t:
                slots[j] = t + travelTime  # replaced with the time that it will finish
                isSlotFound = True
                selectedSlot = j
                break

        # when all slots have larger times, find the smallest time and replace the slot
        if not isSlotFound:
            minIdx = 0
            for j in range(1, slotsNum):
                if slots[j] < slots[minIdx]:
                    minIdx = j

            slots[minIdx] = t + travelTime
            selectedSlot = minIdx

        # calculate bullet comment flight positions, from (x1,y1) to (x2,y2) on screen

        # extra flight length so a comment appears and disappears outside of the screen
        extraLen = math.ceil(len(comment) / 2.0)

        x1 = width + extraLen * fontsize
        y1 = (selectedSlot + 1) * fontsize
        x2 = 0 - extraLen * fontsize
        y2 = y1

        def msecToAssTime(uTime):
            """ convert milliseconds to ass subtitle format """
            msec = uTime % 1000
            msec = int(round(msec / 10.0))
            uTime = math.floor(uTime / 1000.0)
            s = int(uTime % 60)
            uTime = math.floor(uTime / 60.0)
            m = int(uTime % 60)
            h = int(math.floor(uTime / 60.0))
            msf = ("00" + str(msec))[-2:]
            sf = ("00" + str(s))[-2:]
            mf = ("00" + str(m))[-2:]
            hf = ("00" + str(h))[-2:]
            return hf + ":" + mf + ":" + sf + "." + msf

        # build ass subtitle script
        sub = "Dialogue: 3," + msecToAssTime(t) + "," + msecToAssTime(t + travelTime)
        # alpha: 00 means fully visible, and FF (ie. 255 in decimal) is fully transparent.
        sub += ",danmakuFont,,0000,0000,0000,,{\\alpha&H" + alpha + "&\\move("
        sub += str(x1) + "," + str(y1) + "," + str(x2) + "," + str(y2)
        sub += ")}" + comment + "\n"

        danmaku += sub
    # end of for
    return danmaku


class CommentRecorder:
    def __init__(self, room_url_key, room_data, settings):
        self.settings = settings
        self.show_debug_message = settings['program_settings']['show_debug_message']  # 1: enable, 0: disable
        self.save_comments_debug_log = settings['program_settings']['save_comments_debug_log']  # 1: enable, 0: disable

        self.room_data = room_data
        self.room_url_key = room_url_key
        self.room_name = self.room_data['main_name']
        self.room_id = self.room_data['room_id']

        self.comment_log = []
        self._thread_main = None
        self.comment_count = 0
        self.ws = None
        self.ws_startTime = 0
        self.ws_send_txt = ''
        self._thread_interval = None
        self._isQuit = False
        self._isRecording = False

    @property
    def isRecording(self):
        return self._isRecording

    def start(self):
        self._thread_main = threading.Thread(target=self.record, name=self.room_url_key)
        self._thread_main.start()

    def record(self):
        """
        Record comments and save as niconico danmaku (弾幕 / bullets) subtitle ass file
        """

        def ws_on_message(ws, message):
            """ WebSocket callback """
            # "created at" has no millisecond part, so we record the precise time here
            now = int(time.time() * 1000)

            idx = message.find("{")
            if idx < 0:
                logging.error('no JSON message - {}'.format(message))
                return
            message = message[idx:]
            try:
                data = json.loads(message)
            except JSONDecodeError as e:
                logging.debug('broken message, JSON decode error: {}'.format(e))
                logging.debug('--> {}'.format(message))
                # try to fix
                message += '","t":"1"}'
                try:
                    data = json.loads(message)
                except JSONDecodeError:
                    logging.error('failed to fix broken message, JSON decode error: {}'.format(message))
                    return
                logging.debug('--> fix passed: {}'.format(message))

            # add current time
            data['received_at'] = now

            # Some useful info in the message:
            # ['t']  message type, determine the message is comment, telop, or gift
            # ['cm'] comment
            # ['ac'] name
            # ['u']  user_id
            # ['av'] avatar_id
            # ['g'] gift_id
            # ['n'] gift_num

            # type of the message
            m_type = str(data['t'])  # could be integer or string

            if m_type == '1':  # comment
                comment = data['cm']

                # skip counting for 50
                if len(comment) < 3 and comment.isdecimal() and int(comment) <= 50:
                    # s1 = '⑷'; s2 = u'²'; s3 = '❹'
                    # print(s1.isdigit())  # True
                    # print(s2.isdigit())  # True
                    # print(s1.isdecimal())  # False
                    # print(s2.isdecimal())  # False
                    # int(s1)  # ValueError
                    # int(s2)  # ValueError
                    pass
                else:
                    comment = comment.replace('\n', ' ')  # replace line break to a space
                    if self.settings['program_settings']['show_comments'] > 0:
                        logging.info('{}: {}'.format(self.room_url_key, comment))
                    data['cm'] = comment
                    self.comment_log.append(data)
                    self.comment_count += 1

            elif m_type == '2':  # gift
                pass

            elif m_type == '8':  # telop
                self.comment_log.append(data)
                if data['telop'] is not None:  # could be null
                    # logging.info('{}: telop = {}'.format(self.room_url_key, data['telop']))
                    pass

            elif m_type == '11':  # cumulated gifts report
                pass

            elif m_type == '101':  # indicating live finished
                self.comment_log.append(data)
                self._isQuit = True

            else:
                self.comment_log.append(data)

        def ws_on_error(ws, error):
            """ WebSocket callback """
            logging.error('websocket on error: {}'.format(error))

        def ws_on_close(ws):
            """ WebSocket callback """
            logging.debug('websocket closed')
            self._isQuit = True

        def interval_send(ws):
            """
            interval thread to send message and to close WebSocket
            """
            count = 60
            while True:
                # check whether to quit every sec
                if self._isQuit:
                    break

                # send bcsvr_key every 60 secs
                if count >= 60:
                    count = 0
                    try:
                        # logging.debug('sending {}'.format(self.ws_send_txt))
                        ws.send(self.ws_send_txt)
                    except WebSocketConnectionClosedException as e:
                        logging.debug(
                            'WebSocket closed before sending message. {} Closing interval thread now...'.format(e))
                        break

                time.sleep(1)
                count += 1

            # close WebSocket
            if ws is not None:
                ws.close()
                ws = None
            logging.debug('interval thread finished')

        def ws_on_open(ws):
            """ WebSocket callback """
            self.ws_startTime = int(time.time() * 1000)
            logging.debug('websocket on open')

            # keep sending bcsvr_key to the server to prevent disconnection
            self._thread_interval = threading.Thread(target=interval_send, name='{} interval'.format(self.room_url_key),
                                                     args=(ws,))
            self._thread_interval.start()

        # Get live info from https://www.showroom-live.com/api/live/live_info?room_id=xxx
        # If a room closes and then reopen on live within 30 seconds (approximately),
        # the broadcast_key from https://www.showroom-live.com/api/live/onlives
        # will not be updated with the new key. It's the same situation that when a
        # room live is finished, /api/live/onlives will not update its onlives list within
        # about 30 seconds. So here it's better to get accurate broadcast_key
        # from /api/live/live_info
        live_info_url = 'https://www.showroom-live.com/api/live/live_info?room_id=' + str(self.room_id)
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        try:
            r = requests.get(live_info_url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            logging.error('Failed to get live info: ConnectionError - {}'.format(e))
            return False
        if r.status_code != 200:
            logging.error('Failed to get live info: {} - {}'.format(r.status_code, r.reason))
            return False

        try:
            info = json.loads(r.text)
        except JSONDecodeError as e:
            logging.error('Broken live info, JSON decode error: {}'.format(e))
            return False

        if len(info['bcsvr_key']) == 0:
            logging.debug('not on live, no bcsvr_key.')
            return False

        logging.info('{}: is on live, start recording comments'.format(self.room_url_key))

        # logging.debug(json.dumps(self.room_data, indent=2, ensure_ascii=False))

        self._isRecording = True
        self.ws_send_txt = 'SUB\t' + info['bcsvr_key']
        if self.settings['program_settings']['show_debug_message'] > 0:
            websocket.enableTrace(True)  # False: disable trace outputs
        else:
            websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp('ws://' + info['bcsvr_host'] + ':' + str(info['bcsvr_port']),
                                         on_message=ws_on_message,
                                         on_error=ws_on_error,
                                         on_close=ws_on_close)
        self.ws.on_open = ws_on_open
        self.ws.run_forever()

        self.comment_log = sorted(self.comment_log, key=lambda x: x['received_at'])

        if self.comment_count > 0:
            # convert comments to danmaku
            alpha = self.settings['danmaku_settings']['alpha']
            alpha = int(round(alpha * 255.0 / 100.0))
            if alpha > 255:
                alpha = 255
            elif alpha < 0:
                alpha = 0
            alphaHex = '00' + hex(alpha).upper()[2:]
            alphaHex = alphaHex[-2:]

            assTxt = convert_comments_to_danmaku(self.ws_startTime, self.comment_log,
                                                 fontsize=self.settings['danmaku_settings']['font_size'],
                                                 fontname=self.settings['danmaku_settings']['font_name'],
                                                 alpha=alphaHex,
                                                 width=self.settings['danmaku_settings']['width'],
                                                 height=self.settings['danmaku_settings']['height']
                                                 )
        else:
            logging.info('{}: no comments to save'.format(self.room_url_key))

        # change time zone to Tokyo time
        tokyo_timezone = pytz.timezone('Asia/Tokyo')
        dt = datetime.datetime.fromtimestamp(self.ws_startTime / 1000.0)
        dt_tokyo = dt.astimezone(tokyo_timezone)
        time_string = dt_tokyo.strftime('%y%m%d %H%M%S')

        # create subfolder 'comments'
        path = os.getcwd()
        path = os.path.join(path, "comments")
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
            except OSError:
                path = os.getcwd()

        # remove invalid file name characters \ / : * ? " < > |
        invalidChar = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for c in invalidChar:
            self.room_name = self.room_name.replace(c, '_')

        filename = os.path.join(path, self.room_url_key + ' ' + time_string + ' ' + self.room_name)
        logfile = filename + '.log'
        assfile = filename + '.ass'

        # in case that room_name is still invalid
        filename2 = os.path.join(path, self.room_url_key + ' ' + time_string)
        logfile2 = filename2 + '.log'
        assfile2 = filename2 + '.ass'

        def saveLog(_logfile):
            with open(_logfile, 'w', encoding='utf8') as logfp:
                for item in self.comment_log:
                    logfp.write('{}{}'.format(item, '\n'))
            logging.info(self.room_url_key + ': recording finished, saved to ' + _logfile)

        def saveAss(_assfile):
            with open(_assfile, 'w', encoding='utf8') as assfp:
                assfp.write(assTxt)
            logging.info(self.room_url_key + ': recording finished, saved to ' + _assfile)

        try:
            if self.save_comments_debug_log > 0:
                saveLog(logfile)
            if self.comment_count > 0:
                saveAss(assfile)
        except FileNotFoundError as e:
            logging.error('FileNotFoundError: {}'.format(e))
            logging.error('--> try to use {} as filename'.format(self.room_url_key))
            if self.save_comments_debug_log > 0:
                saveLog(logfile2)
            if self.comment_count > 0:
                saveAss(assfile2)
        except OSError as e:
            logging.error('OSError: {}'.format(e))
            logging.error('--> try to use {} as filename'.format(self.room_url_key))
            if self.save_comments_debug_log > 0:
                saveLog(logfile2)
            if self.comment_count > 0:
                saveAss(assfile2)

        self._isRecording = False
        return True

    def quit(self):
        """
        To quit comment logger anytime (to close WebSocket, save file and finish job)
        """
        self._isQuit = True
        self._thread_main.join()
        if self._thread_interval is not None:
            self._thread_interval.join()


class RoomMonitor:
    def __init__(self, room_url_keys, settings):
        self.room_url_keys = room_url_keys
        self.nRooms = 0
        self.cRecords = []
        self._isQuit = False
        self.t = None
        self.settings = settings
        self.interval = settings['program_settings']['interval']

    def quit(self):
        self._isQuit = True
        self.t.join()

    def start(self):
        self.t = threading.Thread(target=self.monitor)
        self.t.start()
        return self.t

    def monitor(self):

        self.nRooms = len(self.room_url_keys)

        self.cRecords = [None] * self.nRooms

        count = self.interval
        logging.debug('interval = {}, {} rooms = {}'.format(self.interval, self.nRooms, self.room_url_keys))
        while True:
            if count >= self.interval:
                count = 0
                room_all, pop_room = getLives()
                for i in range(self.nRooms):
                    if self.cRecords[i] is not None:
                        if self.cRecords[i].isRecording:
                            # logging.debug('already recording...')
                            continue
                        else:
                            self.cRecords[i] = None

                    for room in room_all:
                        if self.room_url_keys[i] == room['room_url_key']:
                            logging.debug('{}: is on main site live list.'.format(self.room_url_keys[i]))
                            cr = CommentRecorder(self.room_url_keys[i], room, self.settings)
                            cr.start()
                            self.cRecords[i] = cr
                            continue

            if self._isQuit:
                break
            count += 1
            time.sleep(1)
            # end while

        # quitting
        for i in range(self.nRooms):
            if self.cRecords[i] is not None:
                if self.cRecords[i].isRecording:
                    logging.info('quitting ' + self.cRecords[i].room_url_key + '... ')
                    self.cRecords[i].quit()
                    self.cRecords[i] = None

    def view_status(self):
        logging.info('Monitoring rooms: {}'.format(self.nRooms))
        k = 0
        s = ''
        for i in range(self.nRooms):
            if self.cRecords[i] is not None:
                if self.cRecords[i].isRecording:
                    k += 1
                    s += '  {}) {}: {}\n'.format(k, self.cRecords[i].room_url_key, self.cRecords[i].room_name)
        s = 'Recording rooms: {}\n'.format(k) + s
        logging.info(s)
        return


def readIni(mode, filename):
    settingsTxt = """[program_settings]
interval = 10                    # seconds, time interval to check rooms are on live or not
show_comments = 0                # 1: enable, 0: disable
show_debug_message = 0           # 1: enable, 0: disable
save_program_debug_log = 0       # 1: enable, 0: disable
save_comments_debug_log = 0      # 1: enable, 0: disable

[danmaku_settings]
width = 640
height = 360
font_name = MS PGothic
font_size = 18
alpha = 10                       # transparency percentage, a number between 0 and 100



"""

    roomsTxt = """#######################################################################################
# To add a room to monitor and record its comments, copy and paste its room_url_key
# in the "[rooms]" section below. Each line is only for one room.
#
# The room_url_key is the last part of the room url address.
# For example, if a room url is https://www.showroom-live.com/LOVE_ANNA_YAMAMOTO
# The room_url_key is the last part after the main website address: LOVE_ANNA_YAMAMOTO
# Please note that it is case sensitive.
#
# The program checks the on live list from the Showroom website. A wrong room_url_key
# will not be notified by the program since it will never be found on the on live list.
#
# Anything after the "#" symbol on a line will be ignored by the program.
# You can put description for a room_url_key after #, or you
# can temporarily cancel a room_url_key by inserting # in
# front of it.
#
# This file only provides an example, go ahead to remove all room_url_keys below and
# add your own rooms. Or you can delete this file and run the program once to generate
# a clean file.
#######################################################################################
[rooms]



"""

    # create ini if not present
    path = os.getcwd()
    filenamepath = os.path.join(path, filename)

    if not os.path.isfile(filenamepath):
        with open(filenamepath, 'w', encoding='utf8') as fp:
            if mode == 1:
                fp.write(settingsTxt)
            else:
                fp.write(roomsTxt)

    with open(filenamepath, 'r', encoding='utf8') as fp:
        lines = fp.readlines()

    inComments = False
    foundProgSettings = False
    foundDanmakuSettings = False
    foundRooms = False
    program_settings = {}
    danmaku_settings = {}
    room_url_keys = []
    for line in lines:
        line = line.strip()
        # remove # and line after it
        sharp = line.find('#')
        if sharp > -1:
            line = line[:sharp].strip()
        if len(line) == 0:
            continue

        if line.lower().find('[program_settings]') > -1:
            foundProgSettings = True
            foundDanmakuSettings = False
            foundRooms = False
            continue
        if line.lower().find('[danmaku_settings]') > -1:
            foundProgSettings = False
            foundDanmakuSettings = True
            foundRooms = False
            continue
        if line.lower().find('[rooms]') > -1:
            foundProgSettings = False
            foundDanmakuSettings = False
            foundRooms = True
            continue

        if foundProgSettings:
            s1, s2 = line.split("=", 1)
            program_settings.update({s1.lower().strip(): int(s2.lower().strip())})
            # if s1.strip().lower().find('interval') > -1:
            #     settings['interval'] = float(s2.strip())
            continue

        if foundDanmakuSettings:
            s1, s2 = line.split("=", 1)
            s1 = s1.lower().strip()
            s2 = s2.strip()
            if s1.find('font_name') < 0:
                s2 = int(s2)
            danmaku_settings.update({s1: s2})
            continue

        if foundRooms:
            room_url_keys.append(line)

    settings = {'program_settings': program_settings, 'danmaku_settings': danmaku_settings}

    if mode == 1:
        return settings
    else:
        return room_url_keys


def main():
    # read settings and room_url_keys
    settings = readIni(1, 'sr_danmaku.ini')
    room_url_keys = readIni(2, 'rooms.ini')

    # build logging
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleFmt = logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%H:%M:%S')
    consoleHandler.setFormatter(consoleFmt)
    if settings['program_settings']['show_debug_message'] > 0:
        consoleHandler.setLevel(logging.DEBUG)
    else:
        consoleHandler.setLevel(logging.INFO)
    log.addHandler(consoleHandler)

    if settings['program_settings']['save_program_debug_log'] > 0:
        fileHandler = logging.FileHandler('sr_danmaku.log', encoding='utf-8')
        fileFmt = logging.Formatter(fmt='%(asctime)s [%(threadName)s][%(levelname)s][%(name)s] %(message)s',
                                    datefmt='%y%m%d %H:%M:%S')
        fileHandler.setFormatter(fileFmt)
        fileHandler.setLevel(logging.DEBUG)
        log.addHandler(fileHandler)

    # build ArgumentParser
    parser = ArgumentParser(description='Monitoring showroom and download comments to danmaku ass')
    parser.add_argument('-u', '--url', help='Only monitor this one SHOWROOM_URL. \
                For more rooms, please edit file "sr_danmaku.ini".', metavar='SHOWROOM_URL', dest='sr_url')

    log.debug('program_settings = {}'.format(settings['program_settings']))
    log.debug('danmaku_settings = {}'.format(settings['danmaku_settings']))

    # handle args
    args = parser.parse_args()

    nRoom = len(room_url_keys)
    if args.sr_url:
        idx = args.sr_url.find('https://www.showroom-live.com/')
        if idx > -1:
            room_url_key = args.sr_url[idx + 30:].strip()
        else:
            room_url_key = args.sr_url
        room_url_keys = [room_url_key]
        log.info('Monitoring {} ...'.format(room_url_key))

    else:
        # remove duplicates
        nRoomPre = nRoom
        room_url_keys = list(dict.fromkeys(room_url_keys))
        nRoom = len(room_url_keys)
        if nRoomPre != nRoom:
            log.info('Removed duplicate {} room(s)'.format(nRoomPre - nRoom))
        log.info('Monitoring {} rooms...'.format(len(room_url_keys)))

    if len(room_url_keys) == 0:
        log.info('No rooms to monitor')
        return

    if settings['program_settings']['show_comments'] > 0:
        log.info('Comments on')
    else:
        log.info('Comments off')

    helptxt = '''Commands:
- Type "h" or "help" for help.
- Type "q" or "quit" to quit.
- Type "s" or "status" to view status.
- Type "c" or "comment" to turn on/off showing comments.
'''
    log.info(helptxt)

    # start monitoring room
    rm = RoomMonitor(room_url_keys, settings)
    rm.start()

    while True:
        try:
            line = input().strip().lower()
        except KeyboardInterrupt:  # Ctrl-C is pressed
            log.info('KeyboardInterrupt')
            break
        if line == 'q' or line == 'quit' or line == 'exit':
            break
        elif line == 'h' or line == 'help':
            log.info(helptxt)
        elif line == 's' or line == 'status':
            rm.view_status()
        elif line == 'c' or line == 'comment' or line == 'comments':
            if settings['program_settings']['show_comments'] > 0:
                settings['program_settings']['show_comments'] = 0
                log.info('Comments off')
            else:
                settings['program_settings']['show_comments'] = 1
                log.info('Comments on')
        else:
            log.info('Unknown command. Type "h" or "help" for help.')
        time.sleep(0.1)

    log.info('quitting jobs...')
    rm.quit()
    log.info("bye")


if __name__ == '__main__':
    main()
