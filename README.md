PyDownloader
============
PyDownloader is a Python module to download files over HTTP. It has two modes of operations namely direct and scrap mode.
In direct mode, simply set the download URL with setURL() and download file using start(). Note, the download task is started
in a seprate thread hence it is necessary for the calling application to wait till download is complete.
In scrap mode, set the URL with setURL(). This mode of operation requires a web page rather than a donwload file. 
Then set the keyword to be searched with setKeyword() and file type with setFileType(). 
It will scrape the URL for all download links having keyword in file name and type as specified by user. 
All the matching links will be downloaded sequentially.


Example Usage
=============
from pydownloader import PyDownloader

app = PyDownloader()
app.setChunkSize(1024) # set download chunk size
app.setKeyword('test') # set keyword to be searched on web link
app.setFileType('mp3') # set type of files to be downloaded
app.setDownloadPath('./downloads') # set download directory

ret = app.setURL(URL)
if ret['status'] == 'ok':
  ret = app.start()
else:
  print(ret['response']['error'])
