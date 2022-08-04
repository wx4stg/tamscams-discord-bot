#!/usr/bin/env python3
# Discord bot for TAMSCAMS and TASC that posts our tweets
# Created 4 August 2022 by Sam Gardner <stgardner4@tamu.edu>


import json
import discord
import tweepy
from facepy import GraphAPI
from time import sleep
from os import path, remove, uname
from datetime import datetime as dt

botTokensDict = json.load(open("botTokens.json", "r"))
discordToken = botTokensDict["discord"]
twitterBearerToken = botTokensDict["twitter-bearer-token"]
discordClient = discord.Client()
twitterClient = tweepy.Client(bearer_token=twitterBearerToken, wait_on_rate_limit=True)
facebookAPI = GraphAPI(botTokensDict["facebook-key"])

async def findTwitterChannel():
    allChannels = discordClient.get_all_channels()
    for channel in allChannels:
        if channel.id == 1004808847141109811:
            return channel
    return None

@discordClient.event
async def on_connect():
    twitterChannel = await findTwitterChannel()
    if twitterChannel is None:
        print("Error: No access to #twitter-feed")
        exit()
    await twitterChannel.send("Bot initialized successfully on "+uname()[1]+" at "+dt.now().strftime("%Y-%m-%d %H:%M:%S"))
    while True:
        if path.exists("alreadyProcessed.json"):
            alreadyProcessedIDs = json.load(open("alreadyProcessed.json", "r"))
        else:
            alreadyProcessedIDs = list()
        for tweetUsername in ["TAMSCAMS", "tamu_tasc"]:
            tweets = twitterClient.search_recent_tweets(query="from:"+tweetUsername, tweet_fields=["id", "referenced_tweets", "author_id"])
            if tweets.data is None:
                continue
            for tweet in tweets.data:
                tweetID = tweet.id
                if "referenced_tweets" in tweet.data.keys():
                        if tweet.referenced_tweets[0].type == "retweeted":
                            tweetUsername = tweet.text.split("RT @")[-1].split(": ")[0]
                            tweetID = tweet.referenced_tweets[0].id
                if str(tweet.id) in alreadyProcessedIDs:
                    continue
                else:
                    alreadyProcessedIDs.append(str(tweet.id))
                    await twitterChannel.send("https://twitter.com/" + tweetUsername + "/status/" + str(tweetID))
        facebookGroupKeys = {
            "TASC" : "408280209379614",
            "TAMSCAMS" : "394074280611522",
            "Test group" : "768418997695857"
        }
        for groupName, groupID in facebookGroupKeys.items():
            try:
                posts = facebookAPI.get(groupID+"/feed", fields="id,message,created_time")["data"]
            except Exception as e:
                posts = list()
            for post in posts:
                if str(post["id"]) in alreadyProcessedIDs:
                    continue
                else:
                    alreadyProcessedIDs.append(post["id"])
                    if "message" in post.keys():
                        await twitterChannel.send(f"New facebook post in {groupName}:\n{post['message']}\nhttps://www.facebook.com/{groupID}/posts/{str(post['id'].replace(groupID+'_', ''))}")
        if path.exists("alreadyProcessed.json"):
            remove("alreadyProcessed.json")
        with open("alreadyProcessed.json", "w") as jsonWrite:
            json.dump(alreadyProcessedIDs, jsonWrite, indent=4)
        sleep(20)
        

discordClient.run(discordToken)