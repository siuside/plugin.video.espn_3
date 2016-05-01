#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris
# Released under GPL(v2)

import urllib, urllib2, xbmcplugin, xbmcaddon, xbmcgui, os, random, string, re
import time
import mechanize
from adobe import ADOBE
from globals import *
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, SoupStrainer
import base64

import player_config
import events
import util
from espn import ESPN
from mso_provider import get_mso_provider
from user_details import UserDetails

import cookielib

LIVE_EVENTS_MODE = 1
PLAY_MODE = 6

cj = cookielib.LWPCookieJar()
channels = ''

def CATEGORIES():
    include_premium = selfAddon.getSetting('ShowPremiumChannels') == 'true'
    channel_list = events.get_channel_list(include_premium)
    curdate = datetime.utcnow()
    upcoming = int(selfAddon.getSetting('upcoming'))+1
    days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
    addDir(translation(30029), events.get_live_events_url(channel_list), LIVE_EVENTS_MODE, defaultlive)
    addDir(translation(30030), events.get_upcoming_events_url(channel_list) + '&endDate='+days+'&startDate='+curdate.strftime("%Y%m%d"), 2,defaultupcoming)
    enddate = '&endDate='+ (curdate+timedelta(days=1)).strftime("%Y%m%d")
    replays1 = [5,10,15,20,25]
    replays1 = replays1[int(selfAddon.getSetting('replays1'))]
    start1 = (curdate-timedelta(days=replays1)).strftime("%Y%m%d")
    replays2 = [10,20,30,40,50]
    replays2 = replays2[int(selfAddon.getSetting('replays2'))]
    start2 = (curdate-timedelta(days=replays2)).strftime("%Y%m%d")
    replays3 = [30,60,90,120]
    replays3 = replays3[int(selfAddon.getSetting('replays3'))]
    start3 = (curdate-timedelta(days=replays3)).strftime("%Y%m%d")
    replays4 = [60,90,120,240]
    replays4 = replays4[int(selfAddon.getSetting('replays4'))]
    start4 = (curdate-timedelta(days=replays4)).strftime("%Y%m%d")
    startAll = (curdate-timedelta(days=365)).strftime("%Y%m%d")
    addDir(translation(30031)+str(replays1)+' Days', events.get_replay_events_url(channel_list) +enddate+'&startDate='+start1, 2, defaultreplay)
    addDir(translation(30031)+str(replays2)+' Days', events.get_replay_events_url(channel_list) +enddate+'&startDate='+start2, 2, defaultreplay)
    addDir(translation(30031)+str(replays3)+' Days', events.get_replay_events_url(channel_list) +enddate+'&startDate='+start3, 2, defaultreplay)
    addDir(translation(30031)+str(replays3)+'-'+str(replays4)+' Days', events.get_replay_events_url(channel_list) +'&endDate='+start3+'&startDate='+start4, 2, defaultreplay)
    addDir(translation(30032), events.get_replay_events_url(channel_list) +enddate+'&startDate='+startAll, 2, defaultreplay)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def LISTNETWORKS(url,name):
    pass

def LISTSPORTS(url,name):
    data = get_html(url)
    #data = '<?xml version="1.0" encoding="CP1252"?>'+data
    SaveFile('videocache.xml', data, ADDONDATA)
    if 'action=replay' in url:
        image = defaultreplay
    elif 'action=upcoming' in url:
        image = defaultupcoming
    else:
        image = defaultimage
    addDir(translation(30034), url, 1, image)
    sports = []
    events = BeautifulSoup(data, 'html.parser', parse_only = SoupStrainer('event'))
    for event in events.find_all('event'):
        sport = event.find('sportdisplayvalue').string.title().encode('utf-8')
        if sport not in sports:
            sports.append(sport)
    for sport in sports:
        addDir(sport, url, 3, image)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def INDEXBYSPORT(url,name):
    INDEX(url,name,bysport=True)

