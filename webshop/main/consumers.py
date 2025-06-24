import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

class MultiplayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'multiplayer_%s' % self.room_name

        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'player_progress':
            # Broadcast player progress to all in room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_progress',
                    'username': data['username'],
                    'progress': data['progress'],
                    'wpm': data['wpm'],
                    'accuracy': data['accuracy']
                }
            )
        elif message_type == 'game_start':
            # Start game for all in room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_start',
                    'text': data['text'],
                    'duration': data['duration']
                }
            )

    async def player_progress(self, event):
        # Send player progress to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'player_progress',
            'username': event['username'],
            'progress': event['progress'],
            'wpm': event['wpm'],
            'accuracy': event['accuracy']
        }))

    async def game_start(self, event):
        # Send game start to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'game_start',
            'text': event['text'],
            'duration': event['duration']
        }))