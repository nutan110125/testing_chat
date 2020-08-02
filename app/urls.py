from django.urls import path
from .views import *

urlpatterns = [
	#User Registration.
	path('user_register', UserUpdateThirdStepView.as_view()),
	
	path('login', LoginWithEmailView.as_view()),
	path('login_with_mobile_number', LoginWithMobileView.as_view()),
	path('verify_otp', VerifyOtp.as_view()),
	
	path('user_profile', UserProfileView.as_view()),
	path('redirect_user_profile', RedirectUserDetail.as_view()),
	
	path('video', UploadVideosApi.as_view()),
	path('all_video', GetAllVideosApi.as_view()),
	path('action_on_video', ActionOnVideoApi.as_view()),
	path('liked_video_user', GetAllVideoLikeByUser.as_view()),
	path('view_action_on_video', ViewActionOfVideo.as_view()),
	path('share_video', ShareUserVideoApi.as_view()),
	path('videos_according_to_views', VideosAccordingToViews.as_view()),

	path('video_comment', CommentApi.as_view()),
	path('video_comment_reply', CommentedReplyApi.as_view()),
	
	path('following_user', FollowingUserRequest.as_view()),
	path('pending_following_list', ListOfPendingFollowingRequest.as_view()),
	path('followed_list', ListOfApprovedFollowedUser.as_view()),
	path('approved_following_list', ListOfApprovedFollowingUser.as_view()),

	path('count_notification', CountNotification.as_view()),
	path('view_notification', viewsNotification.as_view()),

	path('search', SearchApi.as_view()),

	path('user_detail', UserDetail.as_view()),
	path('video_tag', VideoDetail.as_view()),

	path('chat_list', ChatListApi.as_view()),
	path('all_chat', AllChatList.as_view()),

	path('create_order', CreatUserOrder.as_view()),
	path('verify_payment_signature', VerifyPayment.as_view()),
	path('payment', PaymentCaptureApi.as_view()),
	path('all_payment', GetAllPaymentDetail.as_view()),
	path('all_card', GetAllCardDetail.as_view()),

	path('wallet_detail', GetwalletDetail.as_view()),
	path('share_coin', ShareCoin.as_view()),

	path('', index, name='index'),
	path('audio', FetchAudioApi.as_view()),
]