def INDEX(url,name,bysport=False):
    if 'action=live' in url:
        data = events.get_events(url)
        #data = '<?xml version="1.0" encoding="CP1252"?>'+data
    else:
        data = ReadFile('videocache.xml', ADDONDATA)
        data_soup = BeautifulSoup(data, 'html.parser')
        data = data_soup.findAll('event')
    for event in data:
        sport = event.find('sportdisplayvalue').string.encode('utf-8')
        desktopStreamSource = event.find('desktopstreamsource').string
        if name <> sport and bysport == True:
            continue
        elif desktopStreamSource == 'HLS' and StreamType == 'true':
            pass
        else:
            ename = event.find('name').string
            eventid = event.get('id')
            simulcastAiringId = event.find('simulcastairingid').string
            desktopStreamSource = event.find('desktopstreamsource').string
            bamContentId = event.get('bamcontentid')
            bamEventId = event.get('bameventid')
            networkid = event.find('networkid').string
            if networkid is not None:
                network = player_config.get_network(networkid)
            authurl = eventid
            authurl += ','+bamContentId
            authurl += ','+bamEventId
            authurl += ','+simulcastAiringId
            authurl += ','+desktopStreamSource
            authurl += ','+networkid
            sport2 = event.find('sport').string.title()
            if sport <> sport2:
                sport += ' ('+sport2+')'
            league = event.find('league').string
            location = event.find('site').string
            fanart = event.find('large').string
            fanart = fanart.split('&')[0]
            thumb = event.find('large').string
            mpaa = event.find('parentalrating').string
            starttime = int(event.find('starttimegmtms').string)/1000
            eventedt = int(event.find('starttime').string)
            etime = time.strftime("%I:%M %p",time.localtime(float(starttime)))
            endtime = int(event.find('endtimegmtms').string)/1000
            start = time.strftime("%m/%d/%Y %I:%M %p",time.localtime(starttime))
            aired = time.strftime("%Y-%m-%d",time.localtime(starttime))
            date = time.strftime("%m/%d/%Y",time.localtime(starttime))
            udate = time.strftime("%m/%d",time.localtime(starttime))
            now = datetime.now().strftime('%H%M')
            etime24 = time.strftime("%H%M",time.localtime(starttime))
            aspect_ratio = event.find('aspectratio').string
            length = str(int(round((endtime - time.time()))))
            title_time = etime
            if 'action=live' in url and now > etime24:
                color = str(selfAddon.getSetting('color'))
            elif 'action=live' in url:
                color = '999999'
            else:
                color = 'E0E0E0'
                length = str(int(round((endtime - starttime))))
                title_time = ' - '.join((udate, etime))

            channel_color = 'CC0000'

            ename = '[COLOR=FF%s]%s[/COLOR] [COLOR=FFB700EB]%s[/COLOR] [COLOR=FF%s]%s[/COLOR]' % (channel_color, network, title_time, color, ename)

            length_minutes = int(length) / 60

            end = event.find('summary').string
            if end is None or len(end) == 0:
                end = event.find('caption').string

            if end is None:
                end = ''
            end += '\nNetwork: ' + network

            plot = ''
            if sport <> None and sport <> ' ':
                plot += 'Sport: '+sport+'\n'
            if league <> None and league <> ' ':
                plot += 'League: '+league+'\n'
            if location <> None and location <> ' ':
                plot += 'Location: '+location+'\n'
            if start <> None and start <> ' ':
                plot += 'Air Date: '+start+'\n'
            if length <> None and length <> ' ' and 'action=live' in url:
                plot += 'Duration: Approximately '+ str(length_minutes)+' minutes remaining'+'\n'
            elif length <> None and length <> ' ' and ('action=replay' in url or 'action=upcoming' in url):
                plot += 'Duration: '+ str(length_minutes) +' minutes'+'\n'
            plot += end
            infoLabels = {'title': ename,
                          'genre':sport,
                          'plot':plot,
                          'aired':aired,
                          'premiered':aired,
                          'duration':length,
                          'studio':network,
                          'mpaa':mpaa,
                          'videoaspect' : aspect_ratio}
            if 'action=upcoming' in url:
                mode = 5
            else:
                mode = PLAY_MODE
            addLink(ename, authurl, mode, fanart, fanart, infoLabels=infoLabels)
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def PLAYESPN3(url):
    PLAY(url,'n360')

