from mechanize import Browser
import os
import sys
import re
import glob
import socket
import urllib
import datetime
import urllib
import logging
import HTMLParser
import json
from sets import Set

class SaveTvEntity:
    SAVETV_URL = "http://www.save.tv"

    def __init__(self, username, password, logger):
        self.username = username
        self.password = password

        socket.setdefaulttimeout(60)        
        self.browser = Browser()
        # Want debugging messages?
        #self.browser.set_debug_http(True)
        #self.browser.set_debug_redirects(True)
        #self.browser.set_debug_responses(True)

        self.logger = logger
   
    def fetchDownloadableTelecaseIds(self):

        self.logger.debug("Opening video archive ")

        telecastIds = []
        htmlparser = HTMLParser.HTMLParser()
        response = None

        for i in range(1,4):
            try:
                n = 1
                
                while True:

                    #response = self.browser.open("/STV/M/obj/user/usShowVideoArchive.cfm?bLoadLast=1&sSortOrder=StartDateASC")
                    response = self.browser.open("/STV/M/obj/archive/JSON/VideoArchiveApi.cfm?iEntriesPerPage=50&iCurrentPage=%d&iFilterType=1&sSearchString=&iTextSearchType=0&iChannelId=0&iTvCategoryId=0&iTvSubCategoryId=0&bShowNoFollower=false&iRecordingState=1&sSortOrder=StartDateASC&iTvStationGroupId=0&iRecordAge=0&iDaytime=0" % (n))
                    if (response is None):
                        return telecastIDs
                    
                    #f = open("json.log", "w")
                    #f.write(response.get_data())
                    #f.write("\n")d
                    
                    jdata = json.loads(unicode(response.get_data(), 'utf-8'))
                    
                    if (n == 1):
                        countTotal = int(jdata['ITOTALENTRIES'])
                        self.logger.debug("Total: %d" % countTotal)

                    for archiveentry in jdata['ARRVIDEOARCHIVEENTRIES']:
           
                        telecastentry = archiveentry['STRTELECASTENTRY']
                        series = telecastentry['STITLE']
                        episode = telecastentry['SSUBTITLE']
                        startdate = telecastentry['DSTARTDATE']
                        status = telecastentry['SSTATUS']
                        adfree = telecastentry['BADFREEAVAILABLE']
                        telecastId = telecastentry['ITELECASTID']
                        entry = {'telecastId':telecastId,'series':series,'episode':episode,'adfree':adfree}
                        self.logger.debug("%s - %s, Startdate: %s, Status: %s, Ad-Free: %d, Telecast-ID: %d" % (series, episode, startdate, status, adfree, telecastId))
                        
                        if (status == "FAILED" or status == "Sendung entfallen"):
                            self.logger.info("Cancelled. Deleting file.")
                            self.deleteFile(telecastId)
                            
                        elif (status == "OK"):
                            telecastIds.append(entry)
                                    
                    #f.close
                            
                    if (countTotal >= 50):
                        countTotal = countTotal - 50
                        n = n + 1
                    else:
                        break
                    
                    #telecastIds.append(str(e['ITELECASTID']))
                #titles = re.findall("data-title=\"(.*)\"", response.get_data())
                #print telecastIds
                return telecastIds
                
            except (ValueError, KeyError, TypeError):
                self.logger.error("JSON format error", sys.exc_info()[0])
                return telecastIds            
            except:
                if (i == 4):
                    self.logger.error("Failed to open")
                    return telecastIds
                continue

        for recordingLink in self.browser.links(url_regex=".*usShowVideoArchiveDetail.cfm.*"):
            self.logger.debug(recordingLink)
            telecastId = self.extractTelecastId(recordingLink)
            if telecastId not in telecastIds:
                self.logger.debug("Found Download. Telecast-ID: " + telecastId)
                telecastIds.append(telecastId)

        for title in titles:
            title = htmlparser.unescape(title)
            data=urllib.urlencode({'ajax':'true','clientAuthenticationKey':'','callCount':'1','c0-scriptName':'null','c0-methodName':'GetVideoEntries','c0-id':'6851_1403625014088','c0-param0':'string:1','c0-param1':'string:','c0-param2':'string:1','c0-param3':'string:1208799','c0-param4':'string:1','c0-param5':'string:0','c0-param6':'string:1','c0-param7':'string:0','c0-param8':'string:1','c0-param9':'string:','c0-param10':'string:'+title,'c0-param11':'string:2','c0-param12':'string:toggleSerial','xml':'true',"extend":"function (object) {\r\n  for (property in object) {\r\n    this[property] ","":""});                                    
            for i in range(1,4):
                try:
                    sys.stdout.write("Getting TelecastIDs for title " + title)
                    response = self.browser.open("/STV/M/obj/user/usShowVideoArchiveLoadEntries.cfm?null.GetVideoEntries", data)
                    #sys.stdout.write(response.get_data())
                    ids = re.findall("TelecastID=(\d+)", response.get_data())
                    break
                except:
                    if (i == 4):
                        self.logger.error("Failed to open")
                    
            for id in ids:
                if id not in telecastIds:
                    self.logger.debug("Found Download. Telecast-ID: " + id)
                    telecastIds.append(id)
         
        # return list of unique Ids.
        return telecastIds
    
    def extractTelecastId(self, pRecordingLink):
        absurl = pRecordingLink.absolute_url
        telecastId = absurl.split("TelecastID=")[1].split("&&sk")[0]

        #if (not os.path.exists(telecastId)):
        #    f = open(telecastId, "w").close()

        return telecastId

    def getDownloadableRecordingLinks(self, pDownloadableRecordings):
        downloadLinks = {}
        for telecastID in pDownloadableRecordings:
            #print telecastID    
            #created = datetime.datetime.fromtimestamp(os.stat(telecastID).st_mtime)
            #now = datetime.datetime.now()

            #if (created < now):
            #    continue

            #os.path.delete(telecastID)
            #data=urllib.urlencode({'ajax':'true','clientAuthenticationKey':'','callCount':'1','c0-scriptName':'null','c0-methodName':'GetAdFreeAvailable','c0-id':'9999_9999999999999','c0-param0':'string:'+telecastID,'c0-param1':'string','c0-param2':'boolean:true','c0-param3':'string:96987','c0-param4':'string:1','c0-param5':'string:0','c0-param6':'string:1','c0-param7':'string:0','c0-param8':'string:1','c0-param9':'string:','c0-param10':'string:','c0-param11':'string:19','c0-param12':'string:toggleSerial','xml':'True'});
            #adfreeinfo = self.browser.open("/STV/M/obj/cRecordOrder/croGetAdFreeAvailable.cfm", data)
            #p = re.compile("9999_9999999999999 = \'(\d)\'")
            #result = p.search(adfreeinfo.get_data())
            #adfree = 0
            #if result:
            #    adfree = int(result.group(1))
 
            #if (adfree == 0):
            #    print telecastID + " not ad free"
            #    continue

            dlInfoLink = None
            self.logger.debug("Getting link for Telecast-ID " + telecastID)
            for i in range(1,4):
                try:
                    #dlInfoLink = self.browser.open("/STV/M/obj/cRecordOrder/croGetDownloadUrl.cfm?null.GetDownloadUrl&=&ajax=true&c0-id=9999_9999999999999&c0-methodName=GetDownloadUrl&c0-param0=number%3A"+telecastID+"&c0-param1=number%3A0&c0-param2=boolean%3Atrue&c0-scriptName=null&callCount=1&clientAuthenticationKey=&xml=true")
                    response = self.browser.open("/STV/M/obj/cRecordOrder/croGetDownloadUrl.cfm?TelecastId="+telecastID+"&iFormat=0&bAdFree=true")
                    #print response.get_data()
                    break
                except Exception as ex:
                    if (i < 4):
                        continue
                    self.logger.error( "Error getting link for Telecast-ID %s, %s" % (telecastID, ex))
 
            if (response is None):
               continue

            try:
               jdata = json.loads(response.get_data())
               #print jdata['ARRVIDEOURL'][2]
               tmpDlDetails = jdata['ARRVIDEOURL'][2]
            except Exception as ex:
               print ex
            
            if tmpDlDetails <> "":
                downloadLinks[telecastID] = tmpDlDetails

        self.logger.debug(downloadLinks)
        return downloadLinks

    def getRecordingLink(self, telecastID):

        self.logger.debug("Getting link for Telecast-ID " + str(telecastID))
        response = None
        
        for i in range(1,4):
            try:
                #dlInfoLink = self.browser.open("/STV/M/obj/cRecordOrder/croGetDownloadUrl.cfm?null.GetDownloadUrl&=&ajax=true&c0-id=9999_9999999999999&c0-methodName=GetDownloadUrl&c0-param0=number%3A"+telecastID+"&c0-param1=number%3A0&c0-param2=boolean%3Atrue&c0-scriptName=null&callCount=1&clientAuthenticationKey=&xml=true")
                response = self.browser.open("/STV/M/obj/cRecordOrder/croGetDownloadUrl.cfm?TelecastId="+str(telecastID)+"&iFormat=0&bAdFree=true")
                #print response.get_data()
                break
            except Exception as ex:
                if (i < 4):
                    continue
                self.logger.error("Error getting link for Telecast-ID %d, %s" % (telecastID, ex))

        if (response is None):
           return

        try:
           jdata = json.loads(response.get_data())
           dlLink = jdata['ARRVIDEOURL'][2]
        except Exception as ex:
           self.logger.error(ex)

        self.logger.debug(dlLink)
        return dlLink
        
    def getDownloadLink(self, pDlInfoLink):
        p = re.compile("'(http://[^']*?m=dl[^']*)'")
        result = p.search(pDlInfoLink)
        url = ""
        if result:
            url = result.group(1)
            self.logger.debug("Found download URL: " + url)
        else:
            self.logger.debug("No download URL found (probably recording still in progress).")
        return url

    def deleteFile(self, telecastID):
        socket.setdefaulttimeout(30)        
        #post_data = urllib.urlencode({'lTelecastID' : telecastID})
        for i in range(1,4):
            try:
                #response = self.browser.open("/STV/M/obj/user/usShowVideoArchive.cfm", post_data)
                response = self.browser.open("/STV/M/obj/cRecordOrder/croDelete.cfm?TelecastID=%d" % (telecastID))
                if response.code == 200:
                    self.logger.debug("File for telecast-ID %d deleted." % (telecastID) )
                    #self.logger.debug(response.get_data())
                else:
                    self.logger.debug("File not deleted. Response was: %d" % (response.code))
                break
            except Exception as ex:
                self.logger.debug("Exception: " + ex)
                continue
                
        #print "File for telecast-ID %s not deleted. Error was: %s" %(telecastID, ex)
        
    def initialiseLogin(self):
        socket.setdefaulttimeout(30)        
        sys.stdout.write("Logging in ")
        sys.stdout.flush()
        for i in range(1,4): 
            try:
                self.browser.open(self.SAVETV_URL)
                #self.browser.follow_link(self.browser.links(url_regex=".*index\.cfm.*").next())
                #import pdb; pdb.set_trace()
                self.browser.select_form(nr=0)
                self.browser["sUsername"] = self.username
                self.browser["sPassword"] = self.password
                self.browser.submit()
                print " done"
                return True
            except Exception as e:
                sys.stdout.write(".")
                print e.reason
                sys.stdout.flush()
                continue

        print " failed"
        return False

        response = self.browser.follow_link(self.browser.links(url_regex=".*miscShowHeadFrame.cfm.*").next())
        print response.code
        if response.code == 200:
            print "Login successful"
        else:
            print "Login NOT successful"
        #p = re.compile("href=\"([^\"]*usShowVideoArchive[^\"]*)\"")
        #url = p.search(response.get_data()).group(1)        

        #response = self.browser.open(url)
