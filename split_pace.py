import datetime
import time
with open('wan_jin.txt') as fp:
    splitTimeList = [(0, datetime.datetime.strptime('00:00:00', '%H:%M:%S'))]
    for line in fp:
        dummy1, dummy2, distance, paceTime = line.split()
        currentTime = datetime.datetime.strptime(paceTime, "'%H:%M:%S'")
        splitTimeList.append((distance, currentTime))

    for index, e in enumerate(splitTimeList[1:]):
        distance, v = e
        pace5k = v - splitTimeList[index][1]
        print distance, pace5k, str(pace5k//5).split('.')[0], 
        if (index % 2 == 1):
            pace10k = v - splitTimeList[index-1][1] 
            print pace10k, str(pace10k//10).split('.')[0],
        print 

