import time

from django.conf import settings
from pyfcm import FCMNotification

from .models import *

push_service_ios = FCMNotification(
    api_key="AAAAuul4XmI:APA91bGvXXRia5AAVsunlXawSET-gc0JA42zffvdbcaw5Pv2s_y0QwfCgIkJuL_dHOb1gsEk4aqz158MUFJX6IQ1S-GFg4AM31o0L6Tn3OvPtdT5zz9WgUv6mcnLfWxw8lhQDJA8Upso"
)
push_service_android = FCMNotification(
  api_key="AAAAuul4XmI:APA91bGvXXRia5AAVsunlXawSET-gc0JA42zffvdbcaw5Pv2s_y0QwfCgIkJuL_dHOb1gsEk4aqz158MUFJX6IQ1S-GFg4AM31o0L6Tn3OvPtdT5zz9WgUv6mcnLfWxw8lhQDJA8Upso"
)

def send_notification(device_id):
    print("device id", device_id)
    message_title = "Notification"
    message_body = "Hope you're having fun this weekend, don't forget to check today's news"
    result = push_service.notify_multiple_devices(registration_ids=[device_id], message_title=message_title,
                                                  message_body=message_body)
    return result


def send_request_notification(data):
    try:
      print("PUSH NOTIFICATION")
      message_title = "Penut g update"
      message_body = data['description']
      notification_obj = Notification.objects.create(
        from_user=data['from_user'],to_user=data['to_user'],description=data['description'],
        type_of_notification=data['type_of_notification'],type_of_notification_id=data['type_of_notification_id']
      )
      if data['device_type'] == "Ios":
        result = push_service_ios.notify_single_device(
          registration_id="dSwY4MB-Q_q107vBuUjwnt:APA91bE_Yhj1-vn0ycgdwucYPPKbP5hGEk6MKPuNCJHfJ6JxKfNzMlhKWmxFnlvjk5Qqt8yssKdZRZyqs-BRboqsHdNb9yzJcSMMt-yHZV1Ri1iqXVU4sO0gTY-p_xHPzTCz7IkefwnC", 
          message_title=message_title,
          message_body=message_body,
          data_message={
             "title": message_title,
             "icon": "icon_resource",
             "sound": "alert.mp3",
             "type": notification_obj.type_of_notification,
             'notification_id': notification_obj.id,
         }
        )
      else:
        result = push_service_android.notify_single_device(
          registration_id=data['device_id'], 
          message_title=message_title,
          message_body=message_body,
          data_message={
             "title": message_title,
             "icon": "icon_resource",
             "sound": "alert.mp3",
             "type": notification_obj.type_of_notification,
             'notification_id': notification_obj.id,
         }
        )
      print("RESULT",result)
      return {"result":result,"status":True}
    except Exception as e:
      return {"status":False,"message":e.__str__()}

# def send_request1_notification():
#     try:
#       import pdb
#       pdb.set_trace()
#       print("PUSH NOTIFICATION")
#       message_title = "Penut g update"
#       message_body = "hello"        
#       result = push_service_android.notify_single_device(
#         registration_id="dSwY4MB-Q_q107vBuUjwnt:APA91bE_Yhj1-vn0ycgdwucYPPKbP5hGEk6MKPuNCJHfJ6JxKfNzMlhKWmxFnlvjk5Qqt8yssKdZRZyqs-BRboqsHdNb9yzJcSMMt-yHZV1Ri1iqXVU4sO0gTY-p_xHPzTCz7IkefwnC", 
#         message_title=message_title,
#         message_body=message_body
#       )
#       print("RESULT",result)
#       return {"result":result,"status":True}
#     except Exception as e:
#       return {"status":False,"message":e.__str__()}

# send_request1_notification()