#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import datetime
import simplejson as json
import urllib2
import urlutil
# import web_pdb

from urlparse import parse_qsl, urljoin
from urllib import urlencode
from consts import *

# Plugin Info
ADDON_HANDLE = int(sys.argv[1])
ADDON_ID     = 'plugin.video.epgstation'
settings     = xbmcaddon.Addon(ADDON_ID)
server_url   = ''


def get_url(server=sys.argv[0], apipath='', param={}):
    """
    serverとapipathからURL文字列を作成

    Keyword Arguments:
        server {str} -- server名 (default: {sys.argv[0]})
        apipath {str} -- apiPath (default: {''})
        param {dict} -- GET時の引数 (default: {{}})

    Returns:
        str -- 作成したURL
    """

    # 引数なしの場合
    if len(param) <= 0:
        return urljoin(server, apipath)
    # 引数ありの場合は?の後にurlencodeした引数を追加
    else:
        return '{0}?{1}'.format(urljoin(server, apipath), urlencode(param))


def get_videoCount(rule=-1, genre=-1, channel=-1):
    """
    [summary]

    Keyword Arguments:
        rule {int} -- [description] (default: {-1})
        genre {int} -- [description] (default: {-1})
        channel {int} -- [description] (default: {-1})

    Returns:
        [type] -- [description]
    """

    global server_url

    # 動画一覧取得時のパラメータ
    param = {'isHalfWidth':True, 'limit':1}
    if 0 <= int(rule):    param['ruleId']    = rule
    if 0 <= int(genre):   param['genre']     = genre
    if 0 <= int(channel): param['channelId'] = channel

    # 動画一覧取得時
    urlInfo = urlutil.getUrlInfo(server_url)
    url = get_url(urlInfo["url"], 'api/recorded', param)
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    return json.loads(response.read())['total']


def set_thumbnail(listitem, rule=-1, genre=-1, channel=-1, thumbnailId=-1, offset=-1):
    """
    渡されたlistItemにサムネイル情報を設定する
    rule,genre,channel,thumbnailIdのいづれか一つを指定する

    Arguments:
        listitem {xbmcgui.ListItem} -- サムネイルを設定したいlistItem

    Keyword Arguments:
        rule {int, optional} -- ルールID (default: {-1})
        genre {int, optional} -- ジャンルID (default: {-1})
        channel {int, optional} -- チャンネルID (default: {-1})
        thumbnailId {int, optional} -- サムネイルID (default: {-1})
        offset {int, optional} -- rule/genre/channel指定時の’api/recorded'に渡すoffset (default: {-1})
    """

    global server_url

    # サムネイルIDが指定されている場合
    if thumbnailId != -1:
        thumbnail_url = get_url(server_url, 'api/thumbnails/' + str(thumbnailId))
        listitem.setIconImage(thumbnail_url)
        listitem.setArt({
            'poster': thumbnail_url,
            'fanart': thumbnail_url,
            'landscape': thumbnail_url,
            'thumb': thumbnail_url
        })
        return

    # ルールID・ジャンルID・チャンネルIDが指定されている場合
    elif rule == -1 and genre == -1 and channel == -1: return
    try:
        # 動画取得時のパラメータ
        param = {}
        param['isHalfWidth'] = True
        param['limit']   = 1
        if 0 <= int(rule):    param['ruleId']    = rule
        if 0 <= int(genre):   param['genre']     = genre
        if 0 <= int(channel): param['channelId'] = channel
        if 0 <= int(offset):  param['offset']    = offset

        # 動画取得
        urlInfo = urlutil.getUrlInfo(server_url)
        request = urllib2.Request(get_url(urlInfo["url"], 'api/recorded', param), headers=urlInfo["headers"])
        response = urllib2.urlopen(request)
        video = json.loads(response.read())['records'][0]

        thumbnail_url = get_url(server_url, 'api/thumbnails/' + str(video.get('thumbnails')[0]))
        listitem.setIconImage(thumbnail_url)
        listitem.setArt({
            'poster': thumbnail_url,
            'fanart': thumbnail_url,
            'landscape': thumbnail_url,
            'thumb': thumbnail_url
        })
    except:
        print 'thumbnail get error'


