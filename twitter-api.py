#Author: Anita Ly
#Description: This program is running the tweepy package to retrieve tweets from Twitter and the TextBlob package to analyse sentiment among tweets (using a training data set from IMDB movie reviews)

#Package Setup
import re
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import geopy as gp
import base64
import matplotlib.pyplot as plt
from geotext import GeoText
from shapely.geometry import Point, Polygon
import descartes
import folium

#Run App
#streamlit run twitter-api.py

#Class/Method Setup
class TwitterClient(object):
    """Generic Twitter Class for analyzing sentiment, pulling trends and fetching user details"""
    def __init__(self):
        """Class constructor or initialization method"""
        #Keys and tokens from the Twitter Dev Console
        consumer_key = "nV83psgEeY6DczeDQwDnZ3iF1"
        consumer_secret = "qqQmSaOBqF3kPzSkK0RrIWcJKtZWp1jNNG6CCF1PbaqVxtgzD1"
        access_token = "1323687418466324485-uMmwQrNIPO2CXxCdc62mayy7DtUbpm"
        access_token_secret = "5dWDWxG2CwQXMHOUZULcZ1imhmrJyCyF0YUOBBDze9Uaq"
        #Attempt authentication
        try:
            #Create OAuthHandler object
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            #Set access token and secret
            self.auth.set_access_token(access_token, access_token_secret)
            #Create tweepy API object to fetch tweets
            self.api = tweepy.API(self.auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        except:
            print("Error: Authentication Failed")

    def clean_tweet(self, tweet):
        """Clean tweet text by removing links, special characters using regex statements"""
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:/\S+)"," ", tweet).split())

    def get_tweet_polarity(self, tweet):
        """Retrieve polarity of passed tweet using textblob's sentiment method"""
        #Create TextBlob object of passed tweet_text
        analysis = TextBlob(self.clean_tweet(tweet))
        #Return polarity
        return analysis.sentiment.polarity

    def get_tweet_sentiment(self, tweet):
        """Classify sentiment of passed tweet using textblob's sentiment method"""
        #Create TextBlob object of passed tweet text
        analysis = TextBlob(self.clean_tweet(tweet))
        #Set sentiment based on polarity score
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'

    def get_location(self, place):
        """Get coordinates for user defined location"""
        geolocator = gp.Nominatim(user_agent="myGeocoder", timeout=2)
        location = geolocator.geocode(place)
        if location:
            address = location.address
            latitude = location.latitude
            longitude = location.longitude
        else:
            address = 0
            latitude = 0
            longitude = 0
        return address, latitude, longitude

        #tweet_df = tweet_df[tweet_df.location.notnull()]
        #tweet_df["location"] = tweet_df.location.astype(str)
        #tweet_df = tweet_df[tweet_df['location'].str.endswith("Canada")]

    def get_tweets(self, query, geo, count=10, result_type="recent"):
        """Fetch and parse tweets using keyword and count parameters"""
        #Empty list to store parsed tweets
        tweets = []
        try:
            #Call twitter api to fetch tweets
            fetched_tweets = self.api.search(q=query, geocode=geo, count=count, result_type=result_type, lang="en", tweet_mode="extended")
            #Parsing tweets one by one
            for tweet in fetched_tweets:
                #Empty dictionary to store required parameters of a tweet
                parsed_tweet = {}
                #Saving data of tweet
                parsed_tweet['text'] = tweet.full_text
                parsed_tweet['date'] = tweet.created_at
                parsed_tweet['user'] = tweet.user.screen_name
                parsed_tweet['name'] = tweet.user.name
                parsed_tweet['id'] = tweet.user.id_str
                parsed_tweet['url'] = tweet.user.url
                parsed_tweet['user_defined_location'] = tweet.user.location
                parsed_tweet['coordinates'] = tweet.coordinates
                parsed_tweet['friends'] = tweet.user.friends_count
                parsed_tweet['followers'] = tweet.user.followers_count
                #Saving sentiment/polarity of tweet
                parsed_tweet['polarity'] = self.get_tweet_polarity(tweet.full_text)
                parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.full_text)
                #Retrieve location
                parsed_tweet['location'] = self.get_location(tweet.user.location)[0]
                parsed_tweet['latitude'] = self.get_location(tweet.user.location)[1]
                parsed_tweet['longitude'] = self.get_location(tweet.user.location)[2]
                #Appending parsed tweet to tweets list
                if self.get_location(tweet.user.location)[0] != 0:
                    if tweet.retweet_count > 0:
                        #If tweet has retweets, ensure that it is appended only once
                        if parsed_tweet not in tweets:
                            tweets.append(parsed_tweet)
                    else:
                        tweets.append(parsed_tweet)
            #Return parsed tweets
            return tweets
        except tweepy.TweepError as e:
            #Print error (if any)
            print("Error: " + str(e))

    def get_trends(self, woeid):
        """Return most popular and recent trends"""
        trends = []
        try:
            fetched_trends = self.api.trends_place(woeid) #Canada: 23424803
            for trend in fetched_trends[0]["trends"]:
                parsed_trend = {}
                parsed_trend["name"] = trend["name"]
                parsed_trend["tweet_volume"] = trend["tweet_volume"]
                trends.append(parsed_trend)
            return trends
        except tweepy.TweepError as e:
            #Print error (if any)
            print("Error: " + str(e))

    def get_users(self, query, count=10):
        """Fetch user details of parsed tweets"""
        fetched_tweets = self.api.search(q=query, count=count, lang="en")
        tweets = []
        for tweet in fetched_tweets:
            parsed_tweet = {}
            parsed_tweet['user'] = tweet.user.screen_name
            parsed_tweet['friends'] = tweet.user.friends_count
            tweets.append(parsed_tweet)
        return tweets

    def get_json(self, query, geo, count=10, result_type="mixed"):
        """Fetch and parse tweets using keyword and count parameters"""
        #Call twitter api to fetch tweets
        fetched_tweets = self.api.search(q=query, geocode=geo, count=count, result_type=result_type, lang="en")
        return fetched_tweets

