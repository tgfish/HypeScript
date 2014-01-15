"""
This python script automates downloading files from HypeMachine.com
Copyright (C) 2011  Farid Marwan Zakaria

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

import argparse
import os
import unicodedata
import time
#import sys
import urllib2
import urllib
from bs4 import BeautifulSoup
import json
import string

DEBUG = False
validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

#Define script argument for page(s) to download
parser = argparse.ArgumentParser()
parser.add_argument("hypempages", help="Hypem.com Profile Page(s) to download", type=int ) #Page or Pages to download
parser.add_argument("--s", help="Download only a single Hypem.com Page", action="store_true" ) #Single Page Option
args = parser.parse_args()
argval = vars(args)
NUMBER_OF_PAGES = argval.pop('hypempages')

##############AREA_TO_SCRAPE################
# This is the general area that you'd 
# like to parse and scrape. 
# ex. 'popular', 'latest', '<username>' or
# 'track/<id>'
############################################
AREA_TO_SCRAPE = 'phishie'
HYPEM_URL = 'http://hypem.com/{}'.format(AREA_TO_SCRAPE)

#Create directory to put songs 
foldername = "Hypem Download"
if not os.path.exists(foldername):
    os.makedirs(foldername)
dir_path = foldername  

############
############
############

def removeDisallowedFilenameChars(filename):
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)

class HypeScraper:
  
  def __init__(self):
    pass
    
  def start(self):
    total_files_dl = 0
    print "SCRAPING URL: {} ".format(HYPEM_URL)  
    
    if args.s:
      print "PARSING ONLY SINGLE PAGE #: {}".format(NUMBER_OF_PAGES)        
      #self.execute(NUMBER_OF_PAGES)
      page_url = HYPEM_URL + "/{}".format(NUMBER_OF_PAGES)
      html, cookie = self.get_html_file(page_url)
      tracks = self.parse_html(html)
      print "\tPARSED {} SONGS".format(len(tracks) )
      files_dl = self.download_songs(NUMBER_OF_PAGES, tracks, cookie)
      total_files_dl_str = str(files_dl)
          
    else:
      for i in range(1, NUMBER_OF_PAGES + 1): 
        print "PARSING PAGE: {} of {}".format(i, NUMBER_OF_PAGES)        
        page_url = HYPEM_URL + "/{}".format(i)
        html, cookie = self.get_html_file(page_url)
        if html == "": #failed to download page
          continue
        else:    
          tracks = self.parse_html(html)
          print "\tPARSED {} SONGS".format(len(tracks) )
          files_dl = self.download_songs(i, tracks, cookie)
          total_files_dl = total_files_dl + files_dl
          total_files_dl_str = str(total_files_dl)
               
    print "DOWNLOADED "  + total_files_dl_str + " TOTAL FILES" 

    with open(os.path.join(dir_path, "Downloaded_Songs.txt"), "a") as text_file:
      text_file.write("DOWNLOADED {} TOTAL FILES".format(total_files_dl_str))
      #text_file.write("{} - {}.mp3\n".format(artist, title))
      text_file.close()
      
  def get_html_file(self, url):
    data = {'ax':1 ,
              'ts': time.time()
          }
    data_encoded = urllib.urlencode(data)
    complete_url = url + "?{}".format(data_encoded)
    request = urllib2.Request(complete_url)
    try: response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        print '\tHTTPError = ' + str(e.code) + " trying hypem page url."
        with open(os.path.join(dir_path, "Failed_Pages.txt"), "a") as text_file:
          text_file.write("Failed to download the following page URL due to error code {}:\n {}\n".format(e.code, url))
          text_file.close()
        html = ''
        cookie = ''
        return html, cookie
    else:
      #save our cookie
      cookie = response.headers.get('Set-Cookie')
      #grab the HTML
      html = response.read()
      response.close()
      return html, cookie
    
  def parse_html(self, html):
    track_list = []
    soup = BeautifulSoup(html)
    html_tracks = soup.find(id="displayList-data")
    if html_tracks is None:
      return track_list
    try:
      track_list = json.loads(html_tracks.text)
      return track_list[u'tracks']
    except ValueError:
      print "Hypemachine contained invalid JSON."
      return track_list
      
  #tracks have id, title, artist, key
  def download_songs(self, i, tracks, cookie):

    print "DOWNLOADING SONGS..."
    files_downloaded = 0 
    for track in tracks:
    
      key = track[u"key"]
      sid = track[u"id"]
      artist = removeDisallowedFilenameChars(track[u"artist"])
      title = removeDisallowedFilenameChars(track[u"song"])
      stype = track[u"type"]
 
    
      if stype is False:
        print "\tNO LONGER AVAILABLE, SKIPPING:   [{}] {} by {}".format(stype, title, artist)
        with open(os.path.join(dir_path, "Expired_Songs.txt"), "a") as text_file:
          text_file.write("Page {}, {} - {}\n".format(i, artist, title))
          text_file.close()
        continue
   
      if os.path.exists(os.path.join(dir_path, ("{} - {}.mp3".format(artist, title)))):
        print "\tFILE EXISTS, SKIPPING:   {} - {}.mp3".format(artist, title)
        with open(os.path.join(dir_path, "Existing_Songs.txt"), "a") as text_file:
          text_file.write("{} - {}.mp3\n".format(artist, title))
          text_file.close()
        continue        
      else:
        print "\tFETCHING SONG:  [{}] {} by {}".format(stype, title, artist)
           
      try:
        serve_url = "http://hypem.com/serve/source/{}/{}".format(sid, key)
        request = urllib2.Request(serve_url, "" , {'Content-Type': 'application/json'})
        request.add_header('cookie', cookie)
        response = urllib2.urlopen(request)
        song_data_json = response.read()
        response.close()
        song_data = json.loads(song_data_json)
        url = song_data[u"url"]
      
        download_response = urllib2.urlopen(url)
        filename = "{} - {}.mp3".format(artist, title)
        mp3_song_file = open(os.path.join(dir_path, filename), "wb")
        mp3_song_file.write(download_response.read() )
        mp3_song_file.close()
        files_downloaded = files_downloaded + 1
        with open(os.path.join(dir_path, "Downloaded_Songs.txt"), "a") as text_file:
          text_file.write("{} - {}.mp3\n".format(artist, title))
          text_file.close()
      except urllib2.HTTPError, e:
            print '\t -HTTPError = ' + str(e.code) + " trying hypem download url."
            with open(os.path.join(dir_path, "Failed_Songs.txt"), "a") as text_file:
              text_file.write("HTTPError = {}, Page {}, {} - {}.mp3\n".format(e, i, artist, title))
              text_file.close()
      except urllib2.URLError, e:
            print '\t -URLError = ' + str(e.reason)  + " trying hypem download url."
            with open(os.path.join(dir_path, "Failed_Songs.txt"), "a") as text_file:
              text_file.write("URLError = {}, Page {}, {} - {}.mp3\n".format(e, i, artist, title))
              text_file.close()
      except Exception, e:
            print '\t -Generic Exception: ' + str(e)
            with open(os.path.join(dir_path, "Failed_Songs.txt"), "a") as text_file:
              text_file.write("General Exception = {}, Page {}, {} - {}.mp3\n".format(e, i, artist, title))
              text_file.close()
                
    return files_downloaded 

def main():
  scraper = HypeScraper()
  scraper.start()
       
if __name__ == "__main__":
    main()