def PLAY_PROTECTED_CONTENT(url):

    if not check_user_settings():
        return

    data = ReadFile('userdata.xml', ADDONDATA)
    soup = BeautifulSoup(data, 'html.parser')
    affiliateid = soup('name')[0].string
    swid = soup('personalization')[0]['swid']
    identityPointId = affiliateid+':'+swid

    # Split up the url so they can be used as needed
    url_split = url
    url_split = url.split(',')
    eventid = str(url_split[0])
    contentId = str(url_split[1])
    eventId = str(url_split[2])
    simulcastAiringId = str(url_split[3])
    streamType = str(url_split[4])
    networkid = str(url_split[5])

    requestor = ESPN()
    mso_provider = get_mso_provider(selfAddon.getSetting('provider'))
    user_details = UserDetails(selfAddon.getSetting('username'), selfAddon.getSetting('password'))


    adobe = ADOBE(requestor, mso_provider, user_details)
    media_token = adobe.GET_MEDIA_TOKEN()
    resource_id = requestor.get_resource_id()

    start_session_url = player_config.get_start_session_url()
    start_session_url += 'affiliate='+affiliateid
    start_session_url += '&channel='+player_config.get_network(networkid)
    start_session_url += '&partner=watchespn'
    start_session_url += '&playbackScenario=HTTP_CLOUD_MOBILE'
    start_session_url += '&v=2.0.0'
    start_session_url += '&platform=android_tablet'
    start_session_url += '&sdkVersion=1.1.0'
    start_session_url += '&token='+urllib.quote(base64.b64encode(media_token))
    start_session_url += '&resource=' + urllib.quote(base64.b64encode(resource_id))
    start_session_url += '&simulcastAiringId='+simulcastAiringId
    start_session_url += '&tokenType=ADOBEPASS'

    xbmc.log('ESPN3: start_session_url: ' + start_session_url)
    tree = util.get_url_as_xml_soup(start_session_url)
    authstatus = tree.find('auth-status')
    blackoutstatus = tree.find('blackout-status')
    if not authstatus.find('successstatus'):
        if not authstatus.find('notauthorizedstatus'):
            if authstatus.find('errormessage').string:
                dialog = xbmcgui.Dialog()
                import textwrap
                errormessage = authstatus.find('errormessage').string
                try:
                    errormessage = textwrap.fill(errormessage, width=50).split('\n')
                    dialog.ok(translation(30037), errormessage[0],errormessage[1],errormessage[2])
                except:
                    dialog.ok(translation(30037), errormessage[0])
                return
    if not blackoutstatus.find('successstatus'):
        if blackoutstatus.find('errormessage').string:
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30040), blackoutstatus.find('errormessage').string)
            return
    pkan = tree.find('pkanjar').string
    # FFMPEG does not support hds so use hls
    smilurl = tree.find('hls-backup-url').string
    xbmc.log('ESPN3:  smilurl: '+smilurl)
    xbmc.log('ESPN3:  streamType: '+streamType)
    if smilurl == ' ' or smilurl == '':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30038),translation(30039))
        return

    finalurl = smilurl
    ua = urllib.quote('VisualOn OSMP+ Player(Linux;Android;WatchESPN/1.0_Handset)')
    finalurl = finalurl + '|User-Agent=' + ua + '&Cookie=_mediaAuth=' + urllib.quote(base64.b64encode(pkan))
    print finalurl
    item = xbmcgui.ListItem(path=finalurl)
    return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def PLAY_FREE_CONTENT(url):
    data = ReadFile('userdata.xml', ADDONDATA)
    soup = BeautifulSoup(data, 'html.parser')
    affiliateid = soup('name')[0].string
    swid = soup('personalization')[0]['swid']
    identityPointId = affiliateid+':'+swid

    # Split up the url so they can be used as needed
    url_split = url
    url_split = url.split(',')
    eventid = str(url_split[0])
    contentId = str(url_split[1])
    eventId = str(url_split[2])
    simulcastAiringId = str(url_split[3])
    streamType = str(url_split[4])

    pk = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(51)])
    pkan = pk + ('%3D')
    config = 'https://espn.go.com/watchespn/player/config'
    data = get_html(config)
    networks = BeautifulSoup(data, 'html.parser', parse_only = SoupStrainer('network'))
    for network in networks:
        if 'n360' == network['id']:
            playedId = network['playerid']
            cdnName = network['defaultcdn']
            channel = network['name']
            if streamType == 'HLS':
                networkurl = 'http://broadband.espn.go.com/espn3/auth/watchespn/startSession?v=1.5'
            elif streamType == 'HDS' or streamType == 'RTMP':
                networkurl = 'https://espn-ws.bamnetworks.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1'
            authurl = authurl = networkurl
            if '?' in authurl:
                authurl +='&'
            else:
                authurl +='?'

            if streamType == 'HLS':
                authurl += 'affiliate='+affiliateid
                authurl += '&cdnName='+cdnName
                authurl += '&channel='+channel
                authurl += '&playbackScenario=FMS_CLOUD'
                authurl += '&pkan='+pkan
                authurl += '&pkanType=SWID'
                authurl += '&eventid='+eventid
                authurl += '&simulcastAiringId='+simulcastAiringId
                authurl += '&rand='+str(random.randint(100000,999999))
                authurl += '&playerId='+playedId
            elif streamType == 'HDS' or streamType == 'RTMP':
                authurl += 'identityPointId='+affiliateid
                authurl += '&cdnName='+cdnName
                authurl += '&channel='+channel
                authurl += '&playbackScenario=FMS_CLOUD'
                authurl += '&partnerContentId='+eventid
                authurl += '&eventId='+eventId
                authurl += '&contentId='+contentId
                authurl += '&rand='+str(random.randint(100000,999999))
                authurl += '&playerId='+playedId
            html = get_html(authurl)
            tree = BeautifulSoup(html, 'html.parser')
            authstatus = tree.find('auth-status')
            blackoutstatus = tree.find('blackout-status')
            if not authstatus.find('successstatus'):
                if not authstatus.find('notauthorizedstatus'):
                    if authstatus.find('errormessage').string:
                        dialog = xbmcgui.Dialog()
                        import textwrap
                        errormessage = authstatus.find('errormessage').string
                        try:
                            errormessage = textwrap.fill(errormessage, width=50).split('\n')
                            dialog.ok(translation(30037), errormessage[0],errormessage[1],errormessage[2])
                        except:
                            dialog.ok(translation(30037), errormessage[0])
                        return
                else:
                    if not blackoutstatus.find('successstatus'):
                        if blackoutstatus.find('blackout').string:
                            dialog = xbmcgui.Dialog()
                            dialog.ok(translation(30040), blackoutstatus.find('blackout').string)
                            return
            #streamType = tree.find('streamtype').string
            smilurl = tree.find('url').string
            #xbmc.log('ESPN3:  smilurl: '+smilurl)
            #xbmc.log('ESPN3:  streamType: '+streamType)
            if smilurl == ' ' or smilurl == '':
                dialog = xbmcgui.Dialog()
                dialog.ok(translation(30037), translation(30038),translation(30039))
                return

            if streamType == 'HLS':
                finalurl = smilurl
                item = xbmcgui.ListItem(path=finalurl)
                return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

            elif streamType == 'HDS' or streamType == 'RTMP':
                auth = smilurl.split('?')[1]
                smilurl += '&rand='+str(random.randint(100000,999999))

                #Grab smil url to get rtmp url and playpath
                html = get_html(smilurl)
                soup = BeautifulSoup(html, 'html.parser')
                rtmp = soup.findAll('meta')[0]['base']
                # Live Qualities
                #     0,     1,     2,      3,      4
                # Replay Qualities
                #            0,     1,      2,      3
                # Lowest, Low,  Medium, High,  Highest
                # 200000,400000,800000,1200000,1800000
                playpath=False
                if selfAddon.getSetting("askquality") == 'true':
                    streams = soup.findAll('video')
                    quality=xbmcgui.Dialog().select(translation(30033), [str(int(stream['system-bitrate'])/1000)+'kbps' for stream in streams])
                    if quality!=-1:
                        playpath = streams[quality]['src']
                    else:
                        return
                if 'ondemand' in rtmp:
                    if not playpath:
                        playpath = soup.findAll('video')[int(selfAddon.getSetting('replayquality'))]['src']
                    finalurl = rtmp+'/?'+auth+' playpath='+playpath
                elif 'live' in rtmp:
                    if not playpath:
                        select = int(selfAddon.getSetting('livequality'))
                        videos = soup.findAll('video')
                        videosLen = len(videos)-1
                        if select > videosLen:
                            select = videosLen
                        playpath = videos[select]['src']
                    finalurl = rtmp+' live=1 playlist=1 subscribe='+playpath+' playpath='+playpath+'?'+auth
                item = xbmcgui.ListItem(path=finalurl)
                return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def check_user_settings():
    mso_provider = get_mso_provider(selfAddon.getSetting('provider'))
    username = selfAddon.getSetting('username')
    password = selfAddon.getSetting('password')
    if mso_provider is None:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30100))
        return False
    if username is None:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30110))
        return False
    if password is None:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30120))
        return False
    return True


