import uuid
import jwt
import random

from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from rest_framework_jwt.utils import jwt_payload_handler

from .utils import *

# Create your models here.

class MyUserManager(BaseUserManager):

    def create_superuser(self, user_name, password):
        user = self.model(user_name=user_name)
        user.set_password(password)
        user.is_superuser = True
        user.is_active = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_user(self, user_name, password=None, username=''):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not user_name:
            raise ValueError('Users must have an user name')

        user = self.model(
            user_name=self.user_name,
            is_active=False,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

class MyUsers(AbstractBaseUser):
	"""
		User information
	"""
	TYPE_OF_ACCOUNT = (
        ("Public", "Public"),
        ("Private", "Private"),
    )
	DEVICE_TYPE = (
		("Ios","Ios"),
		("Android","Android"),
	)
	SOCIAL_TYPE = (
		("Facebook","Facebook"),
		("Google","Google"),
	)
	country_code = models.CharField(
		"country Code", max_length=10, blank=True, null=True
	)
	email_address = models.EmailField(
		"Email Address", unique=True, max_length=50, validators=[EMAILREGEX], null=True, blank=True
	)
	mobile_number = models.CharField(
		"Mobile Number", max_length=16, blank=True, null=True
	)
	mobile_number_verify = models.BooleanField(
		"Mobile number verify", default=False
	)
	name = models.CharField(
        "Name", max_length=100, blank=True, null=True
    )
	uuid = models.UUIDField(
        default=uuid.uuid4, editable=False
    )
	user_name = models.TextField(
    	"User Name", unique=True
	)
	accepting_terms = models.BooleanField(
        "Terms & Condition", default=False
    )
	device_id = models.TextField(
    	"Device id"
	)
	about_me = models.TextField(
		"About me", blank=True, null=True
	)
	age = models.IntegerField(
		"Age", default=0
	)
	gender = models.CharField(
		"Gender", max_length=20, blank=True, null=True
	)
	image = models.TextField(
		"image", blank=True, null=True
	)
	device_type = models.CharField(
		"Device Type", max_length=20, choices=DEVICE_TYPE, default="Android"
	)
	social_type = models.CharField(
		"Social Type", max_length=30,choices=SOCIAL_TYPE, default="Google"
	)
	type_of_Account = models.CharField(
		"Type of Account", default="Public", max_length=20, choices=TYPE_OF_ACCOUNT
	)
	is_superuser = models.BooleanField(
        "Super User", default=False
    )
	is_staff = models.BooleanField(
        "Staff", default=False
    )
	is_active = models.BooleanField(
        "Status", default=False
    )
	otp = models.CharField(
		"OTP",blank=True, null=True, max_length=7
	)
	is_online = models.BooleanField(
		"User is online", default=False
	)
	created_at = models.DateTimeField(
        "Created Date", auto_now_add=True
    )
	updated_at = models.DateTimeField(
        "Updated Date", auto_now=True
    )

	objects = MyUserManager()
	USERNAME_FIELD = 'user_name'

	def has_perm(self, perm, obj=None):
	    return self.is_staff

	def has_module_perms(self, app_label):
	    return self.is_superuser

	def get_short_name(self):
	    return self.user_name

	def create_jwt(self):
		"""Function for creating JWT for Authentication Purpose"""
		payload = jwt_payload_handler(self)
		token =  jwt.encode(payload, settings.SECRET_KEY)
		auth_token = token.decode('unicode_escape')
		return auth_token

	def __str__(self):
	    return self.user_name

	class Meta:
	    verbose_name = "User"
	    verbose_name_plural = "User"

class UserNewToken(models.Model):
    token = models.TextField(blank=True,null=True)
    user = models.ForeignKey(MyUsers, related_name="token_user", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("token", "user")

class videoAudio(models.Model):
	"""
		User Video Audio
	"""
	user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='user_video_Audio', blank=True,null=True
	)
	audio = models.TextField(
		"Video voice"
	)
	title = models.TextField(
		"Audio Title", blank=True, null=True
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __str__(self):
	    return self.user.user_name

	class Meta:
		verbose_name_plural = "User Videos Audio"
		ordering = ("-created_at",)

class UserVideo(models.Model):
	"""
		Save user uploaded value
	"""
	TYPE_OF_VIDEO = (
        ("Public", "Public"),
        ("Private", "Private"),
    )
	user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='video_user', blank=True,null=True
	)
	video = models.TextField(
		'User Videos', blank=True, null=True
	)
	description = models.TextField(
		"Video Description", blank=True, null=True
	)
	Views_count = models.BigIntegerField(
		"Total Views Count", default=0
	)
	type_of_video = models.CharField(
		"Type of video", max_length=20, default="Public", choices=TYPE_OF_VIDEO
	)
	video_title = models.CharField(
		"Video Title", max_length=225, null=True, blank=True
	)
	video_tag = models.CharField(
		"Video tag", max_length=225, null=True, blank=True
	)
	video_voice = models.ForeignKey(
		videoAudio, on_delete=models.CASCADE, related_name='video_audio', blank=True,null=True
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __str__(self):
	    return self.user.user_name

	class Meta:
		verbose_name_plural = "User Videos"
		ordering = ("-updated_at",)

class UserVideoLikeAction(models.Model):
	"""
		User Video likes
	"""
	video_id =  models.ForeignKey(
		UserVideo, on_delete=models.CASCADE, related_name='liked_video'
	)
	liked_by = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='liked_by_user',
	)
	like = models.BooleanField(
		"User likes", default=True
	) 
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __str__(self):
	    return self.video_id.user.user_name
	class Meta:
		verbose_name_plural = "Videos likes"
		ordering = ("-created_at",)

class UserVideoDislikeAction(models.Model):
	"""
		User Video likes
	"""
	video_id =  models.ForeignKey(
		UserVideo, on_delete=models.CASCADE, related_name='disliked_video'
	)
	disliked_by = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='disliked_by_user',
	)
	dislike = models.BooleanField(
		"User dislikes", default=True
	) 
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __str__(self):
	    return self.video_id.user.user_name
	class Meta:
		verbose_name_plural = "Videos Dislikes"
		ordering = ("-created_at",)

