from .models import *
from .utils import *

from django.db.models import Avg, Count, Min, Sum

from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .pagination import *

#--------------------User Serializers create, Update user ------------------------------------------------------#
class UserSignupSerializers(serializers.ModelSerializer):
    """
        MyUsers Serializer with required fields and vakidation.
    """
    first_name = serializers.CharField(max_length=40, required=False, validators=[NAMEREGEX])
    last_name = serializers.CharField(max_length=40, required=False, validators=[NAMEREGEX])
    country_code = serializers.CharField(max_length=5, required=False, validators=[COUNTRYCODEREGEX])
    device_id = serializers.CharField(max_length=100,required=True)
    user_name = serializers.CharField(max_length=150,required=False)

    def create(self, validated_data):
        if 'device_id' not in validated_data or validated_data['device_id'] == "" or 'accepting_terms' not in validated_data or validated_data['accepting_terms'] == "":
            raise serializers.ValidationError({"error": "Device id or Acceptance Terms  is compulsory."})
        validated_data['user_name'] = "user_"+validated_data['device_id']

        instance = MyUsers.objects.create(**validated_data)
        instance.user_name = instance.user_name+"_"+str(instance.id)
        instance.set_password(instance.user_name)
        instance.save()
        return instance

    class Meta:
        model = MyUsers
        fields = ('id','uuid', 'name', 'country_code', 'mobile_number', 'user_name','accepting_terms',
                  'about_me','device_id','age','image','type_of_Account','gender','mobile_number_verify')

