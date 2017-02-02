import json
import urllib
import re
import requests
import sys

def download_image(detail_list):
    for index, data in enumerate(detail_list):
        result = re.search(r'http://image3.photochoice.net/r/tn_(\d+_\d+_\d+_\d+_[\d\w]+_\d+)', data)
        imageUrl = r'http://image3.photochoice.net/r/tn_{0}/pc_watermark_17_v/3/16500x16500/0x0_1280x16500/'.format(result.group(1))
        filename = "{0:02d}.jpg".format(index+1)
        print "download {0} {1}".format(filename, imageUrl)
        image = urllib.URLopener()
        image.retrieve(imageUrl, filename)

def get_thumb_url(url):
    r = requests.get(url)
    result = re.search(r'appInfo = ({.*})', r.text)
    if result == None:
        return

    appInfo = result.group(1)
    json_format = json.loads(appInfo)
    url = r"http://allsports.tw" + json_format['thumbUrl']
    print 'Get thumburl: ' + url
    return url

def get_detail_list(url):
    r = requests.get(url)
    detail_list = [data['detail'] for data in r.json()]
    print "Get detail list:"
    from pprint import pprint
    pprint (detail_list)
    return detail_list

def main():
    all_sports_url = sys.argv[1]
    print "Requests url: " + all_sports_url
    thumb_url = get_thumb_url(all_sports_url)
    print 
    detail_list = get_detail_list(thumb_url)
    print 
    download_image(detail_list)

if __name__ == '__main__':
    main()
