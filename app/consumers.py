import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.db.models import Q

from .models import *
# from customer.models import OrderList

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        params = self.scope['url_route']['kwargs']
        print("URL" , params)
        self.sender = params['sender']
        self.receiver = params['receiver']
        self.room_name = 'chat_{}_{}'.format(self.sender,self.receiver)
        # Join room group
        try:
            pass
            user = MyUsers.objects.get(id=params['sender'])
            user.is_online = True
            user.save()
        except:
           pass
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        params = self.scope['url_route']['kwargs']
        print("URL" , params)
        self.sender = params['sender']
        self.receiver = params['receiver']
        self.room_name = 'chat_{}_{}'.format(self.sender,self.receiver)
        try:
            pass
            user = MyUsers.objects.get(id=params['sender'])
            user.is_online = False
            user.save()
        except:
           pass
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        params = self.scope['url_route']['kwargs']
        print("URL" , params)
        payload = json.loads(text_data)
        print(payload)
        message = payload['message']
        self.sender = MyUsers.objects.get(id=params['sender'])
        self.receiver = MyUsers.objects.get(id=params['receiver'])
        try:
            obj = ChatList.objects.get(
                Q(sender=self.sender, receiver=self.receiver) |
                Q(sender=self.receiver, receiver=self.sender)
            )
        except:
            obj = ChatList.objects.create(
                sender=self.sender,
                receiver=self.receiver
            )
        Chats.objects.create(

            chat=obj,
            sender=self.sender,
            receiver=self.receiver,
            message=message,
            is_seen=True if not self.receiver.is_online else False,
        )

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.sender.id,
                'receiver_id': self.receiver.id
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id']
        }))