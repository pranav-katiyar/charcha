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
from charcha.discussions.models import User, UserProfile
from django.utils import timezone
import markdown2
from apiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

SOURCE_PRESENTATION = "1huxWCP1GnvPxbgmV94wt5fhfYU32VAYDo3to8DRIlOI"
DESTINATION_FOLDER = "1eB022nuZqH8TPzj9xU-CakQCJr9kdmll"

class Command(BaseCommand):
    help = 'Imports hasher bio from Google Slides - Hasher Engineering Profiles'
    
    def handle(self, *args, **options):
        base_credentials = _load_google_credentials()
        root_slide_service = _polyjuice_potion(
            base_credentials, "sripathi.krishnan@hashedin.com", "slides", "v1")
        root_drive_service = _polyjuice_potion(
            base_credentials, "sripathi.krishnan@hashedin.com", "drive", "v3")

        emails_to_skip = self.emails_to_skip(root_drive_service)
        annotations = self.annotate_source_slides(root_slide_service, SOURCE_PRESENTATION)
        
        all_slides = set([a[0] for a in annotations])

        for annotation in annotations:
            try:
                slide_id = annotation[0]
                email = annotation[1]
                raw_email = annotation[2]
                if not email:
                    continue
                if email in emails_to_skip:
                    print("Skipping slide for " + email + " since it already exists")
                    continue
                print("Processing slide for " + email)
                drive_service = _polyjuice_potion(base_credentials, email, "drive", "v3")
                slide_service = _polyjuice_potion(base_credentials, email, "slides", "v1")
                slides_to_delete =  all_slides - set([slide_id])
                title = raw_email + " Profile"
                presentationId = self.clone_file(drive_service, SOURCE_PRESENTATION, DESTINATION_FOLDER, title)
                self.delete_slides_from_presentation(slide_service, presentationId, slides_to_delete)
            except Exception as e:
                print("Skipping " + email + " due to error - " + str(e))

    def delete_slides_from_presentation(self, slide_service, presentationId, slides_to_delete):
        requests = [{'deleteObject': {'objectId': slide_id}} for slide_id in slides_to_delete]
        slide_service.presentations()\
            .batchUpdate(body={'requests': requests}, presentationId=presentationId).execute()
        
    def emails_to_skip(self, drive_service):
        emails = set()
        children = drive_service.files().list(q="'" + DESTINATION_FOLDER + "' in parents", pageSize=1000).execute()
        for child in children.get('files', []):
            file_name = child['name']
            email = self._normalize_email(file_name)
            if email:
                emails.add(email)
        return emails

    def annotate_source_slides(self, slide_service, presentationId):
        response = slide_service.presentations()\
            .get(presentationId=presentationId)\
            .execute()

        annotations = [None] * len(response['slides'])
        for index, slide in enumerate(response['slides']):
            slide_id = slide['objectId']
            notes = []
            notes_page_elements = get_nested(slide, 'slideProperties.notesPage.pageElements')
            if not notes_page_elements:
                continue
            for pe in notes_page_elements:
                text_elements = get_nested(pe, 'shape.text.textElements')
                if not text_elements:
                    continue
                for te in text_elements:
                    text = get_nested(te, 'textRun.content')
                    if not text:
                        continue
                    notes.append(text)
            
            raw_email = "".join(notes).strip()
            email = self._normalize_email(raw_email)
            annotations[index] = (slide_id, email, raw_email)
        return annotations

    def _normalize_email(self, raw_email):
        '''
        Input => Rashmi Ranjan <rashmi.ranjan@hashedin.com>
        Output => rashmi.ranjan@hashedin.com
        '''
        m = re.search(r"[\s<]?([a-zA-Z0-9\._-]+@hashedin.com)", raw_email)
        if m:
            return m.group(1).lower()
        return None

    def clone_file(self, drive_service, source_id, destination_folder_id, new_title):
        dest_id = drive_service.files().copy(
            body={"name": new_title},
            fileId=source_id,
        ).execute().get('id')
        # Move to the DESTINATION_FOLDER
        drive_service.files()\
            .update(fileId=dest_id, addParents=destination_folder_id, fields='id, parents')\
            .execute()
        return dest_id

    def import_profiles(self):
        with open('/home/sri/apps/charcha/hashers.latest.json') as f:
            engineering_profiles = json.load(f)

        profile_builder = HasherProfileBuilder(engineering_profiles)
        for email in profile_builder.emails:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warn("Email " + email + " does not exist in Charcha database")
                continue
            bio = profile_builder.profile(email)
            slide_object_id = profile_builder.slide_object_id(email)
            UserProfile.objects.update_or_create(user=user, defaults={'bio': bio, 'slide_object_id': slide_object_id})

