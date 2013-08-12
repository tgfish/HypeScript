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

import os
import unicodedata
import time
import sys
import urllib2
import urllib
from bs4 import BeautifulSoup
import json
import string

##############AREA_TO_SCRAPE################
# This is the general area that you'd 
# like to parse and scrape. 
# ex. 'popular', 'latest', '<username>' or
# 'track/<id>'
############################################
AREA_TO_SCRAPE = 'popular'
ask_pages = raw_input ("How many pages would you like to download? ").strip()
NUMBER_OF_PAGES = int(ask_pages)

###DO NOT MODIFY THESE UNLES YOU KNOW WHAT YOU ARE DOING####
DEBUG = False
HYPEM_URL = 'http://hypem.com/{}'.format(AREA_TO_SCRAPE)

foldername = "Hypem Download"
if not os.path.exists(foldername):
    os.makedirs(foldername)
print "\tCREATED FOLDER:" + foldername
dir_path = foldername  
files_downloaded = 0

validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def removeDisallowedFilenameChars(filename):
    cleanedFilename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore')
    return ''.join(c for c in cleanedFilename if c in validFilenameChars)


class HypeScraper:
  
  def __init__(self):
    pass
    
  def start(self):
    print "--------STARTING DOWNLOAD--------"
    print "\tURL : {} ".format(HYPEM_URL)
    print "\tPAGES: {}".format(NUMBER_OF_PAGES)
    
    for i in range(1, NUMBER_OF_PAGES + 1):
    
      print "PARSING PAGE: {}".format(i)
    
      page_url = HYPEM_URL + "/{}".format(i)
      html, cookie = self.get_html_file(page_url)

      if DEBUG:
        html_file = open("hypeHTML.html", "w")
        html_file.write(html)
        html_file.close()
        
      tracks = self.parse_html(html)
      
      print "\tPARSED {} SONGS".format(len(tracks) )
      
      self.download_songs(i, tracks, cookie)
    
    files_downloaded_str = str(files_downloaded)	
    print "DOWNLOADED "  + files_downloaded_str + " FILES"      
      
  def get_html_file(self, url):
    data = {'ax':1 ,
              'ts': time.time()
          }
    data_encoded = urllib.urlencode(data)
    complete_url = url + "?{}".format(data_encoded)
    request = urllib2.Request(complete_url)
    response = urllib2.urlopen(request)
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
  
    print "\tDOWNLOADING SONGS..."
    for track in tracks:
    
      key = track[u"key"]
      id = track[u"id"]
      artist = removeDisallowedFilenameChars(track[u"artist"])
      title = removeDisallowedFilenameChars(track[u"song"])
      type = track[u"type"]
   
      if os.path.exists(os.path.join(dir_path, ("{} - {}.mp3".format(artist, title)))):
        print "\tFILE EXISTS, SKIPPING: {} - {}.mp3".format(artist, title)
      else:
        print "\tFETCHING SONG...." 
        print u"\t{} by {}".format(title, artist)
      
        if type is False:
          continue
       
        try:
          serve_url = "http://hypem.com/serve/source/{}/{}".format(id, key)
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
          with open(os.path.join(dir_path, "log.txt"), "a") as text_file:
               text_file.write("{} - {}.mp3\n".format(artist, title))
               text_file.close()
        except urllib2.HTTPError, e:
              print 'HTTPError = ' + str(e.code) + " trying hypem download url."
              with open(os.path.join(dir_path, "Failed_songs_log.txt"), "a") as text_file:
                   text_file.write("HTTPError = {}, Page {}, {} - {}.mp3\n".format(e, i, artist, title))
                   text_file.close()
        except urllib2.URLError, e:
              print 'URLError = ' + str(e.reason)  + " trying hypem download url."
              with open(os.path.join(dir_path, "Failed_songs_log.txt"), "a") as text_file:
                   text_file.write("URLError = {}, Page {}, {} - {}.mp3\n".format(e, i, artist, title))
                   text_file.close()
        except Exception, e:
              print 'generic exception: ' + str(e)
              with open(os.path.join(dir_path, "Failed_songs_log.txt"), "a") as text_file:
                   text_file.write("General Exception = {}, Page {}, {} - {}.mp3\n".format(e, i, artist, title))
                   text_file.close()
     

def main():
  scraper = HypeScraper()
  scraper.start()
       
if __name__ == "__main__":
    main()
    
