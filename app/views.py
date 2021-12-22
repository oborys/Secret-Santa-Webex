from app import app
import datetime as dt
from pprint import pprint
import os, time
import requests
import json
import sys
import subprocess
import os
import random
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import datetime as dt
from datetime import datetime, timedelta
from flask import Flask
from flask import request, redirect, url_for, render_template
import configparser
import re
import sqlite3

import random
import itertools  
from itertools import combinations
import datetime as dt
from datetime import datetime, timedelta
import string

import urllib.parse


# read variables from config
credential = configparser.ConfigParser()
credential.read('cred')


######################
bearer_bot = credential['Webex']['WEBEX_TEAMS_TOKEN']
botEmail = credential['Webex']['WEBEX_BOT_EMAIL']
checkAnswerText = credential['Text']['CHECK_ANSWER']
answerIsWrittenText = credential['Text']['ANSWER_IS_WRITTEN']
# WebhookUrl
webhookUrl = credential['Webex']['WEBEX_WEBHOOK_URL']

adminEmailList = ['adminmail@mail.com', 'adminmail2@mail.com']

headers_bot = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer_bot
}

#### Functions

def createWebhook(bearer, webhookUrl):
    hook = True
    botWebhooks = send_webex_get("https://webexapis.com/v1/webhooks")["items"]
    for webhook in botWebhooks:
        if webhook["targetUrl"] == webhookUrl:
            hook = False
    if hook:
        dataWebhook = {
        "name": "Messages collab bot Webhook",
        "resource": "messages",
        "event": "created",
        "targetUrl": webhookUrl
        }
        dataWebhookCard = {
            "name": "Card Report collab bot Webhook",
            "targetUrl": webhookUrl,
            "resource": "attachmentActions",
            "event": "created"
        }
        send_webex_post("https://webexapis.com/v1/webhooks/", dataWebhook)
        send_webex_post("https://webexapis.com/v1/webhooks/", dataWebhookCard)
    print("Webhook status: done")

def deleteWebHooks(bearer, webhookUrl):
    webhookURL = "https://api.ciscospark.com/v1/webhooks/"
    botWebhooks = send_webex_get(webhookURL)["items"]
    for webhook in botWebhooks:
        send_webex_delete(webhookURL + webhook["id"])

def send_webex_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers_bot)
    else:
        request = requests.get(url, headers=headers_bot, params=payload)
    if js == True:
        if request.status_code == 200:
            try:
                r = request.json()
            except json.decoder.JSONDecodeError:
                print("Error JSONDecodeError")
                return("Error JSONDecodeError")
            return r
        else:
            print (request)
            return ("Error " + str(request.status_code))
    return request

def send_webex_delete(url, payload=None):
    if payload == None:
        request = requests.delete(url, headers=headers_bot)
    else:
        request = requests.delete(url, headers=headers_bot, params=payload)


def send_webex_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers_bot).json()
    return request


def postNotificationToPerson(reportText, personEmail):
    body = {
        "toPersonEmail": personEmail,
        "markdown": reportText,
        "text": "This text would be displayed by Webex Teams clients that do not support markdown."
        }
    send_webex_post('https://webexapis.com/v1/messages', body)