class UserVideosCommentAction(models.Model):
	"""
		User comments on video
	"""
	video_id =  models.ForeignKey(
		UserVideo, on_delete=models.CASCADE, related_name='commented_on_video'
	)
	comment_by = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='comment_by_user',
	)
	comment = models.TextField(
		"User comment of video", blank=True, null=True
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __Str__(self):
		return self.video_id

	class Meta:
		verbose_name_plural = "Videos Comment"
		ordering = ("-updated_at",)

class UserCommentReply(models.Model):
	"""
		Reply of Comments
	"""
	comment_id = models.ForeignKey(
		UserVideosCommentAction, on_delete=models.CASCADE, related_name='comment_reply'
	)
	reply_by = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='reply_by_user', blank=True, null=True
	)
	comment = models.TextField(
		"User comment of video"
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __Str__(self):
		return self.comment_id

	class Meta:
		verbose_name_plural = "Videos Comment Reply"
		ordering = ("-updated_at",)

class ShareVideo(models.Model):
	"""
		Share user video
	"""
	share_by = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='share_by_user', blank=True, null=True
	)
	video_id =  models.ForeignKey(
		UserVideo, on_delete=models.CASCADE, related_name='shared_video'
	)
	share_count = models.BigIntegerField(
		"Total share count", default=0
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __str__(self):
	    return self.video_id.user.user_name
	class Meta:
		verbose_name_plural = "Share User Video"
		ordering = ("-created_at",)

class CommentsActions(models.Model):
	"""
		Actions for main comment or comment Reply
	"""
	comment_id = models.ForeignKey(
		UserVideosCommentAction, on_delete=models.CASCADE, related_name='main_comment_action', blank=True, null=True
	)
	reply_id = models.ForeignKey(
		UserCommentReply, on_delete=models.CASCADE, related_name='reply_comment_action', blank=True, null=True
	)
	action = models.CharField(
		"Actions of comment", max_length=20, blank=True, null=True
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __Str__(self):
		return self.id

	class Meta:
		verbose_name_plural = "Videos Comment or Reply Action"

class UserFollowingOrFollwed(models.Model):
	"""
		Following of user or Followed of user Model
	"""
	TYPE_OF_REQUEST = (
		('Pending','Pending'),
		('Approved','Approved')
	)
	following_by_user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name="following_by_user"
	)
	followed_user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name="following_user"
	)
	type_of_request = models.CharField(
		"Type of Request", default="Approved", max_length=20, choices=TYPE_OF_REQUEST
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __Str__(self):
		return self.id

	class Meta:
		verbose_name_plural = "Account Following or Followed User"
		ordering = ("-created_at",)

class Notification(models.Model):
	"""
		Notification
	"""
	STATUS = (
        ("Comment", "Comment"),
        ("Like", "Like"),
        ("Follow Request", "Follow Request"),
        ("Follow Approve", "Follow Approve"),
        ("Comment Reply", "Comment Reply"),
        ("Dislike", "Dislike"),
        ("Following", "Following")
    )
	from_user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name="from_user"
	)
	to_user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name="to_user"
	)
	description = models.TextField(
		"Notification description"
	)
	seen = models.BooleanField(
		"Notification seen", default=False
	)
	type_of_notification = models.CharField(
		"Type of Notification", max_length=50, choices=STATUS
	) 
	type_of_notification_id = models.IntegerField(
		"Type notification id"
	)
	read = models.BooleanField(
		"Notification read", default=False
	)
	is_clear = models.BooleanField(
		"Clear Notification", default=False
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	def __str__(self):
		return self.id

	class Meta:
		verbose_name_plural = "Notification"
		ordering = ("-created_at",)

class ChatList(models.Model):
    """Chat list for admin and merchant chat"""
    sender = models.ForeignKey(
    	MyUsers, on_delete=models.CASCADE, related_name='chat_sender'
	)
    receiver = models.ForeignKey(
    	MyUsers, on_delete=models.CASCADE, related_name='chat_receiver'
	)
    sender_deleted = models.BooleanField(
    	default=False
	)
    receiver_deleted = models.BooleanField(
    	default=False
	)
    created_at = models.DateTimeField(
    	"Created Date", auto_now_add=True
	)
    updated_at = models.DateTimeField(
    	"Updated Date", auto_now=True
	)

    class Meta:
        verbose_name_plural = "Chat List"
        ordering = ('-created_at',)
        unique_together = [['sender','receiver',]]

class Chats(models.Model):

    chat = models.ForeignKey(
    	ChatList, on_delete=models.CASCADE, related_name='chatlist'
	)
    sender = models.ForeignKey(
    	MyUsers, on_delete=models.CASCADE, related_name='chatsender'
	)
    receiver = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='chatreceiver'
	)
    message = models.TextField(
    	"Message"
	)
    sender_deleted = models.BooleanField(
		default=False
	)
    receiver_deleted = models.BooleanField(
    	default=False
	)
    is_seen = models.BooleanField(
        default=False
    )
    created_at = models.DateTimeField(
        "Created Date", auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "Updated Date", auto_now=True
    )

    class Meta:
        verbose_name_plural = "User Chats"
        ordering = ('-created_at',)

