from .bot import notify_space
from django.core.mail import send_mail
from bleach.sanitizer import Cleaner

plain_text_cleaner = Cleaner(tags=[], attributes={}, strip=True)
html_cleaner = Cleaner(
    tags=['a', 'b', 'em', 'i', 'strong', 'p', 'br'
    ],
    attributes={
        "a": ("href",),
    },
    strip=True
)


def notify_via_email(email, event):
    # skip sending emails for now till we remove our sandbox restrictions
    pass
    # html = "<b>" + event['line1'] + "</b><br/>"
    # html += "<p>" + event['line2'] + "</p><br/>"
    # html += "<a href='" + event['link'] + "'>" + event['link_title'] + "</a>"
    # cleaned_html = html_cleaner.clean(html)
    # plaintext = plain_text_cleaner.clean(html)
    # send_mail(
    #     subject=event['heading'] + ' ' + event['sub_heading'],
    #     from_email='noreply-charcha@hashedin.com',
    #     recipient_list=[email],
    #     fail_silently=False,
    #     message=plaintext,
    #     html_message=cleaned_html
    # )

def notify_user(user, event):
    if user.gchat_space:
        notify_space(user.gchat_space, event)
        
    if user.email:
        notify_via_email(user.email, event)