def postCard(personEmail):
    # open and read data from file as part of body for request
    with open("cardText.txt", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    print("POST CARD TO ", personEmail)

def printParticipantList(personEmail):
    with open('allParticipantAddress.txt', 'r') as f:
        allPairs = f.read().split('\n')
        allPairsList = f.read().split('\n')
    
    n = 1
    reportText = "All Pairs List \n"
    for pair in allPairs:
        reportText = reportText + "number: {} \n Email and Data: {} \n".format(n, pair)
        n += 1
    body = {
        "toPersonEmail": personEmail,
        "markdown": reportText,
        "text": "This text would be displayed by Webex Teams clients that do not support markdown."
    }
    send_webex_post('https://webexapis.com/v1/messages', body)
  
def getParticipantAddress(address, personEmail):
    with open('allParticipantAddress.txt', 'a') as m:
        data = personEmail + ";" + address + '\n'
        m.write(data)
    with open('allParticipantList.txt', 'a') as p:
        data = personEmail + '\n'
        p.write(data)

def printTitleCard(personEmail):   
    # open and read data from file as part of body for request
    with open("cardText.txt", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()

def sentSantaInfo(personEmail, recipientEmailAdr):
    recipientEmail = recipientEmailAdr.split(';')[0]
    print("recipientEmail ", recipientEmail)
    resp = send_webex_get('https://api.ciscospark.com/v1/people?email=' + recipientEmailAdr.split(';')[0])
    recipientName = resp["items"][0]["displayName"]
    print("recipientName ", recipientName)
    reportText = "Congratulations, choose a gift worth up to UAH 300 and send it to the addressee by December 28 {}, {}, address: {} \n It is possible anonymously. Also, expect a gift for yourself at the specified address/office".format(recipientName, recipientEmail, str(recipientEmailAdr.split(';')[1]))
    with open('allParticipantChain.txt', 'a') as p:
        text = str(personEmail) + ' to ' + reportText + '\n'
        p.write(text)
    postNotificationToPerson(reportText, personEmail)
    #print(personEmail, " code: ", str(resp.status_code))

def shuffleAndGetPair():
    with open("allParticipantAddress.txt", "r", encoding="utf-8") as f:
        addressList = f.read().split('\n')
        if addressList[-1] == '':
            addressList.pop()
        random.shuffle(addressList)
        numberIter = len(addressList)
        i = 0
        while True:
            if (i + 1) < numberIter:
                email = addressList[i].split(';')[0]
                recipientEmailAdr = addressList[i + 1]
                sentSantaInfo(email, recipientEmailAdr)
            elif (i + 1) == numberIter:
                recipientEmailAdr = addressList[0]
                sentSantaInfo(addressList[i].split(';')[0], recipientEmailAdr)
                break
            i += 1

    
@app.route('/', methods=['GET', 'POST'])
def webex_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        print("Webhook:")
        pprint(webhook)
        if webhook['resource'] == 'messages' and webhook['data']['personEmail'] != botEmail:
            result = send_webex_get('https://webexapis.com/v1/messages/{0}'.format(webhook['data']['id']))
            print("result messages", result)
            in_message = result.get('text', '').lower()
            print("in_message", in_message)
            if in_message.startswith('/list') and (webhook['data']['personEmail'] in adminEmailList):
                personEmail = webhook['data']['personEmail']
                printParticipantList(personEmail)
            elif in_message.startswith('/runsanta') and (webhook['data']['personEmail'] in adminEmailList):
                shuffleAndGetPair()
            else:
                printTitleCard(webhook['data']['personEmail'])

        elif webhook['resource'] == 'attachmentActions':
            result = send_webex_get('https://webexapis.com/v1/attachment/actions/{}'.format(webhook['data']['id']))
            print("RESULT ",result)

            if (result['inputs']['address']):
                person = send_webex_get('https://api.ciscospark.com/v1/people/{}'.format(result['personId']))
                personEmail = person["emails"][0]
                with open('allParticipantList.txt', 'r') as p:
                    data = p.read().split('\n')
                if personEmail in data:
                    reportText = checkAnswerText
                    postNotificationToPerson(reportText, personEmail)
                else:
                    getParticipantAddress(result['inputs']['address'], personEmail)
                    reportText = answerIsWrittenText
                    postNotificationToPerson(reportText, personEmail)
        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"http://bit.ly/SparkBot-512x512\" alt=\"Webex Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\"></i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Please don't forget to create Webhooks to start receiving events from Webex Teams!</i></b></center>" \
                "<center><b>Generate meeting token <a href='/token'>/token</a></b></center>"
        return message




print("Start the Santa")
deleteWebHooks(bearer_bot, webhookUrl)
createWebhook(bearer_bot, webhookUrl)
