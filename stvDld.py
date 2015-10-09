import os
import re
import sys
import ConfigParser
import atexit
import logging
import subprocess
import glob

from SaveTvEntity import SaveTvEntity
from SaveTvDownloadWorker import SaveTvDownloadWorker
from SaveTvRenamer import SaveTvRenamer

class SaveTvDownloader:
    def readConfiguration(self):
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/savetv.cfg')
        
        self.SAVETV_USERNAME = config.get('SaveTV', 'Benutzername')
        self.SAVETV_USERID = config.get('SaveTV', 'UserId')
        self.SAVETV_PASSWORD = config.get('SaveTV', 'Passwort')
        self.MOVIE_DIRECTORY = os.path.normpath(config.get('System', 'MovieDir')) + os.sep
        self.TVSHOW_DIRECTORY = os.path.normpath(config.get('System', 'TvShowDir')) + os.sep
        self.DELETE_AFTER_DOWNLOAD = config.getboolean('Optionen', 'DeleteAfterDownload') 
        self.SUFFIX = config.get('Optionen', 'FileNameSuffix')
        self.SHOWS = []
        self.logger = logging.getLogger('SaveTvDownloader')

        handler = logging.FileHandler('./savetv.log')
        #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        #handler.setFormatter(formatter)
        self.logger.addHandler(handler) 
        self.logger.setLevel(logging.DEBUG)
        
        for dir in os.listdir(self.TVSHOW_DIRECTORY):
            if (os.path.isdir(self.TVSHOW_DIRECTORY + dir)):
                #print "Adding TV show: " + dir;
                self.SHOWS.append(dir)

    def doDownload(self):
        svte = SaveTvEntity(self.SAVETV_USERNAME, self.SAVETV_PASSWORD, self.logger)

        if svte.initialiseLogin():
            availableRecordings = svte.fetchDownloadableTelecaseIds()
            #dlLinks = svte.fetchDownloadableTelecaseIds()
            file_complete = False;
            renamer = SaveTvRenamer(self.logger)
            for rec in availableRecordings:
                series  = rec['series']
                episode = rec['episode']
                adfree = rec['adfree']
                
                try:
                    self.logger.debug("Getting " + series + " - " + episode)
                    telecastId = rec['telecastId']
                    link = svte.getRecordingLink(telecastId)
                    
                    if (not link.startswith("http:")):
                        self.logger.warn(link + "is no http link. Deleting entry.")
                        svte.deleteFile(telecastId)
                        continue
                    
                    path = None
                    
                    if (episode is not None and len(episode) > 0):
                        path = renamer.getPath(series, episode, None)
                        if (path is None):
                            continue

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
                                    svte.deleteFile(telecastId)
                                    
                    if (adfree == 0):
                        continue
                                    
                    downloader = SaveTvDownloadWorker(self, link, path, self.logger)
                    file_complete = downloader.download()
                    if self.DELETE_AFTER_DOWNLOAD and file_complete:
                       svte.deleteFile(telecastId)
                       
                except Exception as ex:
                    self.logger.error(ex)
                    continue
            return True
        return False

           
def exitHook():
    print "Exiting"
    lock_file = ".savetv.lck"
    os.remove(lock_file)
    
if __name__ == "__main__":
    lock_file = ".savetv.lck"
    
    if (os.path.exists(lock_file)):

	data = subprocess.Popen(['ps','aux'], stdout=subprocess.PIPE).stdout.readlines()
	print data

        print "Already running"
        sys.exit(1)

    atexit.register(exitHook)
    open(lock_file, "w").close()

    downloader = SaveTvDownloader()
    downloader.readConfiguration()

    if downloader.doDownload():
        sys.exit(0);


    print "Exiting"
    sys.exit(1);
