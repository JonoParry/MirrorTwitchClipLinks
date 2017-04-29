#LiveStreamFailLinksBot
import praw
import urllib2, json, requests
from datetime import datetime
import config

twitchClipURL = "https://clips.twitch.tv/"
streamableUploadFromURL = "https://api.streamable.com/import?url="
lastProcessed = ""
lastProcessedDT = 0.0

def isTwitchClipURL(url):
    return url.startswith(twitchClipURL)

def getClipURLFromURL(url):
    print("Getting clip from: ", url)
    clipInfo = "quality_options:"
    urlContent = urllib2.urlopen(url)

    bracketCounter = 0
    foundClipInfo = False
    clipInfoString = ""
    for x in urlContent:
        if str(x).find(clipInfo) > -1:
            print "found clipinfo"
            foundClipInfo = True
        if foundClipInfo:
            clipInfoString += str(x)

            if str(x).find("[") > -1:
                bracketCounter += 1
            if str(x).find("]")  > -1:
                bracketCounter -= 1
            if bracketCounter == 0:
                break

    decodedString = clipInfoString.replace('\n','')
    decodedString = decodedString.replace(clipInfo,"")
    decodedString = decodedString.replace(' ','')
    decodedString = str(decodedString).rstrip(',')
    data = json.loads(decodedString)

    return str(data[0]['source'])

def uploadToStreamable(url,title):
    params = {'url': url}
    r = requests.get(streamableUploadFromURL + url + '&title=' + title, auth=(config.streamableAccount['user'],config.streamableAccount['password']))
    shortCode = json.loads(r.content)['shortcode']
    return shortCode

def postToReddit(submission, shortCode):
    print "Posting to reddit"
    submission.reply("Mirror: https://streamable.com/" + shortCode)
    
def processSubmission(submission):
    url = str(submission.url)
    if isTwitchClipURL(url):
        clipURL = getClipURLFromURL(url)
        
        #check hasn't already been posted
        post = True
        for top_level_comment in submission.comments:
            if(str(top_level_comment.author.name) == reddit.config.username):
                post = False
                break
        if(post):
            #create streamable
            shortCode = uploadToStreamable(clipURL,str(submission.title))
            #post link in comments
            postToReddit(submission, shortCode)


reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit("livestreamfail")

#Get last processed timestamp
validDt=True
try:
    with open("lastprocessed.txt", "r") as f:
        lastProcessed = f.readline()
    date = datetime.utcfromtimestamp(float(lastProcessed))
except:
    validDt = False

#get submissions to process
if(len(lastProcessed) > 0 and validDt):
    lastProcessed = int(float(lastProcessed))

    #process from lastprocessed time
    for submission in subreddit.submissions(start=lastProcessed,end=None):
        processSubmission(submission)
        if(datetime.utcfromtimestamp(float(submission.created_utc)) > datetime.utcfromtimestamp(float(lastProcessedDT))):
            lastProcessedDT = submission.created_utc
else:
    #process newest 10
    for submission in subreddit.new(limit=10):
        processSubmission(submission)
        if(datetime.utcfromtimestamp(float(submission.created_utc)) > datetime.utcfromtimestamp(float(lastProcessedDT))):
            lastProcessedDT = submission.created_utc

#write last processed timestamp to txt
with open("lastprocessed.txt", "w") as f:
    f.write(str(lastProcessedDT))
    f.close()