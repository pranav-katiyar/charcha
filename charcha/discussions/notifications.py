from .bot import notify_space
from django.core.mail import send_mail
from bleach.sanitizer import Cleaner
from django import template

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
    event = event.copy()
    event['line2'] = html_cleaner.clean(event['line2'])
    
    t = template.loader.get_template("emails/email_notification.html")
    html = t.render({"event": event})
    plaintext = plain_text_cleaner.clean(html)
    send_mail(
        subject=event['heading'] + ' ' + event['sub_heading'],
        from_email='noreply-charcha@hashedin.com',
        recipient_list=[email],
        fail_silently=False,
        message=plaintext,
        html_message=html
    )

def notify_user(user, event):
    if user.gchat_space:
        notify_space(user.gchat_space, event)
        
    if user.email:
        notify_via_email(user.email, event)