def PLAY(url):
    xbmc.log('ESPN3:  url: '+ url)
    url_split = url.split(',')
    networkid = str(url_split[5])
    xbmc.log('ESPN3: networkid ' + networkid)
    if networkid == 'n360':
        PLAY_FREE_CONTENT(url)
    else:
        PLAY_PROTECTED_CONTENT(url)


def saveUserdata():
    userdata1 = 'http://broadband.espn.go.com/espn3/auth/watchespn/userData?format=xml'
    data1 = get_html(userdata1)
    SaveFile('userdata.xml', data1, ADDONDATA)
    soup = BeautifulSoup(data1, 'html.parser')
    checkrights = 'http://broadband.espn.go.com/espn3/auth/espnnetworks/user'

def get_html(url):
    try:
        xbmc.log('ESPN3:  get_html: '+url)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:38.0) Gecko/20100101 Firefox/38.0')]
        usock = opener.open(url)
        response = usock.read()
        #xbmc.log('ESPN3:  get_response: '+response)
        usock.close()
        return response
    except:
        xbmc.log('ESPN3:  get_response: Could not open URL: '+url)
        return False

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

def SaveFile(filename, data, dir):
    path = os.path.join(dir, filename)
    try:
        file = open(path,'w')
    except:
        file = open(path,'w+')
    file.write(data)
    file.close()

def ReadFile(filename, dir):
    path = os.path.join(dir, filename)
    if filename == 'userdata.xml':
        try:
            file = open(path,'r')
        except:
            saveUserdata()
            file = open(path,'r')
    else:
        file = open(path,'r')
    return file.read()

def addLink(name, url, mode, iconimage, fanart=False, infoLabels=False):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name.encode('utf-8'))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)

    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    liz.setIconImage(iconimage)
    if not fanart:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=False):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name.encode('utf-8'))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if not fanart:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = get_params()
url = None
name = None
mode = None
cookie = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

xbmc.log("Mode: " + str(mode))
xbmc.log("URL: " + str(url))
xbmc.log("Name: " + str(name))

if mode == None or url == None or len(url) < 1:
    xbmc.log("Generate Main Menu")
    CATEGORIES()
elif mode == LIVE_EVENTS_MODE:
    xbmc.log("Indexing Videos")
    INDEX(url,name)
elif mode == 2:
    xbmc.log("List sports")
    LISTSPORTS(url,name)
elif mode == 3:
    xbmc.log("Index by sport")
    INDEXBYSPORT(url,name)
elif mode == PLAY_MODE:
    PLAY(url)
elif mode == 5:
    xbmc.log("Upcoming")
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))