def select_list():
    """
    一覧の選択画面を表示
    """
    li = xbmcgui.ListItem('ルール一覧')
    url = str(get_url(sys.argv[0], '', {'action':'list_rules'}))
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)

    li = xbmcgui.ListItem('ジャンル一覧')
    url = str(get_url(sys.argv[0], '', {'action':'list_genre'}))
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)

    li = xbmcgui.ListItem('チャンネル一覧')
    url = str(get_url(sys.argv[0], '', {'action':'list_channels'}))
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=url, listitem=li, isFolder=True)


def list_rules(offset=0):
    """
    ルール一覧を表示

    Keyword Arguments:
        offset {int} -- [何番目のルールから取得するか] (default: {0})
    """
    global server_url

    # dateadded で並び替えできるように設定
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.setContent(ADDON_HANDLE, 'movies')

    # ルール一覧取得時のパラメータ
    param = {}
    param['limit'] = settings.getSettingInt('rules_length')
    param['offset'] = offset
    param['type'] = 'all'

    # ルール一覧取得
    urlInfo = urlutil.getUrlInfo(server_url)
    url = get_url(urlInfo["url"], 'api/rules', param)
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    rules = json.loads(response.read())["rules"]

    addList_rule({"id":-1, "searchOption": {"keyword": "全ての動画"}})
    addList_rule({"id":0, "searchOption": {"keyword": "キーワードなし"}})

    if settings.getSettingBool('rules_enableonly'):
        for rule in rules:
            if rule['reserveOption']['enable']:
                addList_rule(rule)
    else:
        for rule in rules:
            addList_rule(rule)


def list_genre():
    """
    ジャンル一覧を表示
    """
    global server_url

    # dateadded で並び替えできるように設定
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.setContent(ADDON_HANDLE, 'movies')

    # ジャンル一覧取得
    urlInfo = urlutil.getUrlInfo(server_url)
    url = get_url(urlInfo["url"], 'api/recorded/options')
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    addList_genre({"genre":-1, "keyword": "全ての動画"})
    genres = json.loads(response.read())["genres"]
    for genre in genres:
        genre['keyword'] = GENRE1[genre['genre']]
        addList_genre(genre)


def list_channels():
    """
    チャンネル一覧を表示
    """
    global server_url

    # dateadded で並び替えできるように設定
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.setContent(ADDON_HANDLE, 'movies')

    # チャンネル別件数一覧取得
    urlInfo = urlutil.getUrlInfo(server_url)
    url = get_url(urlInfo["url"], 'api/recorded/options')
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    channel_nums = json.loads(response.read())["channels"]

    # 放送局情報取得
    url = get_url(urlInfo["url"], 'api/channels')
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    channels = json.loads(response.read())

    addList_channel({"channelId":-1, "name": "全ての動画"})

    for channel in channels:
        for num in channel_nums:
            if channel.get('id') == num.get('channelId'):
                addList_channel(channel)
                break


def list_videos(rule=-1, genre=-1, channel=-1, offset=0):
    """
    動画一覧を表示
    rule / genre / channel のいづれか一つを指定

    Keyword Arguments:
        rule {int} -- ルールID (default: {-1})
        genre {int} -- ジャンルID (default: {-1})
        channel {int} -- チャンネルID (default: {-1})
        offset {int} -- 何番目の動画から取得するか (default: {0})
    """

    global server_url

    # dateadded で並び替えできるように設定
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.setContent(ADDON_HANDLE, 'movies')

    # 動画一覧取得時のパラメータ
    param = {'isHalfWidth':True, 'limit':settings.getSettingInt('recorded_length'), 'offset':offset}
    if 0 <= int(rule):    param['ruleId']    = rule
    if 0 <= int(genre):   param['genre']     = genre
    if 0 <= int(channel): param['channelId'] = channel

    # 動画一覧取得時
    urlInfo = urlutil.getUrlInfo(server_url)
    url = get_url(urlInfo["url"], 'api/recorded', param)
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    videos = json.loads(response.read())['records']
    for video in videos:
        addList_video(video)


