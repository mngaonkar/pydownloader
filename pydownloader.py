import urllib2
import urllib
import re
import sys
import os
from threading import Thread, Lock, Event

class Task(Thread):
    _obj = None
    
    def __init__(self, obj, args = None):
        self._obj = obj
        self._args = args
        self._flag_stop = Event()
        self._flag_pause = Event()
        self._flag_resume = Event()
        super(Task, self).__init__()
        
        
    def run(self):
        print('starting task...')
        if self._obj: 
            self._obj.run()
            

class PyDownloader():
    
    CHUNK_SIZE = 1024 * 1024
    DOWNLOAD_DIR = '.'
    
    def __init__(self):
        self.task = None
        self.linkList = []
        self.link = None
        self.urlName = ''
        self.chunkSize = self.CHUNK_SIZE
        self.downloadPath = self.DOWNLOAD_DIR
        self.fileType = 'mp4'
        self.keyword = 'test'
        self.webData = ''
        self.totalFileCount = 0
        self.downloadedFileCount = 0
        self.currentDownloadFile = 'None'
        self.currentDownloadProgress = 0
        self.currentDownloadSize = 0

        
    def resetStats(self):
        self.webData = ''
        self.totalFileCount = 0
        self.downloadedFileCount = 0
        self.currentDownloadFile = 'None'
        self.currentDownloadProgress = 0
        self.currentDownloadSize = 0

        
    def getDownloadLinks(self):
        return self.linkList
        
        
    def getTaskStatus(self):
        if self.task and self.task.isAlive():
            return "active"
        else:
            return "stopped"
        
        
    def setChunkSize(self, chunkSize):
        if chunkSize != None and chunkSize != '':
            self.chunkSize = chunkSize
        else:
            self.chunkSize = self.CHUNK_SIZE
        
        
    def setFileType(self, fileType):
        if fileType != None:
            self.fileType = fileType
        
    
    def setKeyword(self, keyword):
        if keyword != None:
            self.keyword = keyword
        
        
    def setDownloadPath(self, path):
        if path != None and path != '':
            self.downloadPath = path
        else:
            self.downloadPath = self.DOWNLOAD_DIR
        
        
    def stop(self):
        if self.task:
            self.task._flag_stop.set()
            return ({'status':'ok', 'response':{'error':'task stop request received'}})
        else:
            return ({'status':'ok', 'response':{'error':'task not started'}})
            
            
    def start(self):
        if self.getTaskStatus() != 'active':
            self.resetStats()
            self.task = Task(self)
            self.task.start()
            return ({'status':'ok', 'response':{'error':'task started'}})
        else:
            return ({'status':'ok', 'response':{'error':'task is already active'}})
        
        
    def run(self):
        """Download task """
        try:
            if self.keyword != '' or self.fileType != '':
                print('parsing web link...')
                self.webData = self.link.read()
                self.getLinks()
            else:
                print('downloading web link...')
                self.linkList.append(self.urlName)
                self.totalFileCount = 1
            
            if len(self.linkList):
                print('\n'.join([urllib.unquote(i) for i in self.linkList]))
            print('\n---------------------------------------------------------')
            print('total links = %d' % self.totalFileCount)
            print('\n---------------------------------------------------------')
            ret = self.downloadLinks()
            print(ret)
            #self.linkList = [urllib.unquote(i) for i in self.linkList]
        except Exception as e:
            raise
        
        
    def getLinks(self):
        """Get all download links """
        self.linkList = []
        if self.keyword != '' and self.fileType != '':
            self.linkList = re.findall(r'<a\s+href\s*=\s*\"(.*%s.*\.%s)\s*\"' % \
                (self.keyword, self.fileType), self.webData, re.I)
        elif self.keyword == '' and self.fileType != '':
            self.linkList = re.findall(r'<a\s+href\s*=\s*\"(.+\.%s)\s*\"' % \
                (self.fileType), self.webData, re.I)
        elif self.keyword != '' and self.fileType == '':
            self.linkList = re.findall(r'<a\s+href\s*=\s*\"(.*%s.*\..+)\s*\"' % \
                (self.keyword), self.webData, re.I)
        
        self.totalFileCount = len(self.linkList)
        
        
    def getURLInfo(self, url):
        info = {}
        
        request = urllib2.Request(url)
        link = urllib2.urlopen(request)
        if link.info()['accept-ranges'] == 'bytes':
            info['resumeSupport'] = True
        else:
            info['resumeSupport'] = False
            
        info['fileSize'] = link.info()['content-length']
        info['date'] = link.info()['date']
        
        return info
        
        
    def downloadLinks(self):
        """Download all the links sequentially"""
        for item in self.linkList:
            self.currentDownloadProgress = 0
            sizeCompleted = 0
            
            if 'http' not in item:
                self.currentDownloadFile = self.urlName + item
            else:
                self.currentDownloadFile = item
           
            try:
                localFileName = self.downloadPath + '/' + urllib.unquote(item).split('/')[-1]
                
                urlInfo = self.getURLInfo(self.currentDownloadFile)
                if urlInfo['resumeSupport']: 
                    print("server file resume supported")
                else:
                    print("server file resume NOT supported")
                
                if os.path.isfile(localFileName) and urlInfo['resumeSupport']:
                    sizeCompleted = os.path.getsize(localFileName)
                    if sizeCompleted >= int(urlInfo['fileSize']):
                        self.downloadedFileCount += 1
                        continue
                    self.fd = open(localFileName, 'ab+')
                    
                    self.fd.seek(sizeCompleted)
                else:
                    self.fd = open(localFileName, 'wb')
                
                request = urllib2.Request(self.currentDownloadFile)
                if urlInfo['resumeSupport']:
                    request.headers['range'] = 'bytes=%s-' % (sizeCompleted)
                self.link = urllib2.urlopen(request)
                self.fileSize = int(urlInfo['fileSize'])
                self.currentDownloadProgress = int((sizeCompleted / float(self.fileSize)) * 100)
                self.currentDownloadSize = self.fileSize
                
                print('downloading %s [%d bytes]...' % (urllib.unquote(item), self.fileSize))
                
                while True:
                    if self.task._flag_stop.is_set():
                        self.fd.close()
                        return ({'status':'success', 'response':{'error':'user stopped service'}})
                    chunk = self.link.read(self.chunkSize)
                    if not chunk: 
                        break
                    else:
                        self.fd.write(chunk)
                        sizeCompleted += self.chunkSize
                        self.currentDownloadProgress = int((sizeCompleted / float(self.fileSize)) * 100)
                        if self.currentDownloadProgress > 100: self.currentDownloadProgress = 100
                        sys.stdout.write('\r%3d%%' % (self.currentDownloadProgress))
                        sys.stdout.flush()
                
                self.fd.close()
                self.downloadedFileCount += 1
                print(' (%d/%d) downloaded\n' % (self.downloadedFileCount, self.totalFileCount))
                
            except Exception as e:
                return ({'status':'error', 'response':{'error':'%s' % str(e)}})
        return ({'status':'success', 'response':{'file_count':'%d' % self.downloadedFileCount}})
        
        
    def setURL(self, url):
        self.url = url
        try:
            self.link = urllib2.urlopen(url)
            self.urlName = self.link.geturl()
            return ({'status':'ok', 'response':{'url':'%s' % self.urlName}})
        except Exception as e:
            return ({'status':'error', 'response':{'error':'%s' % str(e)}})
        