class HasherProfileBuilder:
    def __init__(self, presentation):
        self.presentation = presentation
        self.slides_by_email = self._index_slide_by_email()

    @property
    def emails(self):
        return self.slides_by_email.keys()

    @property
    def slides(self):
        return self.presentation['slides']

    def _slide_for_email(self, raw_email):
        email = self._normalize_email(raw_email)
        if not email:
            raise Exception("Not a valid email " + raw_email)
        if email not in self.slides_by_email:
            raise Exception("Email " + email + " not found in presentation")
        return self.slides_by_email[email]

    def _skip_text(self, text):
        if not text:
            return False

        # Many people copied from Khozaif's slide, and then marked this text invisible somehow
        # But the text exists in the slide, and is not relevant.
        if 'Khozaif is a reliable' in text:
            return True
        elif 'short bio' in text.lower() and len(text) < 15:
            return True
        elif 'photo' in text.lower() and len(text) < 8:
            return True
        return False

    def slide_object_id(self, email):
        slide = self._slide_for_email(email)
        return slide['objectId']
        
    def profile(self, email):
        slide = self._slide_for_email(email)
        
        profile = ""
        count_empty_string = 0
        for text in self._text_in_slide(slide):
            if self._skip_text(text):
                continue
            if not text.strip():
                count_empty_string += 1
            else:
                count_empty_string = 0
            
            if text.endswith('\n'):
                text += '\n'
            
            # >2 consecutive new line characters are combined into 2 new lines
            if count_empty_string > 2:
                continue
            profile += text

        # Convert the text to html using markdown
        return markdown2.markdown(profile)
            
    def _text_in_slide(self, slide):
        slide_id = slide['objectId']
        for pe in slide['pageElements']:
            if 'shape' in pe:
                shape = pe['shape']
                if shape['shapeType'] == 'TEXT_BOX' and 'text' in shape and 'textElements' in shape['text']:
                    for te in shape['text']['textElements']:
                        if 'textRun' in te:
                            yield te['textRun']['content']

    def _index_slide_by_email(self):
        slide_by_email = {}
        for slide in self.slides:
            notes = []
            notes_page_elements = get_nested(slide, 'slideProperties.notesPage.pageElements')
            if not notes_page_elements:
                continue
            for pe in notes_page_elements:
                text_elements = get_nested(pe, 'shape.text.textElements')
                if not text_elements:
                    continue
                for te in text_elements:
                    text = get_nested(te, 'textRun.content')
                    if not text:
                        continue
                    notes.append(text)
            
            raw_email = "".join(notes).strip()
            email = self._normalize_email(raw_email)
            if email:
                slide_by_email[email] = slide
        
        return slide_by_email

    def _normalize_email(self, raw_email):
        '''
        Input => Rashmi Ranjan <rashmi.ranjan@hashedin.com>
        Output => rashmi.ranjan@hashedin.com
        '''
        m = re.search(r"[\s<]?([a-zA-Z0-9\._-]+@hashedin.com)", raw_email)
        if m:
            return m.group(1).lower()

        return None

def _load_google_credentials():
    keyfile_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', None)
    if not keyfile_str:
        logger.warn("Environment variable GOOGLE_SERVICE_ACCOUNT_JSON not found.")
        return None
    
    service_account_info = json.loads(keyfile_str)
    scopes = ['https://www.googleapis.com/auth/drive.metadata', 'https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=scopes)
    
    return credentials

def _polyjuice_potion(base_credentials, email, api, version):
    'impersonate another user using delegated credentials'
    delegated_credentials = base_credentials.with_subject(email)
    # drive_client = googleapiclient.discovery.build('drive', 'v3', credentials=delegated_credentials)
    # slides_client = googleapiclient.discovery.build('slides', 'v1', credentials=delegated_credentials)
    # return (drive_client, slides_client)
    return googleapiclient.discovery.build(api, version, credentials=delegated_credentials)

# def _load_slide_client():
#     keyfile_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', None)
#     if not keyfile_str:
#         logger.warn("Environment variable GOOGLE_SERVICE_ACCOUNT_JSON not found. \
#             Disabling notifications via google chatbot")
#         return None
    
#     keyfile_dict = json.loads(keyfile_str)
#     scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/presentations']
#     credentials = ServiceAccountCredentials.from_json_keyfile_dict(
#         keyfile_dict, scopes)
#     slides_client = build('slides', 'v1', http=credentials.authorize(Http()))
#     return slides_client

def get_nested(obj, path):
    tokens = path.split('.')
    for token in tokens:
        if token in obj:
            obj = obj[token]
        else:
            return None
    return obj

def download_presentation():
    client = _load_slide_client()
    response = client.presentations().get(presentationId='1k9fzHK_SDtsWnFwyOdx_Tr0uNP-E3Ea4KAZ1eV77WCw').execute()
    with open('/home/sri/apps/charcha/hashers.latest.json', 'w') as f:
        f.write(json.dumps(response))

def sub_lists(accumulator, annotations, start, end):
    if end - start <= 1:
        return None
    else:
        mid = (start + end) // 2
        accumulator.append(annotations[start:mid])
        accumulator.append(annotations[mid:end])
        sub_lists(accumulator, annotations, start, mid)
        sub_lists(accumulator, annotations, mid, end)
    return accumulator