class CardDetail(models.Model):
	"""
		User card detail
	"""
	user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='card_user'
	)
	card_id = models.CharField(
		"user card Unique id", max_length=100
	)
	crad_holder_name = models.CharField(
		"Card Holder name", max_length=100,blank=True,null=True
	)
	card_number = models.CharField(
		"Card Number", max_length=20
	)
	card_last4_number = models.CharField(
		"Card last 4 digit", max_length=4,blank=True,null=True
	)
	card_network = models.CharField(
		"Card Network", max_length=100
	)
	card_expiry_date = models.CharField(
		"Card Expiry date", max_length=10
	)
	created_at = models.DateTimeField(
	    "Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
	    "Updated Date", auto_now=True
	)

	class Meta:
	    verbose_name_plural = "User Card Detail"
	    ordering = ('-created_at',)

class PaymentDetail(models.Model):
	"""
		Paymant detail
	"""
	ORDER_STATE = (
		("Created","Created"),
		("Attempted","Attempted"),
		("Paid","Paid"),
	)
	sender = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='senderpayment'
	)
	receiver = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='receiverpayment'
	)
	order_id = models.CharField(
		"Payment order id", max_length=100
	)
	order_currency = models.CharField(
		"order currency",max_length=20, blank=True, null=True
	)
	order_status = models.CharField(
		"Order Status", max_length=20, choices=ORDER_STATE, default="Created"
	)
	payment_attempts = models.IntegerField(
		"Payment attempts on particular order id", default=0
	)
	payment_id = models.CharField(
		"payment id", max_length=100, blank=True, null=True
	)
	payment_verify = models.BooleanField(
		"Verify payment signature", default=False
	)
	payment_signature = models.TextField(
		"Payment signature",blank=True,null=True
	)
	type_of_payment = models.CharField(
		"Type of payment",max_length=20,blank=True,null=True
	)
	amount = models.IntegerField(
		"amount"
	)
	payment_capture = models.BooleanField(
		"Payment capture", default=False
	)
	created_at = models.DateTimeField(
	    "Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
	    "Updated Date", auto_now=True
	)

	class Meta:
		verbose_name_plural = "User payment Detail"
		ordering = ('-updated_at',)

class WalletDetail(models.Model):
	"""
		User wallet detail
	"""
	TYPE_OF_COLLECTION = (
		("Wallet","Wallet"),
		("My Collection", "My Collection")
	)
	user = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='user_wallet'
	)
	total_coin  = models.IntegerField(
		"User coin"
	)
	type_of_coin = models.CharField(
		"Type of coin collection", choices=TYPE_OF_COLLECTION, default="Wallet", max_length=20
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	class Meta:
		verbose_name_plural = "User wallet Detail"
		ordering = ('created_at',)

class CoinSharingHistory(models.Model):
	"""
		Coin Sharing History
	"""
	sender = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='coin_sender'
	)
	receiver = models.ForeignKey(
		MyUsers, on_delete=models.CASCADE, related_name='coin_receiver'
	)
	coin = models.IntegerField(
		"Sharing coin"
	)
	created_at = models.DateTimeField(
		"Created Date", auto_now_add=True
	)
	updated_at = models.DateTimeField(
		"Updated Date", auto_now=True
	)

	class Meta:
		verbose_name_plural = "Coin Sharing History"
		ordering = ('-created_at',)