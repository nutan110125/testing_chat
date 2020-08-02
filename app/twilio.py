import os
import random
from twilio.rest import Client

account_sid = 'AC6129ffdba308c55a33279be9cba974f5'
auth_token = 'f4d81d9328a6d6dadd420e2660a79a6a'
client = Client(account_sid, auth_token)


def twillio_message(mobile_no,user):
    try:
        code = str(''.join([str(random.randint(0, 9)) for _ in range(6)]))
        message = client.messages.create(
            body='<#>{0} is your Penut Account Verification code.waX1n5c9+Pz'.format(code),
            from_="+12514281143",
            to=mobile_no
        )
        user.otp = code
        user.save()
        return {"service_sid":message.sid,"status":True}
    except Exception as e:
        return {"message":e.__str__(),"status":False}