def main():
    #Creating object of TwitterClient Class
    api = TwitterClient()
    #Calling function to get tweets, users and trends
    print("This program fetches a number of tweets based on an entered query, analyzes the sentiment of those tweets using the TextBlob training dataset and pulls the top trends based on geography\n\n")
    #count = int(input("Enter the number of search results to fetch: "))
    count = int(st.sidebar.slider('Select the number of tweets to parse', 1, 500, 500))
    #keyword = input("Enter a keyword: ")
    keyword = st.sidebar.text_input("Enter a keyword", "winter")
    #result_type = input("Enter a result type (mixed, recent, popular): ")
    result_type = st.sidebar.selectbox('Choose the result type', ('recent', 'popular', 'mixed'))
    locator = gp.Nominatim(user_agent="Geocoder")
    place = st.sidebar.selectbox('Choose a location (as the focal point for the search)', ('Toronto, Ontario, Canada', 'Vancouver, British Columbia, Canada', 'Montreal, Quebec, Canada'))
    #location = gp.RateLimiter(locator.geocode(place), min_delay_seconds=1)
    location = locator.geocode(place)
    radius = str(st.sidebar.slider('Select a radius span (in km) for the search', 1, 10000, 1000))
    geo = str(location.latitude) + "," + str(location.longitude) + "," + radius +"km"
    tweets = api.get_tweets(query=keyword, geo=geo, count=count, result_type=result_type)
    users = api.get_users(query=keyword, count=count)
    if place == "Toronto, Ontario, Canada":
        woeid = 4118
    elif place == "Vancouver, British Columbia, Canada":
        woeid = 9807
    elif place == "Montreal, Quebec, Canada":
        woeid = 3534
    trends = api.get_trends(woeid)

    #View JSON for Tweet
    #json = api.get_json(query=keyword, geo=geo, count=count, result_type=result_type)
    #print(json)

    #Printing user details of fetched tweets
    print("\n\nList of Users")
    sorted_users = sorted(users, key=lambda k: k["friends"], reverse=True)
    for user in sorted_users:
        print(user["user"] + ": " + str(user["friends"]) + " friends")

    print("\n\nSentiment Analysis")
    #Picking positive tweets from tweets
    ptweets = [tweet for tweet in tweets if tweet['sentiment'] == 'positive']
    #Percentage of positive tweets
    if len(tweets) > 0:
        positive = 100 * len(ptweets) / len(tweets)
        print("Positive tweets percentage: {}%".format(100 * len(ptweets) / len(tweets)))
    else:
        print("No positive tweets available")
    #Picking negative tweets from tweets
    ntweets = [tweet for tweet in tweets if tweet['sentiment'] == 'negative']
    #Percentage of negative tweets
    if len(tweets) > 0:
        negative = 100 * len(ntweets) / len(tweets)
        print("Negative tweets percentage: {}%".format(100 * len(ntweets) / len(tweets)))
    else:
        print("No negative tweets available")
    #Percentage of neutral tweets
    if len(tweets) > 0:
        neutral = 100 * (len(tweets) - (len(ntweets) + len(ptweets))) / len(tweets)
        print("Neutral tweets percentage: {}%".format(100 * (len(tweets) - (len(ntweets) + len(ptweets))) / len(tweets)))
    else:
        print("No neutral tweets available")

    #Printing first 10 positive tweets
    print("\n\nPositive tweets:")
    counter = 1
    for tweet in ptweets[:10]:
        print(str(counter) + ") " + tweet['text'])
        print("\n")
        counter += 1

    #Printing first 10 negative tweets
    print("\n\nNegative tweets:")
    counter = 1
    for tweet in ntweets[:10]:
        print(str(counter) + ") " + tweet['text'])
        print("\n")
        counter += 1

    #Printing the top trends on Twitter
    print("\n\nTop Twitter Trends")
    for trend in trends:
        print(trend["name"] + ": " + str(trend["tweet_volume"]))

    #places = tweet_df["location"].apply(lambda x: GeoText(x).cities)
    #cities = list(places)
    #cleanse = []
    #clean = ["0" if x == [] else x for x in cities]
    #for city in clean:
    #    place = city[0]
    #    cleanse.append(place)
    #tweet_df["city"] = cleanse

    st.title('Twitter Parser Web App')
    st.subheader("Interested in scraping data from Twitter? Use the parameters in the sidebar to continue!")
    st.text("Twitter Search Data")
    tweet_df = pd.DataFrame(tweets)


    #st.dataframe(tweet_df)

    #geolocator = gp.Nominatim(user_agent="Geocoder",timeout=2)
    #tweet_df["location"] = tweet_df.user_defined_location.apply(geolocator.geocode, language="en")
    #tweet_df["latitude"] = [0 if g is None else g.latitude for g in tweet_df.location]
    #tweet_df["longitude"] = [0 if g is None else g.longitude for g in tweet_df.location]
    #tweet_df = tweet_df[tweet_df.location.notnull()]
    #tweet_df["location"] = tweet_df.location.astype(str)
    #tweet_df = tweet_df[tweet_df['location'].str.endswith("Canada")]
    #midpoint = (np.average(tweet_df['latitude']), np.average(tweet_df['longitude']))
    #st.deck_gl_chart(viewport={'latitude': midpoint[0], 'longitude': midpoint[1], 'zoom': 4}, layers=[{'type': 'ScatterplotLayer', 'data': tweet_df["city", "latitude", "longitude"], 'radiusScale': 250, 'radiusMinPixels': 5, 'getFillColor': [248, 24, 148],}])
    st.map(tweet_df[["latitude", "longitude"]])

    #Mapbox Token
    token = "sk.eyJ1IjoibHlhbml0YSIsImEiOiJja2l6aGI1aHUwZWVoMzB0ZDF6d2c3enllIn0.jdVPFoJVzrm92PUY405RxA"

    column_names = ['date', 'user', 'name', 'id', 'url', 'user_defined_location', 'location', 'coordinates', 'latitude', 'longitude', 'friends', 'followers', 'text', 'sentiment', 'polarity']
    tweet_reordered_df = tweet_df.reindex(columns=column_names)
    st.dataframe(tweet_reordered_df)
    csv = tweet_reordered_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download = tweet_data.csv>Download CSV File</a> (click and save as &lt;filename&gt;.csv)'
    st.markdown(href, unsafe_allow_html=True)

    #polarity_df = tweet_df[["location", "polarity"]]
    #polarity_chart = alt.Chart(polarity_df).mark_bar().encode(x="polarity", y=alt.Y("location", sort="x"), color=alt.Color("location", legend=None)).interactive()
    #st.altair_chart(polarity_chart)

    sentiment_list = ["Positive", "Negative", "Neutral"]
    sentiment_percentage = [positive, negative, neutral]
    sentiment_dt = {'sentiment': sentiment_list, 'percent': sentiment_percentage}
    sentiment_df = pd.DataFrame(sentiment_dt)
    st.dataframe(sentiment_df)

    st.text("")
    st.text("Top Twitter Trends")
    trends_df = pd.DataFrame(trends)
    trends_df = trends_df[trends_df.tweet_volume.notnull()]
    st.dataframe(trends_df)

if __name__ == "__main__":
    #Calling main function
    main()