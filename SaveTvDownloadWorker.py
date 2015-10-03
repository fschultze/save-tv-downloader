import socket, urllib, os, sys, commands, time, datetime, re, glob, logging

from SaveTvRenamer import SaveTvRenamer


class SaveTvDownloadWorker:
    """
    Inspired by: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/83208
    """
    
    def __init__(self, pParent, pUrl, dstpath, logger):
        self.dnldUrl = pUrl
        self.parent = pParent
        #self.renamer = SaveTvRenamer(logger)
        if (dstpath is not None):
            self.dstpath = dstpath.encode(sys.getfilesystemencoding())
        else:
            self.dstpath = None

        self.logger = logger
            
    def download(self):
        myUrlclass = urllib.FancyURLopener()
        socket.setdefaulttimeout(30)

        self.logger.debug("Opening " + self.dnldUrl + " ")
        for i in range(1,4):
            try:
                webPage = myUrlclass.open(self.dnldUrl)
                fileLength = long(webPage.headers['Content-Length'])
                break
            except:
                if (i == 4):
                    self.logger.error("Failed to open " + self.dnlUrl)
                    return None
                    
                continue

        try:
            contentDisposition = webPage.headers['Content-Disposition']
            filename = contentDisposition.split("filename=")[1]
        except:
            filename = self.dnldUrl.split("/")
            filename = filename[len(filename)-1]
        
        webPage.close()    
        #import pdb; pdb.set_trace()

        self.originalFilename = filename
        
        if re.search("Sendung entfallt", filename) is not None:
            return True
        
        # save.tv seems to offer files for other users. Check and only accept files containing our username.
        if (self.parent.SAVETV_USERID not in filename):
            self.logger.debug("File %s is not for me." %(filename))
            return False

        #self.logger.debug("Searching for " + filename)
        #path = self.renamer.getname(filename)
        path = self.dstpath
        
        if (path is None):
            self.logger.debug(filename + " is not a TV show")
            fname = filename.replace("_", " ")
            m = re.search("(.*)" + self.parent.SUFFIX, fname)
            
            if (m is not None):
                fname = m.group(1).rstrip() + ".mp4"
            else:
                self.logger.debug(fname + " didn't match")

            path = self.parent.MOVIE_DIRECTORY + fname
        else:
            s = re.search("^(.+\d+x\d\d)", path)
            if (s is not None):
                namepart = s.group(1)
                fnames = glob.glob(namepart + "*.*")
                namepart = namepart.replace("german-tv", "dvd")
                fnames.extend(glob.glob(namepart + "*.*"))
                for f in fnames:
                    self.logger.debug(f)
                    if (f.endswith(".mp4") or f.endswith(".mkv") or f.endswith(".avi")):
                        self.logger.info("File " + path + " already exists. Deleting from server")
                        return True
                        
        if (os.path.isfile(path)):
            self.logger.debug("File %s already downloaded." %(filename))
            return True

        #m = re.search("(\d\d\d\d-\d\d-\d\d_\d\d\d\d)", filename)
        #datestr = m.group(1)        
        #timestamp = time.strptime(datestr, "%Y-%m-%d_%H%M")
        #recordingtime = datetime.datetime.fromtimestamp(time.mktime(timestamp))
        #delta = datetime.datetime.now() - recordingtime
        
        #if delta < datetime.timedelta(hours=24):
        #    self.logger.debug ("File " + filename + " is too new to be ad-free")
        #    return False
        
        temppath = path + ".part"

        self.logger.debug("Downloading " + filename + " to " + path)

        alreadyDownloadedBytes = long(self.getAlreadyDownloadedBytes(temppath))
        if alreadyDownloadedBytes == fileLength:
            self.logger.debug("%s already downloaded, size: %s" %(filename, alreadyDownloadedBytes))
            #self.markFileAsFinished(filename, self.originalFilename)
            os.rename(temppath, path)
            return True
        
        if alreadyDownloadedBytes >= fileLength:
            self.logger.debug("%s already present, but size is too big (file: %s, web: %s)" %(filename, alreadyDownloadedBytes, fileLength))
            try:
                os.remove(filename)
            except Exception as e:
                self.logger.error(e)
                return False

        self.logger.debug("Downloading %s with size %s (already downloaded: %s)" %(filename, fileLength, alreadyDownloadedBytes))

        #return False

        try:
            wgetResult = commands.getstatusoutput("curl -s -S -o \"%s\" \"%s\"" %(temppath, self.dnldUrl))
            self.logger.debug (wgetResult)
        except:
            return False

        #sys.stdout.flush()

        # Wenn Datei komplett, ".part" entfernen
        if (self.getAlreadyDownloadedBytes(temppath) == fileLength):
            os.rename(temppath, path)
            return True
            
        return False
        
    def getAlreadyDownloadedBytes(self, path):
        if os.path.exists(path):
            existSize = os.path.getsize(path)
            return existSize
        return 0

    def updateXBMC(self, series):
        hosts = ['macmini', 'first', 'raspberry-regina', 'raspberry-hanni']
        for host in hosts:
            try:
                curlResult = commands.getstatusoutput("curl -H \"Accept: application/json\" -H \"Content-type: application/json\" -d '{\"id\":5,\"jsonrpc\":\"2.0\",\"method\":\"VideoLibrary.Scan\",\"params\":{\"directory\":\"nfs://firefly/mnt/storage/tvseries/geman-tv/\"+series}}' http://"+host+":8080/jsonrpc")
            except:
                continue
                
    #def removePartEndingFromFileName(self, filename, originalFilename):
    #    os.rename(self.download_directory+filename, self.download_directory+originalFilename)

if __name__ == "__main__":
    std = SaveTvDownloadWorker("http://80.190.216.181/25966898_CB5E3E716DE63A1ED50B48A0A6F415CB/?m=dl", "/tmp/")
    std.download()
