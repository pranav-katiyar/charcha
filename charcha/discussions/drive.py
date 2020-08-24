import sys
import re
import json
import os
from httplib2 import Http
from google.oauth2 import service_account
import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import GoogleCredentials
import django
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import markdown2
from apiclient.discovery import build
import logging
from django.http import Http404

# This corrresponds to the folder https://drive.google.com/drive/u/1/folders/1eB022nuZqH8TPzj9xU-CakQCJr9kdmll
HASHER_PROFILES_FOLDER = "1eB022nuZqH8TPzj9xU-CakQCJr9kdmll"
def _load_google_credentials():
    keyfile_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', None)
    if not keyfile_str:
        logger.warn("Environment variable GOOGLE_SERVICE_ACCOUNT_JSON not found.")
        return None
    
    service_account_info = json.loads(keyfile_str)
    scopes = ['https://www.googleapis.com/auth/drive.metadata']
    credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes)
    
    return credentials

def _impersonate(email, api, version):
    'impersonate another user using delegated credentials'
    delegated_credentials = BASE_CREDENTIALS.with_subject(email)
    # drive_client = googleapiclient.discovery.build('drive', 'v3', credentials=delegated_credentials)
    # slides_client = googleapiclient.discovery.build('slides', 'v1', credentials=delegated_credentials)
    # return (drive_client, slides_client)
    return googleapiclient.discovery.build(api, version, credentials=delegated_credentials)

def get_hasher_profile_url(requester, profile_email):
    drive_service = _impersonate(requester.email, "drive", "v3")
    children = drive_service.files().list(
        q="'" + HASHER_PROFILES_FOLDER + "' in parents and name contains '" + profile_email + "'" , 
        pageSize=1000
    ).execute()
    files = children.get('files', [])
    if files:
        return "https://docs.google.com/presentation/d/" + files[0]['id']
    
    raise Http404('Slide for user ' + profile_email + " does not exist in the folder https://drive.google.com/drive/u/1/folders/" + HASHER_PROFILES_FOLDER)

BASE_CREDENTIALS = _load_google_credentials()