def addList_rule(rule):
    """
    ファイル一覧にルールフォルダを追加

    :param channel: EPGStationの'api/rules'で取得したルール情報を1つづつ
    :type channel: dict
    """    
    li = xbmcgui.ListItem(rule['searchOption']['keyword'])
    if settings.getSettingBool('folder_showthumbnail'): set_thumbnail(li, rule=rule.get('id', -1))
    search_url = get_url(sys.argv[0], '', {'action':'list_videos', 'rule':rule.get('id', -1)})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=search_url, listitem=li, isFolder=True)


def addList_genre(genre):
    """
    ファイル一覧にジャンルフォルダを追加

    :param channel: EPGStationの'api/recorded/options'で取得した情報のうち、genres以下の情報を1つづつ
    :type channel: dict
    """    
    li = xbmcgui.ListItem(genre['keyword'])
    if settings.getSettingBool('folder_showthumbnail'): set_thumbnail(li, genre=genre.get('genre', -1))
    search_url = get_url(sys.argv[0], '', {'action':'list_videos', 'genre':genre.get('genre', -1)})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=search_url, listitem=li, isFolder=True)


def addList_channel(channel):
    """
    ファイル一覧にチャンネルフォルダを追加

    :param channel: EPGStationの'api/channels'で取得した放送局情報を1つづつ
    :type channel: dict
    """    
    li = xbmcgui.ListItem(channel['name'])
    if settings.getSettingBool('folder_showthumbnail'): set_thumbnail(li, channel=channel.get('id', -1))
    search_url = get_url(sys.argv[0], '', {'action':'list_videos', 'channel':channel.get('id', -1)})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=search_url, listitem=li, isFolder=True)


def addList_video(video):
    """
    ファイル一覧に動画ファイル情報を追加

    :param video: EPGStationの'api/recorded'で取得した動画情報を1つづつ
    :type video: dict
    """
    global server_url

    li = xbmcgui.ListItem(video['name'])

    thumbnailList = video.get('thumbnails',[])
    if len(thumbnailList) > 0: set_thumbnail(li, thumbnailId=thumbnailList[0])

    startdate = datetime.datetime.fromtimestamp(video['startAt'] / 1000)

    info = {
        'originaltitle': video['name'],
        'title': video['name'],
        'sorttitle': video['name'],
        'tvshowtitle': video['name'],
        'album':  video['name'],
        'year': startdate.strftime('%Y'),
        'date': startdate.strftime('%d.%m.%Y'),
        'aired': startdate.strftime('%Y-%m-%d'),
        'dateadded': startdate.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': (video['endAt'] - video['startAt']) / 1000,
    }

    try:
        # ジャンル
        if 'genre1' in video and video['genre1'] in GENRE1:
            # ジャンル1
            info['genre'] = GENRE1[video['genre1']]

            # ジャンル2
            if 'genre2' in video and video['genre1'] in GENRE2 and video['genre2'] in GENRE2[video['genre1']]:
                info['genre'] += ' / ' + GENRE2[video['genre1']][video['genre2']]

        # 詳細
        if 'description' in video and not 'extended' in video:
            info['plot'] = video['description']
            info['plotoutline'] = video['description']
        elif 'description' in video and 'extended' in video:
            info['plot'] = video['description'] + '\n\n' + video['extended']
            info['plotoutline'] = video['description']
    except:
        print 'error'

    li.setInfo('video', info)

    # メニューにファイル毎の再生項目を追加
    params = {'isDownload':False}
    menuList = []
    for file in video['videoFiles']:
        videourl = get_url(sys.argv[0], '', {'action':'play_video', 'recid':video['id'], 'vid':file['id']})
        menuList.append( ('再生 : '.decode('utf-8') + file['name'], 'PlayMedia(' + videourl + ')') )
    
    # デフォルトの再生ファイルを決定 (TODO: エンコード名を取得して優先順位を設定できるようにしたい)
    defaultType = 'encoded' if settings.getSettingInt('video_playtype') == 1 else 'ts'
    vid = 0
    for file in video['videoFiles']:
        if vid == 0:
            vid = file['id']
        elif file['type'] == defaultType:
            vid = file['id']

    menuList.append(('削除', 'RunScript(%s/delete.py, %d, %s)' % (settings.getAddonInfo('path'), video['id'], video['name'])))
    menuList.append(('更新', 'Container.Refresh'))
    li.addContextMenuItems(menuList)

    videourl = get_url(server_url, 'api/videos/' + str(vid), params)
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=videourl, listitem=li)


