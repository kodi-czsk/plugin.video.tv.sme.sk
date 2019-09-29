# -*- coding: utf-8 -*-
import urllib2,urllib,re,os
import xbmcplugin,xbmcgui,xbmcaddon
import datetime
import time
import elementtree.ElementTree as ET
import rfc822

__baseurl__ = 'https://video.sme.sk'
__addon__ = xbmcaddon.Addon('plugin.video.tv.sme.sk')
__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")
__scriptname__ = __addon__.getAddonInfo('name')
icon =  os.path.join( __cwd__, 'icon.png' )
nexticon = os.path.join( __cwd__, 'nextpage.png' )

def log(msg, level=xbmc.LOGDEBUG):
	if type(msg).__name__=='unicode':
		msg = msg.encode('utf-8')
	xbmc.log("[%s] %s"%(__scriptname__,msg.__str__()), level)

def logDbg(msg):
	log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
	log(msg,level=xbmc.LOGERROR)

def notifyErr(msg, timeout = 7000):
	xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__scriptname__, msg.encode('utf-8'), timeout, __addon__.getAddonInfo('icon')))
	logErr(msg)

def addLink(name,url,mode,iconimage,desc,duration,pub=""):
	logDbg("addLink(): '"+name+"' url='"+url+ "' img='"+iconimage+"' desc='"+desc+"' dur='"+duration+"' pub='"+pub+"'")
	u=sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8'))+"&desc="+urllib.quote_plus(desc.encode('utf-8'))
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": duration, "dateadded": pub} )
	liz.setProperty("IsPlayable", "true")
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok

def addDir(name,url,mode,iconimage,desc):
	logDbg("addDir(): '"+name+"' url='"+url+"' img='"+iconimage+"' desc='"+desc+"'")
	u=sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8'))+"&desc="+urllib.quote_plus(desc.encode('utf-8'))
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc} )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def getDuration(durstr):
	try:
		x = time.strptime(durstr,'%M:%S')
		return str(datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds())
	except:
		return "0"

def getDataFromUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

def getHtmlFromUrl(url):
	return getDataFromUrl(url).decode("utf-8")

def getXmlFromUrl(url):
	return getDataFromUrl(url).decode("utf-8")

def listCategories():
	logDbg("listCategories()")
	addDir(u'[B]Najnovšie videá[/B]',__baseurl__+'/rss',2,icon,'')
	addDir(u'[B]Spravodajstvo[/B]',__baseurl__+'/r/7026/spravodajstvo.html',3,icon,'')
	addDir(u'[B]Publicisticka[/B]',__baseurl__+'/r/7028/publicistika.html',3,icon,'')
	addDir(u'[B]Zábava[/B]',__baseurl__+'/r/7031/zabava.html',3,icon,'')
	addDir(u'[B]Zoznam relácií[/B]',__baseurl__+'/relacie/',1,icon,'')

def listLatest(url):
	logDbg("listLatest()")
	xml = ET.fromstring(getDataFromUrl(url))
	for i in xml.find('channel').findall('item'):
		addLink(i.find('title').text.strip().replace('(video)',''),
			i.find('link').text,
			5,
			i.find('enclosure').attrib['url'],
			i.find('description').text,
			"0",
			time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(rfc822.mktime_tz(rfc822.parsedate_tz(i.find('pubDate').text))))
			)

def listShows(url):
	logDbg("listShows()")
	httpdata = getHtmlFromUrl(url)
	items = re.compile(u'<div class=\"col-sm col-3-sm px-s px-m-mo\">.+?<a href="(.+?)" title="(.+?)" class="tvshows-item">.+?<img src="(.+?)"', re.DOTALL).findall(httpdata)
	for link,name,img in items:
		addDir(name,link,3,img,'')

def listEpisodes(url):
	logDbg("listEpisodes()")
	
	httpdata = getHtmlFromUrl(url)

	beg_idx=httpdata.find('class="video-row')
	end_idx=httpdata.find('id="js-paging"')
	data=httpdata[beg_idx:end_idx]
	
	pattern = re.compile('data-deep-tags=\"position-[0-9]+\" class=\"video-box-tile\".+?href=\"(.+?)\">.+?<img class=\"video-box-tile-img\" src=\"(.+?)\".+?>.+?<h2.*?>(.+?)</h2>.+?<span class=\"media-box-author.*?>(.+?)</span>.+?(?:(?:<time datetime=\"(.+?)\">)|(?:</a>.+?<a))', re.DOTALL)
	it = re.finditer(pattern,data)
	for item in it:
		link,img,title,authors,duration = item.groups()
		addLink(title.strip().replace('(video)',''),link,5,img,"",getDuration(duration))
	nextlink=re.compile('<link rel=\"next\" href=\"(.+?)\">', re.DOTALL).search(httpdata)
	if nextlink:
		if not nextlink.group(1).startswith('http'):
			url=__baseurl__+nextlink.group(1)
		else:
			url=nextlink.group(1)
		addDir(u'[B]Nasledujúce články[/B]',url,3,nexticon,'')
	else:
		logDbg('No next page.') 
	return None

def getVideoUrl(url):
	logDbg("getVideoUrl()")
	logDbg("\tPage url="+url)
	httpdata = getHtmlFromUrl(url)
	# try vimeo provider
	match = re.compile(r'data-direct-source=\"(.+?)"', re.DOTALL).search(httpdata)
	if match:
		logDbg("\tFound Vimeo direct URL: "+match.group(1))
		return match.group(1)
	else:
		# try youtube provider
		match = re.compile(r'<iframe src=\"//www\.youtube\.com/embed/(.+?)\"', re.DOTALL).search(httpdata)
		if match:
			logDbg("\tFound YouTube video ID: "+match.group(1))
			return 'plugin://plugin.video.youtube/play/?video_id='+match.group(1)
		else:
			# try youtube provider different way
			match = re.compile(r'<iframe src=\"//(.*?sme\.sk/vp/.+?)\"', re.DOTALL).search(httpdata)
			if match:
				return getVideoUrl('http://'+match.group(1))
			else:
				notifyErr(u'Neznámy zdroj videa!')
	return None

def playEpisode(url):
	logDbg("playEpisode()")
	logDbg("\tur="+url)
	url=getVideoUrl(url)
	if url:
		liz = xbmcgui.ListItem(path=url, iconImage="DefaultVideo.png")
		liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc} )
		liz.setProperty('IsPlayable', "true")
		xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=(url!=None), listitem=liz)
	return

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

params=get_params()
url=None
name=None
desc=None
mode=None

try:
	url=urllib.unquote_plus(params["url"])
except:
	pass
try:
	name=urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode=int(params["mode"])
except:
	pass
try:
	desc=urllib.unquote_plus(params["desc"])
except:
	pass

logDbg("Mode: "+str(mode))
logDbg("URL: "+str(url))
logDbg("Name: "+str(name))
logDbg("Desc: "+str(desc))

if mode==None or url==None or len(url)<1:
	listCategories()

elif mode==1:
	listShows(url)

elif mode==2:
	listLatest(url)

elif mode==3:
	listEpisodes(url)

elif mode==5:
	playEpisode(url)
	sys.exit(0)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
