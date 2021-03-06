"""Sraper template for Discovery Networks (USA)."""
from bs4 import BeautifulSoup
import re
import requests
import json
from scrapertemplates import basic


class DiscoveryScraper(basic.BasicScraper):
    """Scraper Template for DiscoveryGo (USA)."""

    CHANNEL = ""

    token = ""
    codes = {"sciencechannel": "SCI",
             "discovery": "DSC",
             "animalplanet": "APL",
             "investigationdiscovery": "IDS",
             "velocity": "VEL",
             "destinationamerica": "DAM",
             "ahctv": "AHC",
             "discoverylife": "DLF",
             "tlc": "TLC"}

    def scrape(self):
        """Scrape Discovery networks (USA)."""
        for s in self.getShows():
            print(s[0])
            self.getEpisodes(s)

    def getShows(self):
        """Get Show list from Discovery.com to get ALL shows."""
        # Warning: 2 extrem long URLs ahead!!!
        url_token = ("https://www.{channel}.com/anonymous?authLink="
                     "https%3A%2F%2Flogin.discovery.com%2Fv1%2Foauth2%2"
                     "Fauthorize%3Fclient_id%3D3020a40c2356a645b4b4%26"
                     "redirect_uri%3Dhttps%253A%252F%252Ffusion.ddmcdn.com"
                     "%252Fapp%252Fmercury-sdk%252F180%252"
                     "FredirectHandler.html%253Fhttps%253A%252F%252F"
                     "www.{channel}.com%26response_type%3Danonymous%26"
                     "state%3DeyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                     "eyJub25jZSI6InFIYmVsMjF3dGZLZTRZRnhpZFdIOVdoSElPQ0Y1R2E"
                     "2In0.nbxy_qf3PyWErA7FwFkh1XtaDSpLkuJlfILQM_s34mE%26"
                     "networks.code%3DSCI&client_id=3020a40c2356a645b4b4"
                     "&state=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
                     "eyJub25jZSI6InFIYmVsMjF3dGZLZTRZRnhpZFdIOVdoSElPQ0Y1R2E"
                     "2In0.nbxy_qf3PyWErA7FwFkh1XtaDSpLkuJlfILQM_s34mE")

        url_token = url_token.format(channel=self.CHANNEL)

        url_shows = ("https://api.discovery.com/v1/content/shows?networks"
                     ".code={code}&platform=desktop&product=sites&sort="
                     "-video.airDate.type%28episode%7Climited%7Cevent%7Cstunt"
                     "%7Cextra%29")
        url_shows = url_shows.format(code=self.codes[self.CHANNEL])

        r = requests.get(url=url_token)
        self.token = json.loads(r.text)["access_token"]

        # Yep, you have to receive a token to list shows
        r = requests.get(url=url_shows,
                         headers={"authorization": "Bearer " + self.token})
        j_shows = json.loads(r.text)
        for show in j_shows:
            yield (show["name"], show["socialUrl"].split("/")[3])

    def getEpisodes(self, show):
        """Get Episodes from discoverygo.com."""
        ch = self.CHANNEL
        if ch == "velocity":
            ch += "channel"

        url_episodes = "https://www.{channel}go.com/{show_link}/"
        url_episodes = url_episodes.format(channel=ch, show_link=show[1])

        print(url_episodes)

        myTVShowTitle = show[0]

        myShowID = self.addShow(myTVShowTitle, "en")

        r = requests.get(url_episodes)
        bs = BeautifulSoup(r.text, "html.parser")

        episodeInfos = [e for e in bs.find_all("script",
                                               type="application/ld+json")]

        for eI in episodeInfos:

            """ Are these mistakes in js for any purpose.
                Ugly, but it works, sortof."""
            b = """}
        }
    }"""
            text = eI.string
            text = text.replace(b, "}}")
            text = re.sub("(&.+;)", "", text)
            text = text.replace("\"sameAs :", "\"sameAs\" :")
            text = re.sub("\r|\n", "", text)
            js = json.loads(text)

            if js["@type"] == "TVEpisode":

                # TODO: write THIS thing nice.
                Free = not eI.next_sibling.next_sibling.next_sibling.next_sibling.div["class"][0] == "content-auth"

                if Free:
                    print("FREE PREVIEW")
                    try:
                        episodeNumber = js["episodeNumber"]
                        seasonNumber = 0
                        myEpisodeTitle = js["name"]
                        quality = "1080"
                        url = js["sameAs"]
                        seasonNumber = js["partOfSeason"]["seasonNumber"]

                        self.parent.myDB.addEpisode(myShowID,
                                                    seasonNumber,
                                                    episodeNumber,
                                                    myEpisodeTitle,
                                                    url, "any", quality)
                    except Exception:
                        print("Skip episode")
