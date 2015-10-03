# -*- coding: utf-8 -*-

import os
import re
import sys
import shutil
import ConfigParser
import tvdb_api
import logging
import translitcodec
import traceback
import codecs

from tvdb_api import Tvdb

class SaveTvRenamer:

    def __init__(self, logger):
        config = ConfigParser.SafeConfigParser()
        config.readfp(codecs.open(os.path.dirname(os.path.realpath(__file__)) + '/savetv.cfg', "r", "ascii"))
        #config.read(os.path.dirname(os.path.realpath(__file__)) + '/savetv.cfg')

        logging.basicConfig(level=logging.DEBUG)

        self.TVSHOW_DIRECTORY = os.path.normpath(config.get('System', 'TvShowDir')) + os.sep
        self.MOVIE_DIRECTORY = os.path.normpath(config.get('System', 'MovieDir')) + os.sep
        self.TVDB = Tvdb(language = 'de', select_first = False) #, dvdorder = True)
        self.SHOWS = {}
        self.SUFFIX = config.get('Optionen', 'FileNameSuffix')
        self.logger = logger

        for dir in os.listdir(self.TVSHOW_DIRECTORY):
            if (os.path.isdir(self.TVSHOW_DIRECTORY + dir)):
                try:
                    self.SHOWS[dir] = config.get('Shows', dir)
                except:
                    self.SHOWS[dir] = "(" + dir + ") (.*)"


    def getPath(self,show,episodename,epnum):
                   
            m = None
            sid = None
            
            for dir in self.SHOWS.keys():
                sid = None
                entry = self.SHOWS[dir].split(",")
                if (len(entry) == 2):
                    sid = int(entry[0])
                    regex = entry[1] #.decode('utf-8')
                else:
                    regex = entry[0] #.decode('utf-8')

                m = re.search(regex, show + " " + episodename, re.UNICODE|re.IGNORECASE)
                if (m is not None):
                    break
            
            if (sid is None and m is None):
                self.logger.debug("Show not configured. Using original name.")
                dir = show

            episodename = episodename.replace("!","").replace("?","").replace(":","")
            
            if (epnum is not None):
                results = [ self.TVDB[show][1][int(epnum)] ]
            else:
                try:
                    if (sid is not None):
                        self.logger.debug( "Searching TVDB with " + str(sid) + " - " + episodename )
                        results = self.TVDB[sid].search(episodename,'episodename')
                    else:
                        self.logger.debug( "Searching TVDB with " + show + " - " + episodename )
                        results = self.TVDB[show].search(episodename,'episodename')
                except Exception as ex:
                    self.logger.error(ex)
                    path = None
                    #self.logger.error("%d:%d" % (fname, lineno))
                    #path = "%s%s - %s.mp4" % (self.TVSHOW_DIRECTORY, show, episodename)
                    #self.logger.warn("Not found. Using " + path)
                    return path
                
            if (len(results) == 0):
                self.logger.debug( "'" + show + " - " + episodename + "' not found in TVDB. Trying manual search." )

                #search_name = name.replace('Der',' ').replace('Die', '').replace('Das', ' ').strip()
                #search_name = name.replace('ae', '.*').replace('ue', '.*').replace('oe', '.*').replace('Ae', '.*').replace('Oe','.*').replace('Ue','.*').replace('ss', '.*').replace(' ', '.*')
                #self.logger.debug( search_name )
                try:
                    #episodename = episodename.encode("utf-8")
                    pattern = re.compile(episodename, re.IGNORECASE|re.UNICODE)
                except Exception as ex:
                    self.logger.debug( "Encoding error" )

                if (sid is not None):
                    allseasons = self.TVDB[sid]
                else:
                    allseasons = self.TVDB[show]

                res = None
                for s in allseasons:
                    season = allseasons[s]
                    self.logger.debug( "%d Folgen in Staffel %d" % (len(season),s) )
                    for x in range(1, len(season)+1):
                        try:
                            ep = season[x]
                            res = pattern.search(ep['episodename'])
                            if res is not None:
                                results.append(ep)
                                self.logger.debug( "Found with \"manual\" search" )
                                break
                        except Exception as ex:
                            self.logger.warn(ex)
                            continue
                    if res is not None:
                        break
                                                
                if (len(results) == 0):
                    try:
                        #episodename = episodename.decode('iso8859-1', 'ignore')
                        path = "%s%s/%s - %s.mp4" % (self.TVSHOW_DIRECTORY, dir, dir, episodename)
                        path = path.encode('translit/long')
                        #self.logger.warn(episodename + " not found. Using " + path)
                        #path = re.sub("[\"\\?:]", '', path)
                        self.logger.warn("Re-encoded path: " + path)
                    except Exception as ex:
                        self.logger.warn("Error in name: " + episodename)
                        self.logger.warn(ex)
                    
                    return path
                else:
                    self.logger.debug("Found %d matches" % (len(results)))
                    
            for result in results:
                self.logger.debug(result)
                if (epnum is not None):
                    season = 1
                    episode = int(epnum)
                else:
                    season = int(result['seasonnumber'])
                    episode = int(result['episodenumber'])

                episodename = result['episodename'].encode('translit/long').encode("iso8859-15", errors='ignore')
                filename = "%s %dx%02d %s.mp4" % (dir,season,episode,episodename)
                path = "%s%s/Season %d/" % (self.TVSHOW_DIRECTORY,dir,season)

                try:
                    #filename = filename
                    #path = path.encode('translit/long')
                    #filename = filename.encode('iso-8859-15')
                    #path = path.encode('iso-8859-15')

                    if (not os.path.isdir(path)):
                        self.logger.debug( "Creating directory " + path )
                        try:
                            os.makedirs(path)
                        except OSError as exc: # Python >2.5
                            if exc.errno == errno.EEXIST and os.path.isdir(path):
                                pass
                            else: raise
                except Exception as ex:
                    self.logger.error(ex)
                    
                dstpath = path + filename
                dstpath = re.sub("[\"\\?:]", '', dstpath)
                
                self.logger.debug(dstpath)
                return dstpath
    

    def rename(self,file,dstpath=None):

        srcpath = self.TVSHOW_DIRECTORY + file
        
        if (os.path.isfile(srcpath)):

            self.logger.debug( file )
            
            if (file.find("Sendung entfaellt") > 0):
                self.logger.debug("Cancelled. Deleting file " + srcpath)
                os.remove(srcpath)
                return

            if (dstpath is None):
                dstpath = self.getname(file)
        
            if (dstpath is None):
                return
                                            
            if (os.path.isfile(dstpath)): # and os.path.getsize(srcpath) >= os.path.getsize(dstpath)):
                self.logger.debug( dstpath + " already exists. Remove " + file )
                try:
                    os.remove(srcpath)
                except OSError as detail:
                    self.logger.debug( "Could not remove " + srcpath,detail )
            else:
                self.logger.debug( "Moving " + srcpath + " to " + dstpath )
                try:
                    shutil.move(srcpath,dstpath)
                except OSError as detail:
                    self.logger.debug( "Could not move " + srcpath,detail )

        elif (os.path.isfile(self.MOVIE_DIRECTORY + file)):
            newname = file.replace('_', ' ')
            newname = re.sub(' ' + self.SUFFIX, '', newname)
            dstpath = self.MOVIE_DIRECTORY + newname + ".mp4"
            srcpath = self.MOVIE_DIRECTORY + file
            self.logger.debug( "Moving " + srcpath + " to " + dstpath )
            try:
                shutil.move(srcpath,dstpath)
            except OSError as detail:
                self.logger.debug( "Could not move " + srcpath, detail )

if __name__ == "__main__":
    renamer = SaveTvRenamer()

    for file in os.listdir(renamer.TVSHOW_DIRECTORY):
        if file.endswith(".part") or os.path.isdir(renamer.TVSHOW_DIRECTORY + file):
            continue
        renamer.rename(file)

    for file in os.listdir(renamer.MOVIE_DIRECTORY):
        if not file.endswith("_478139.mp4"):
            continue
        renamer.rename(file)
        