#----------------User Profile Serializers-----------------------------------------------------------------------#
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for editing user profile."""
    count_following_by_user = SerializerMethodField('following_by_user_count')
    count_followed_user = SerializerMethodField('Followed_user_count')
    total_like = SerializerMethodField('get_total_like')

    def following_by_user_count(self,obj):
        return UserFollowingOrFollwed.objects.filter(followed_user=obj,type_of_request='Approved').count()

    def Followed_user_count(self,obj):
        return UserFollowingOrFollwed.objects.filter(following_by_user=obj,type_of_request='Approved').count()

    def get_total_like(self,obj):
        like_obj = UserVideoLikeAction.objects.filter(video_id__user=obj).count()
        return like_obj
            
    class Meta:
        model = MyUsers
        exclude = ('password','is_staff','is_active','is_superuser','otp','last_login','created_at','updated_at')

#-------------------Following User Serializers------------------------------------------------------------------#
class FollowingUserSerializer(serializers.ModelSerializer):
    """
        Following User Serializers
    """
    following_by_user_detail = UserProfileSerializer(source='following_by_user',read_only=True)
    followed_user_detail = UserProfileSerializer(source='followed_user', read_only=True)
    class Meta:
        model = UserFollowingOrFollwed
        fields = '__all__'

#--------------------------------Following User list Detail-----------------------------------------------------#
class FollowingSerializer(serializers.ModelSerializer):
    """
        Following list serializers
    """
    following_by_user_detail = UserProfileSerializer(source='following_by_user',read_only=True)
    class Meta:
        model = UserFollowingOrFollwed
        exclude = ('followed_user',)

class FollowingRequestUserSerializer(serializers.ModelSerializer):
    """
        Pending Following List User Detail
    """
    following_by_user = SerializerMethodField('get_following_bt_user')

    def get_following_bt_user(self,followed_user):
        obj = UserFollowingOrFollwed.objects.filter(followed_user=followed_user,type_of_request='Pending')
        serializer = FollowingSerializer(instance=obj, many=True)
        return serializer.data

    class Meta:
        model = MyUsers
        exclude = ('password','is_staff','is_active','is_superuser','otp','last_login','created_at','updated_at')

class ApprovedFollowingUserSerializer(serializers.ModelSerializer):
    """
        Approved Following List User Detail
    """
    following_by_user = SerializerMethodField('get_following_by_user')

    def get_following_by_user(self,followed_user):
        obj = UserFollowingOrFollwed.objects.filter(followed_user=followed_user,type_of_request='Approved')
        serializer = FollowingSerializer(instance=obj, many=True)
        return serializer.data

    class Meta:
        model = MyUsers
        exclude = ('password','is_staff','is_active','is_superuser','otp','last_login','created_at','updated_at')
#-----------------------------Followed user list Detail---------------------------------------------------------#
class FollowedSerializer(serializers.ModelSerializer):
    """
        Followed user list
    """
    followed_user_detail = UserProfileSerializer(source='followed_user',read_only=True)
    class Meta:
        model = UserFollowingOrFollwed
        exclude = ('following_by_user',)

class FollowedRequestUserSerializer(serializers.ModelSerializer):
    """
        Following List User Detail
    """
    followed_user = SerializerMethodField('get_followed_user')

    def get_followed_user(self,following_by_user):
        obj = UserFollowingOrFollwed.objects.filter(following_by_user=following_by_user,type_of_request='Approved')
        serializer = FollowedSerializer(instance=obj, many=True)
        return serializer.data

    class Meta:
        model = MyUsers
        exclude = ('password','is_staff','is_active','is_superuser','otp','last_login','created_at','updated_at')

#-------------------------Get All Videos without login----------------------------------------------------------#
class VideoUserDetailSerializers(serializers.ModelSerializer):

    count_following_by_user = SerializerMethodField('following_by_user_count')
    def following_by_user_count(self,obj):
        return UserFollowingOrFollwed.objects.filter(followed_user=obj,type_of_request='Approved').count()
    class Meta:
        model = MyUsers
        fields = ("image",'name','user_name','id','count_following_by_user')

class VideoAudioDetailSerializers(serializers.ModelSerializer):
    audio_user_detail = VideoUserDetailSerializers(source='user',read_only=True)
    audio_used_count = SerializerMethodField('user_audio_used_count')

    def user_audio_used_count(self,obj):
        total = UserVideo.objects.filter(video_voice=obj).count()
        if total:
            return total
        else:
            return 0

    class Meta:
        model = videoAudio
        exclude = ('created_at','updated_at')

class GetAllVideosSerializers(serializers.ModelSerializer):
    count_like = SerializerMethodField('liked_video_count')
    count_dislike = SerializerMethodField('disliked_video_count')
    count_share = SerializerMethodField('shared_video_count')
    count_comment = SerializerMethodField('commented_on_video_count')
    user_detail = VideoUserDetailSerializers(source='user',read_only=True)
    user_like = SerializerMethodField("get_user_like")
    user_dislike = SerializerMethodField("get_user_dislike")
    video_voice_detail = VideoAudioDetailSerializers(source='video_voice', read_only=True)

    def get_user_like(self,obj):
        user = self.context.get('user')
        like_obj = UserVideoLikeAction.objects.filter(liked_by=user,video_id=obj).first()
        if like_obj:
            return True
        return False

    def get_user_dislike(self,obj):
        user = self.context.get('user')
        like_obj = UserVideoDislikeAction.objects.filter(disliked_by=user,video_id=obj).first()
        if like_obj:
            return True
        return False

    def shared_video_count(self,obj):
        total = ShareVideo.objects.filter(video_id=obj).aggregate(Sum('share_count'))['share_count__sum']
        if total:
            return total
        else:
            return 0 

    def liked_video_count(self,obj):
        return UserVideoLikeAction.objects.filter(video_id=obj).count()

    def disliked_video_count(self,obj):
        return UserVideoDislikeAction.objects.filter(video_id=obj).count()

    def commented_on_video_count(self,obj):
        return UserVideosCommentAction.objects.filter(video_id=obj).count()

    class Meta:
        model = UserVideo
        exclude = ('created_at','updated_at','type_of_video')

#----------------------------------------Get All User Who liked Video-------------------------------------------#
class VideoLikedUserSerializers(serializers.ModelSerializer):
    user_detail = VideoUserDetailSerializers(source='liked_by',read_only=True)
    class Meta:
        model = UserVideoLikeAction
        exclude = ('created_at','updated_at','video_id')

class GetAllUserOflikedVideo(serializers.ModelSerializer):

    video_liked_user = SerializerMethodField('get_video_liked_user')

    def get_video_liked_user(self,obj):
        user_obj = UserVideoLikeAction.objects.filter(video_id=obj)
        serializer = VideoLikedUserSerializers(instance=user_obj, many=True)
        return serializer.data

    class Meta:
        model = UserVideo
        exclude = ('created_at','updated_at','type_of_video')

#------------------------------Comment on Video Serializers-----------------------------------------------------#
class CommentedVideoDetail(serializers.ModelSerializer):
    count_like = SerializerMethodField('liked_video_count')
    count_dislike = SerializerMethodField('disliked_video_count')
    count_comment = SerializerMethodField('commented_on_video_count')
    user_detail = VideoUserDetailSerializers(source='user',read_only=True)

    def liked_video_count(self,obj):
        return UserVideoLikeAction.objects.filter(video_id=obj).count()

    def disliked_video_count(self,obj):
        return UserVideoDislikeAction.objects.filter(video_id=obj).count()

    def commented_on_video_count(self,obj):
        return UserVideosCommentAction.objects.filter(video_id=obj).count()

    class Meta:
        model = UserVideo
        exclude = ('created_at','updated_at','type_of_video')

class CommentReplyDetail(serializers.ModelSerializer):
    reply_by_user = VideoUserDetailSerializers(source='reply_by',read_only=True)
    class Meta:
        model = UserCommentReply
        exclude = ('created_at','updated_at')

class CommentOnVideoSerializers(serializers.ModelSerializer):
    commented_user = VideoUserDetailSerializers(source='comment_by',read_only=True)
    comment_reply = SerializerMethodField('get_comment_reply')


    def get_comment_reply(self,obj):
        comment_obj = UserCommentReply.objects.filter(comment_id=obj)
        serializer = CommentReplyDetail(instance=comment_obj,many=True)
        return serializer.data

    class Meta:
        model = UserVideosCommentAction
        exclude = ('created_at','updated_at')

#----------------------Notification Serializer-----------------------------------------------------------------#
class GetAllNotification(serializers.ModelSerializer):
    from_user_detail = VideoUserDetailSerializers(source='from_user',read_only=True)
    to_user_detail = VideoUserDetailSerializers(source='to_user',read_only=True)
    class Meta:
        model = Notification
        exclude = ("created_at","updated_at")

#---------------------------------------Get Redirect User------------------------------------------------------#
class UserRedirectProfileSerializer(serializers.ModelSerializer):
    """Serializer for editing user profile."""
    count_following_by_user = SerializerMethodField('following_by_user_count')
    count_followed_user = SerializerMethodField('Followed_user_count')
    total_like = SerializerMethodField('get_total_like')
    is_following = SerializerMethodField('get_is_following')
    is_followed = SerializerMethodField('get_is_followed')

    def following_by_user_count(self,obj):
        return UserFollowingOrFollwed.objects.filter(followed_user=obj,type_of_request='Approved').count()

    def Followed_user_count(self,obj):
        return UserFollowingOrFollwed.objects.filter(following_by_user=obj,type_of_request='Approved').count()

    def get_total_like(self,obj):
        like_obj = UserVideoLikeAction.objects.filter(video_id__user=obj).count()
        return like_obj

    def get_is_following(self,obj):
        user = self.context.get('user')
        user_obj = UserFollowingOrFollwed.objects.filter(following_by_user=user,followed_user=obj).first()
        if user_obj:
            return True
        else:
            return False

    def get_is_followed(self,obj):
        user = self.context.get('user')
        user_obj = UserFollowingOrFollwed.objects.filter(following_by_user=obj,followed_user=user).first()
        if user_obj:
            return True
        else:
            return False
            
    class Meta:
        model = MyUsers
        exclude = ('password','is_staff','is_active','is_superuser','otp','last_login','created_at','updated_at')

#------------------------------------------Share Video Serializer----------------------------------------------#
class ShareVideoSerializers(serializers.ModelSerializer):
    video_detail = CommentedVideoDetail(source='video_id', read_only=True)
    share_by_user_detail = VideoUserDetailSerializers(source='share_by',read_only=True)
    class Meta:
        model = ShareVideo
        fields = '__all__'

class VideosharedUserSerializers(serializers.ModelSerializer):
    user_detail = VideoUserDetailSerializers(source='share_by',read_only=True)
    class Meta:
        model = ShareVideo
        exclude = ('created_at','updated_at','video_id')

class GetAllUserOfSharedVideo(serializers.ModelSerializer):

    video_share_user = SerializerMethodField('get_video_shared_user')

    def get_video_shared_user(self,obj):
        user_obj = ShareVideo.objects.filter(video_id=obj)
        serializer = VideosharedUserSerializers(instance=user_obj, many=True)
        return serializer.data

    class Meta:
        model = UserVideo
        exclude = ('created_at','updated_at','type_of_video')

#----------------------------------------Chat Serilizers-------------------------------------------------------#
class ChatListUserDetailSerializers(serializers.ModelSerializer):

    class Meta:
        model = MyUsers
        fields = ("image",'name','user_name','id')

class ChatListSerializers(serializers.ModelSerializer):
    sender_user_detail = ChatListUserDetailSerializers(source='sender',read_only=True)
    receiver_user_detail = ChatListUserDetailSerializers(source='receiver',read_only=True)
    count_unseen_message = SerializerMethodField('get_message_count')

    def get_message_count(self,obj):
        user = self.context.get('user')
        unseen_message_count = Chats.objects.filter(chat=obj,receiver=user,is_seen=False).count()
        return unseen_message_count 

    class Meta:
        model = ChatList
        fields = '__all__'

class ChatSerializers(serializers.ModelSerializer):
    sender_user_detail = ChatListUserDetailSerializers(source='sender',read_only=True)
    receiver_user_detail = ChatListUserDetailSerializers(source='receiver',read_only=True)
    class Meta:
        model = Chats
        fields = '__all__'

#------------------------------------------Video tag-----------------------------------------------------------#
class GetAllVideosTagSerializers(serializers.ModelSerializer):

    class Meta:
        model = UserVideo
        fields = ('id','video_tag')

#----------------------User Video Detail-----------------------------------------------------------------------------#
class VideoSerializers(serializers.ModelSerializer):
    video_user_detail = VideoUserDetailSerializers(source='user',read_only=True)
    video_voice_detail = VideoAudioDetailSerializers(source='video_voice', read_only=True)
    class Meta:
        model = UserVideo
        exclude = ('created_at','updated_at')

class LikedVideoSerilaizers(serializers.ModelSerializer):
    video_detail = VideoSerializers(source='video_id',read_only=True)

    class Meta:
        model = UserVideoLikeAction
        exclude = ('created_at','updated_at')

class AllUserVideoSerializers(serializers.ModelSerializer):

    class Meta:
        model = MyUsers
        fields = ('id','user_name','email_address','image')


#-------------------------------------------------Payment Detail----------------------------------------------------#
class AllPaymentSerializers(serializers.ModelSerializer):
    class Meta:
        model = PaymentDetail
        exclude = ('created_at','updated_at')

class AllCardDetailSerializers(serializers.ModelSerializer):
    class Meta:
        model = CardDetail
        exclude = ('created_at','updated_at')

#-----------------------------Audio Detail---------------------------------------------------------------------------#
class AudioUser(serializers.ModelSerializer):
    class Meta:
        model = MyUsers
        fields = ('id','image','name','user_name')

class AudioSerializers(serializers.ModelSerializer):
    user_detail = AudioUser(source='user',read_only=True)
    class Meta:
        model = videoAudio
        fields = '__all__'

#----------------------------------Share coin history-----------------------------------------------------------------#
class ShareHistorySerializers(serializers.ModelSerializer):
    sender_detail = AudioUser(source='sender',read_only=True)
    receiver_detail = AudioUser(source='receiver',read_only=True)
    action = SerializerMethodField('get_share_coin_action')

    def get_share_coin_action(self,obj):
        user = self.context.get('user')
        if obj.sender == user:
            return "Send"
        else:
            return "received"

    class Meta:
        model = CoinSharingHistory
        fields = '__all__'