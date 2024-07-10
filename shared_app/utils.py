import re

import vonage


def validate_phone(phone_number):
    pattern = "^\\+?\\d{1,4}?[-.\\s]?\\(?\\d{1,3}?\\)?[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,9}$"
    return bool(re.match(pattern, phone_number))


def validate_email(email):
    pattern = (r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*["
               r"a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
    return bool(re.match(pattern, email))


def validate_email_or_phone(auth_type_input):
    if validate_email(auth_type_input):
        return 'email'
    elif validate_phone(auth_type_input):
        return 'phone'
    else:
        return None


# Twilio
# from twilio.rest import Client

# account_sid = settings.TWILIO_ACCOUNT_SID
# auth_token = settings.TWILIO_AUTH_TOKEN
# account_sid_conf = config('TWILIO_ACCOUNT_SID')
# auth_token_conf = config('TWILIO_AUTH_TOKEN')


# def send_sms(to_number, body):

# Initialize Twilio client
#  = Client(account_sid, auth_token)
#
# # Send SMS
# message = client.messages.create(
#     body=body,
#     from_='+12513062962',
#     to=to_number
# )

# return message.sid

client = vonage.Client(key="f7661299", secret="Tzv1Ugay7myzHtFK")
sms = vonage.Sms(client)


def send_sms_vonage(to_number, body):
    response = sms.send_message(
        {
            "from": "Vonage team!!!",
            "to": to_number,
            "text": body,
        }
    )

    if response["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {response['messages'][0]['error-text']}")

    return response