def play_video(recid, vid):
    """
    渡されたvidの動画ファイルを再生
    :param recid: str
    :param vid: str
    :return: None
    """
    # TODO: ListItemの取得処理がaddList_videoと完全にかぶっているので、
    #       引数で必要な情報を渡せるようにするか関数化したい。

    global server_url

    # 動画取得時のパラメータ
    params = {'isHalfWidth':True}

    # 動画一覧取得時
    urlInfo = urlutil.getUrlInfo(server_url)
    url = get_url(server_url, 'api/recorded/' + str(recid), params)
    request = urllib2.Request(url=url, headers=urlInfo["headers"])
    response = urllib2.urlopen(request)
    video = json.loads(response.read())

    # 動画ファイル情報を追加
    li = xbmcgui.ListItem(video['name'])

    thumbnailList = video.get('thumbnails',[])
    if len(thumbnailList) > 0: set_thumbnail(li, thumbnailId=thumbnailList[0])

    startdate = datetime.datetime.fromtimestamp(video['startAt'] / 1000)

    info = {
        'originaltitle': video['name'],
        'title': video['name'],
        'sorttitle': video['name'],
        'tvshowtitle': video['name'],
        'album':  video['name'],
        'year': startdate.strftime('%Y'),
        'date': startdate.strftime('%d.%m.%Y'),
        'aired': startdate.strftime('%Y-%m-%d'),
        'dateadded': startdate.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': (video['endAt'] - video['startAt']) / 1000,
    }

    try:
        # ジャンル
        if 'genre1' in video and video['genre1'] in GENRE1:
            # ジャンル1
            info['genre'] = GENRE1[video['genre1']]

            # ジャンル2
            if 'genre2' in video and video['genre1'] in GENRE2 and video['genre2'] in GENRE2[video['genre1']]:
                info['genre'] += ' / ' + GENRE2[video['genre1']][video['genre2']]

        # 詳細
        if 'description' in video and not 'extended' in video:
            info['plot'] = video['description']
            info['plotoutline'] = video['description']
        elif 'description' in video and 'extended' in video:
            info['plot'] = video['description'] + '\n\n' + video['extended']
            info['plotoutline'] = video['description']
    except:
        print 'error'

    params = {'isDownload':False}
    li.setPath( get_url(server_url, 'api/videos/' + str(vid), params) )
    li.setInfo('video', info)

    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(handle=ADDON_HANDLE, succeeded=True, listitem=li)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring:
    :return:
    """

    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring[1:]))

    # プラグインの引数にaction=XXXがあれば該当の処理、なければルール一覧表示
    if params:
        if params['action'] == 'list_videos': # 動画一覧表示
            list_videos(rule=params.get('rule',-1), genre=params.get('genre',-1), channel=params.get('channel',-1), offset=params.get('offset',0) )
        elif params['action'] == 'list_rules': # ルール一覧表示
            list_rules()
        elif params['action'] == 'list_genre': # ジャンル一覧表示
            list_genre()
        elif params['action'] == 'list_channels': # チャンネル一覧表示
            list_channels()
        elif params['action'] == 'select_list': # リスト選択表示
            select_list()
        elif params['action'] == 'play_video': # メニューから動画ID指定で再生
            play_video(params['recid'], params['vid'])
    else: # アクション未指定時は設定値に従う
        view = settings.getSettingInt('select_home')
        if view == '0':
            select_list()
        elif view == '1':
            list_rules()
        elif view == '2':
            list_genre()
        elif view == '3':
            list_channels()
        else:
            select_list()

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


if __name__ == '__main__':
    # web_pdb.set_trace()
    # 設定値読み込み
    server_url = settings.getSettingString('server_url')

    # URL未設定の場合は設定画面開く
    if not server_url:
        settings.openSettings()
        server_url = settings.getSettingString('server_url')
    
    router(sys.argv[2])
