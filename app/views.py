import uuid, os
import jwt
import boto3
import random
import base64
import requests

from django.conf import settings
from django.contrib.auth import authenticate,login,logout
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from boto3.s3.transfer import TransferConfig
from datetime import datetime,timedelta

from .serializers import *
from .twilio import *
from .utils import *
from .models import *
from .permission import *
from .pagination import *
from .pyfcm import *
from .payment import *

import logging
logging.basicConfig()
# Get an instance of a logger
logger = logging.getLogger(__name__)
client = boto3.client('s3', region_name='ap-south-1', aws_access_key_id=S3_bucket_access_token,
	                      aws_secret_access_key=S3_bucket_secret_access_token)

def upload_file_to_s3(file_name, bucket, object_name):
	"""Upload a file to S3 bucket"""
	if object_name is None:
	    object_name = file_name
	try:
	    response = client.upload_file(file_name, bucket,
	                                  object_name, ExtraArgs={'ACL': 'public-read'})
	except ClientError as e:
	    logging.error(e)
	    return e
	return response

def upload_image(image):
	if image.startswith('data:image/png;base64'):
	    replace_base64_content = image.replace('data:image/png;base64', "")
	    file_name = str(random.random()) +'.jpg'
	else:
	    if image.startswith('data:image/jpeg;base64'):
	        replace_base64_content = image.replace('data:image/jpeg;base64', "")
	        file_name =  str(random.random()) +'.png'
	data = replace_base64_content
	imgdata = base64.b64decode(data)
	local_path = 'app/staticfiles/static/upload_image/' +file_name
	with open(local_path, 'wb') as f:
	    f.write(imgdata)
	s3_path = "upload_image/"+file_name
	response = client.generate_presigned_post(S3_bucket_name, s3_path,ExpiresIn=60)
	print(response)
	with open(local_path, "rb") as fh:
		files = {'file': (local_path, fh)}
		try:
			data = response['fields']
			r = requests.post(response['url'], data=data, files=files)
			print(r.status_code)
		finally:
			fh.close()
	os.remove(local_path)
	file_url = S3_bucket_video_url +s3_path
	# upload_file_to_s3(local_path,S3_bucket_name,'upload_image/'+file_name)
	file_url = S3_bucket_video_url +s3_path
	return file_url

def update_profile(user,params):
	user.mobile_number = params['mobile_number']
	user.mobile_number_verify = params['mobile_number_verify']
	user.first_name = params['first_name']
	user.last_name = params['last_name']
	if user.user_name != params['user_name']:
		user.user_name = params['user_name'] 
	user.about_me = params['about_me']
	user.age = params['age']
	user.gender = params['gender']
	user.type_of_Account = "Private" if params['type_of_Account'] == 'private' else 'Public'
	user.is_active = True if params['mobile_number_verify'] else False
	user.country_code = params['country_code']
	user.set_password(user.user_name)
	if params['image']:
		image = params['image']
		if params['image']:
			image = params['image']
			user.image = upload_image(image) 
	user.save()
	return user

def walletDetail(user,amount):
	try:
		coin = 0
		if amount == 10:
			coin = 8
		elif amount == 20:
			coin = 16
		elif amount == 40:
			coin = 32
		elif amount == 80:
			coin=65
		elif amount == 100:
			coin=90
		elif amount == 500:
			coin = 500
		wallet_obj = WalletDetail.objects.filter(user=user).first()
		if wallet_obj:
			wallet_obj.total_coin = wallet_obj.total_coin+coin
		else:
			wallet_obj = WalletDetail.objects.create(user=user,total_coin=coin)
		return {"status":True,"total_coin":wallet_obj.total_coin}
	except Exception as e:
		return {"status":False,"message":e.__str__()}

class LoginWithEmailView(APIView):
	"""
		Login Api
	"""
	def post(self, request):
		try:
			data = request.data
			if 'email_address' not in data or data['email_address'] == "":
				return Response(
					{
					"status":False,
					"message":"Something went wrong!",
					"error":{"type":"validation_Error","message":"Email Address is compulsory."}
					},status=status.HTTP_400_BAD_REQUEST)
			if 'device_id' not in data or data['device_id'] == "":
				return Response(
					{
					"status":False,
					"message":"Something went wrong!",
					"error":{"type":"validation_Error","message":"Device id is compulsory."}
					},status=status.HTTP_400_BAD_REQUEST)
			if 'device_type' not in data and data['device_type'] == "":
				return Response(
					{
					"status":False,
					"message":"Something went wrong!",
					"error":{"type":"validation_Error","message":"Device Type is compulsory."}
					},status=status.HTTP_400_BAD_REQUEST)
			user = MyUsers.objects.filter(email_address=data['email_address']).first()
			status_obj = ""
			message = ""
			user_exist = False
			if user:
				if user.device_id != data['device_id']:
					logout(request)
					user.device_id = data['device_id']
					if data['device_type'] == "ios":
						user.device_type="Ios"
					else:
						user.device_type="Android"
					user.save()
				if user.age:
					status_obj = True
					message = "Logged In Successfully."
					user_exist = True
				else:
					status_obj = True
					message = "User Age does not exist."
					user_exist = False
			else:
				if data['device_type'] == "ios":
					device_type="Ios"
				else:
					device_type="Android"
				file_name = random.randint(000,9999999999)
				user_name = "user"+str(file_name)+"_"
				user = MyUsers.objects.create(
					email_address=data['email_address'],device_id=data['device_id'],user_name=user_name,device_type=device_type
				)
				user.user_name = user.user_name+str(user.id)
				user.set_password(user.user_name)
				user.is_active = True
				user.save()
				status_obj = True
				message = "User Age does not exist."
				user_exist = False
			user_obj = authenticate(user_name=user.user_name,password=user.user_name)
			if user_obj:
				login(request,user_obj)
				token = user_obj.create_jwt()
				token_obj = UserNewToken.objects.filter(user=user).first()
				if token_obj:
					token_obj.token = token
					token_obj.save()
				else:
					UserNewToken.objects.create(user=user,token=token)
				return Response({
					"status":status_obj,
					"message": message,
					"code":200,
					"token":token,
					"user_id":user_obj.id,
					"user_exist":user_exist
				}, status=status.HTTP_200_OK)
			return Response({
				"status":status_obj,
				"message":message,
				"code":400,
				"user_id":user.id,
				"user_exist":user_exist	
			},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
		    return Response({
				"status":False,
				"code":400,
				"message":"Something went wrong!",
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class LoginWithMobileView(APIView):
	"""
		Login Api
	"""
	def post(self, request):
		try:
			data = request.data
			if 'country_code' not in data or data['country_code'] == "":
				return Response(
					{
					"status":False,
					"message":"Something went wrong!","error":{"type":"validation_Error","message":"Country Code is compulsory."}
					},status=status.HTTP_400_BAD_REQUEST)
			if 'mobile_number' not in data or data['mobile_number'] == "":
				return Response(
					{
					"status":False,
					"message":"Something went wrong!","error":{"type":"validation_Error","message":"Mobile number is compulsory."}
					},status=status.HTTP_400_BAD_REQUEST)
			if 'device_id' not in data or data['device_id'] == "":
				return Response(
					{
					"status":False,
					"message":"Something went wrong!","error":{"type":"validation_Error","message":"Device id is compulsory."}
					},status=status.HTTP_400_BAD_REQUEST)
			user = MyUsers.objects.filter(mobile_number=data['mobile_number']).first()
			status_obj = ""
			message = ""
			user_exist = False
			if user:
				if user.device_id != data['device_id']:
					logout(request)
					user.device_id = data['device_id']
					user.save()
				if user.country_code != data['country_code']:
					user.country_code = data['country_code']
					user.save()
				if user.age:
					status_obj = True
					message = "Logged In Successfully."
					user_exist = True
				else:
					status_obj = False
					message = "User Age does not exist."
					user_exist = False
			else:
				user_name = "user"+data['device_id']+"_"
				user = MyUsers.objects.create(
					mobile_number=data['mobile_number'],device_id=data['device_id'],user_name=user_name,country_code=data['country_code'])
				user.user_name = user.user_name+str(user.id)
				user.set_password(user.user_name)
				user.is_active = True
				user.save()
				status_obj = False
				message = "User does not exist."
				user_exist = False
			user_obj = authenticate(user_name=user.user_name,password=user.user_name)
			mobile_info = user.country_code+user.mobile_number
			if user_obj:
				login(request,user_obj)
				# message_obj = twillio_message(mobile_info,user_obj)
				token = user_obj.create_jwt()
				token_obj = UserNewToken.objects.filter(user=user).first()
				if token_obj:
					token_obj.token = token
					token_obj.save()
				else:
					UserNewToken.objects.create(user=user,token=token)
				# if message_obj['status']:
				return Response({
					"status":status_obj,
					"message": message,
					"code":200,
					"token":token,
					"user_id":user_obj.id,
					"user_exist":user_exist
				}, status=status.HTTP_200_OK)
				# else:
				# 	return Response({
				# 		"status":False,
				# 		"message":message_obj['message'],
				# 		"error":{"type":"Exception","message":"Twilio error"}	
				# 	},status=status.HTTP_400_BAD_REQUEST)
			message_obj = twillio_message(mobile_info,user)
			if message_obj['status']:
				return Response({
				"status":status_obj,
				"message":message,
				"code":400,
				"user_id":user.id,
				"user_exist":user_exist	
				},status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({
					"status":False,
					"message":message_obj['message'],
					"error":{"type":"Exception","message":"Twilio error"}	
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
		    return Response(
					{
					"status":False,
					"message":"Something went wrong!","error":{"type":"validation_Error","message":e.__str__()}
					},status=status.HTTP_400_BAD_REQUEST)

class VerifyOtp(APIView):
	"""
		Verify code.
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			params = request.data
			if 'code' not in params or params['code'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Code is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if request.user.otp == params['code']:
				request.user.mobile_number_verify = True
				request.user.save()
				return Response({
					"status":True,
					"message":"Your mobile number is verified successfully.",
					"code":200	
				},status=status.HTTP_200_OK)
			else:
				return Response({
					"status":False,
					"message":"Verification code is incorrect."	,
					"code":400
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			}, status=status.HTTP_400_BAD_REQUEST)

class UserUpdateThirdStepView(APIView):
	"""
	    User Manual Signup View
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			params = request.data
			if 'name' not in params or params['name'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Name is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'age' not in params or params['age'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Age is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'gender' not in params or params['gender'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Gender is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'accepting_terms' not in params or params['accepting_terms'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Accepting terms is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			request.user.age = params['age']
			request.user.gender = params['gender']
			request.user.name = params['name']
			request.user.accepting_terms = params['accepting_terms']
			request.user.save()
			serializers = UserProfileSerializer(request.user)
			return Response({
				"status":True,
				"message":"User Register Successfully.",
				"code":200,
				"data":serializers.data	
			})
		except Exception as e:
			return Response({
				"status":False,
				"message":e.__str__(),
				"code":400,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
	"""
		Update profile view
	"""
	permission_classes = (IsTokenValid,)
	def put(self,request):
		try:
			params = request.data
			if 'mobile_number' not in params or params['mobile_number'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Mobile Number is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'name' not in params or params['name'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Name is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'age' not in params or params['age'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Age is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'gender' not in params or params['gender'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Gender is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'country_code' not in params or params['country_code'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Country Code is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'type_of_Account' not in params or params['type_of_Account'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Type of account is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'user_name' not in params or params['user_name'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"User Name is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			request.user.name = params['name']
			request.user.age = params['age']
			request.user.user_name = params['user_name']
			request.user.gender = params['gender']
			request.user.country_code = params['country_code']
			request.user.mobile_number = params['mobile_number']
			request.user.about_me = params['about_me']
			if params['type_of_Account'].lower() == 'private':
				request.user.type_of_Account = 'Private'
			else:
				request.user.type_of_Account = 'Public'
			request.user.set_password(request.user.user_name)
			if params['image']:
				image = params['image']
				if params['image']:
					image = params['image']
					request.user.image = upload_image(image) 
			request.user.save()
			serializers = UserProfileSerializer(request.user)
			return Response({
				"status":True,
				"code":200,
				"message":"User Profile updated successfully.",
				"data":serializers.data	
			},status=status.HTTP_200_OK)
		except Exception as e:
		    return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
	    	}, status=status.HTTP_400_BAD_REQUEST)
 
	def get(self,request):
		try:
			serializers = UserProfileSerializer(request.user)
			return Response({
				"status":True,
				"message": "Success.",
				"data":serializers.data,
				"code":200
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			}, status=status.HTTP_400_BAD_REQUEST)				

class UploadVideosApi(APIView):
	"""
		Get,Upload and delete user video.
	"""
	permission_classes = (IsTokenValid,)
	parser_classes = (MultiPartParser, FormParser)
	def post(self,request):
		try:
			if 'video' not in request.data or not request.data['video']:
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"video is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'video_title' not in request.data or request.data['video_title'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"video title is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			video = request.FILES.get('video',False)
			file_name = random.randint(000,9999999999)
			file_path_within_bucket = 'inputs/{file_name}.mp4'.format(file_name=str(file_name))
			path = default_storage.save(file_path_within_bucket, ContentFile(video.read()))
			response = client.generate_presigned_post(video_s3_bucket_name, file_path_within_bucket,ExpiresIn=60)
			print(response)
			with open('mediafiles/'+file_path_within_bucket, "rb") as fh:
				files = {'file': (file_path_within_bucket, fh)}
				try:
					data = response['fields']
					r = requests.post(response['url'], data=data, files=files)
					print(r.status_code)
				finally:
					fh.close()
			video_file_url = s3_get_video_url +str(file_name)+".mp4"
			audio_file_url = s3_get_video_url +str(file_name)+".mp3"
			video_obj = UserVideo.objects.create(user=request.user,video=video_file_url,video_title=request.data['video_title'])
			if 'type_of_video' in request.data and request.data['type_of_video'] == 'private':
				video_obj.type_of_video = "Private"
			if 'description' in request.data:
				video_obj.description = request.data['description']
			if 'video_tag' in request.data:
				video_obj.video_tag = request.data['video_tag']
			if 'video_voice' in request.data and request.data['video_voice'] != "":
				audio_obj = videoAudio.objects.filter(audio=request.data['video_voice']).first()
				if audio_obj:
					video_obj.video_voice = audio_obj
			else:
				admin_user = MyUsers.objects.filter(email_address='admin@penutg.com').first()
				audio_obj = videoAudio.objects.create(user=admin_user,audio=audio_file_url,title=request.data['video_title'])
				video_obj.video_voice = audio_obj
			video_obj.save()
			serializers = VideoSerializers(video_obj)
			return Response({
				"status":True,
			    'message': 'Successfully video uploded.',
			    'data': serializers.data,
			    "code":200
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message":"Something Went Wrong!",
				"status":False,
				"code":400,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		try:
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			user_serializers = AllUserVideoSerializers(request.user)
			video_obj = UserVideo.objects.filter(user=request.user).all()
			limit = 20
			list2, page, paginator = paginatorData(video_obj, limit,  request.GET.get('page'))
			video_serializers = VideoSerializers(list2,many=True)
			user_video_liked = UserVideoLikeAction.objects.filter(liked_by=request.user).all()
			limit = 20
			list3, page, paginator = paginatorData(user_video_liked, limit,  request.GET.get('page'))
			liked_video_serializers = LikedVideoSerilaizers(list3,many=True)
			return Response({
					"status":True,
				    'message': 'User All Video.',
				    'data': {"user_detail":user_serializers.data,"user_video_detail":video_serializers.data,"user_liked_video":liked_video_serializers.data},
				    "code":200
				},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message":"Something Went Wrong!",
				"status":False,
				"code":400,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def delete(self,request):
		try:
			if not request.GET.get("id"):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"video id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			video_id = UserVideo.objects.filter(id=request.GET.get("id")).delete()
			serializers = AllUserVideoSerializers(request.user)
			return Response({
				"status":True,
				'message': 'User All Video.',
				'data': serializers.data,
				"code":200
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

	def put(self,request):
		try:
			if 'id' not in request.data or request.data['id'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"video id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'video_title' not in request.data or request.data['video_title'] == "":
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"video title is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.filter(id=request.data['id']).first()
			if video_obj:
				video_obj.description = request.data['description']
				if 'type_of_video' in request.data:
					if request.data['type_of_video'] == 'private':
						video_obj.type_of_video = "Private"
					else:
						video_obj.type_of_video = "Public"
				if 'description' in request.data:
					video_obj.description = request.data['description']
				if 'video_tag' in request.data:
					video_obj.video_tag = request.data['video_tag']
				video_obj.video_title = request.data['video_title']
				video_obj.save()
			serializers = VideoSerializers(video_obj)
			return Response({
				"status":True,
			    'message': 'Updated successfully.',
			    'data': serializers.data,
			    "code":200
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message":"Something Went Wrong!",
				"status":False,
				"code":400,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class GetAllVideosApi(APIView):
	"""
		Get All Video to Show
	"""
	permission_classes = (UserViewsPermission,)
	def get(self,request):
		try:
			if not  request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			instance = UserVideo.objects.filter(type_of_video="Public").all()
			limit = 20
			list2, page, paginator = paginatorData(instance, limit,  request.GET.get('page'))
			if request.user.is_authenticated:
				serializers = GetAllVideosSerializers(list2, many=True, context={"user":request.user})
			else:
				serializers = GetAllVideosSerializers(list2, many=True)
			return Response({
				"status":True,
				"code":200,
				"message":"All Video",
				"data":serializers.data	
			},status=status.HTTP_200_OK)

		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class RedirectUserDetail(APIView):
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			if not request.GET.get('id') and not request.GET.get('user_name'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"User name or id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":" page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if request.GET.get('id'):
				user_obj = MyUsers.objects.filter(id=request.GET.get('id')).first()
			else:
				user_obj = MyUsers.objects.filter(user_name=request.GET.get('user_name')).first()
			user_serializers = UserRedirectProfileSerializer(user_obj,context={"user":request.user})
			video_obj = UserVideo.objects.filter(user=user_obj).all()
			limit = 20
			list2, page, paginator = paginatorData(video_obj, limit,  request.GET.get('page'))
			video_serializers = VideoSerializers(list2,many=True)
			user_video_liked = UserVideoLikeAction.objects.filter(liked_by=user_obj).all()
			limit = 20
			list3, page, paginator = paginatorData(user_video_liked, limit,  request.GET.get('page'))
			liked_video_serializers = LikedVideoSerilaizers(list3,many=True)
			return Response({
				"status":True,
			    'message': 'Redirect user detail',
			    'data': {"user_detail":user_serializers.data,"user_video":video_serializers.data,"user_liked_video":liked_video_serializers.data},
			    "code":200
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class ActionOnVideoApi(APIView):
	"""
		Like,Dislike,Viewsand Comment on video
	"""
	permission_classes = (IsTokenValid,)
	def put(self,request):
		try:
			params = request.data
			if 'id' not in params or params['id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'action' not in params or params['action'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Action on video is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.filter(id=params['id']).first()
			if video_obj:
				if params['action'] == "dislike":
					UserVideoLikeAction.objects.filter(video_id=video_obj,liked_by=request.user).delete()
					dislike_obj = UserVideoDislikeAction.objects.create(video_id=video_obj,disliked_by=request.user)
				elif params['action'] == "dislike_remove":
					UserVideoDislikeAction.objects.filter(video_id=video_obj,disliked_by=request.user).delete()
				elif params['action'] == 'like':
					UserVideoDislikeAction.objects.filter(video_id=video_obj,disliked_by=request.user).delete()
					like_obj = UserVideoLikeAction.objects.create(video_id=video_obj,liked_by=request.user)
					name = request.user.name if request.user.name else request.user.user_name
					data = {
						"device_id":video_obj.user.device_id,
						"description":name + " has liked your video",
						"from_user":request.user,
						"to_user":video_obj.user,
						"type_of_notification":"Like",
						"type_of_notification_id":like_obj.id,
						"device_type":video_obj.user.device_type
					}
					notification_obj = send_request_notification(data)
					if not notification_obj['status']:
						return Response({
							"message": "Notification error.",
							"code":400,
							"status":False,
							"error":{"type":"Exception","message":notification_obj['message']}
						}, status=status.HTTP_400_BAD_REQUEST)
				else:
					like_obj = UserVideoLikeAction.objects.filter(video_id=video_obj,liked_by=request.user).delete()
				serializers = GetAllVideosSerializers(video_obj, context={"user":request.user})
				return Response({
					"status":True,
				    'message': 'Action Perform Successfully on this video.',
				    'data': serializers.data,
				    "code":200
				},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class ViewActionOfVideo(APIView):
	def get(self,request):
		try:
			if not request.GET.get('id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.filter(id=request.GET.get('id')).first()
			video_obj.Views_count = video_obj.Views_count+1
			video_obj.save()
			return Response({
				"status":True,
			    'message': 'Views done successfully',
			    'Views_count': video_obj.Views_count,
			    "code":200
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class GetAllVideoLikeByUser(APIView):
	"""
		Get All User Who liked particular video
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			video_id = request.GET.get('id')
			if not video_id:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.get(id=video_id)
			serializers = GetAllUserOflikedVideo(video_obj)
			return Response({
				"status":True,
				"code":200,
				"message":"All Users Who liked this video",
				"data":serializers.data	
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class CommentApi(APIView):
	"""
		Comments of video
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			params = request.data
			if 'id' not in params or params['id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'comment' not in params or params['comment'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Comment is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			comment_obj = UserVideosCommentAction.objects.create(comment_by=request.user,comment=params['comment'],video_id_id=params['id'])
			name = request.user.name if request.user.name else request.user.user_name
			data = {
				"device_id":comment_obj.video_id.user.device_id,
				"description":name + " has commented" +comment_obj.comment+ " your video",
				"from_user":request.user,
				"to_user":comment_obj.video_id.user,
				"type_of_notification":"Comment",
				"type_of_notification_id":comment_obj.id,
				"device_type":comment_obj.video_id.user.device_type
			}
			notification_obj = send_request_notification(data)
			if not notification_obj['status']:
				return Response({
					"message": "Notification error.",
					"code":400,
					"status":False,
					"error":{"type":"Exception","message":notification_obj['message']}
				}, status=status.HTTP_400_BAD_REQUEST)
			serializers = CommentOnVideoSerializers(comment_obj)
			return Response({
				"status":True,
				"code":200,
				"message":"Commented Video detail",
				"data":serializers.data	
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def put(self,request):
		try:
			params = request.data
			if 'id' not in params or params['id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Comment Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'comment' not in params or params['comment'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Comment is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			comment_obj = UserVideosCommentAction.objects.filter(id=params['id']).first()
			if comment_obj:
				comment_obj.comment = params['comment']
				comment_obj.save()
			serializers = CommentOnVideoSerializers(comment_obj)
			return Response({
				"status":True,
				"code":200,
				"message":"Commented Video detail",
				"data":serializers.data	
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		try:
			video_id = request.GET.get('id')
			if not video_id:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			comment_obj = UserVideosCommentAction.objects.filter(video_id=video_id).all()
			limit = 20
			list2, page, paginator = paginatorData(comment_obj, limit,  request.GET.get('page'))
			serializers = CommentOnVideoSerializers(list2,many=True)
			return Response({
				"status":True,
				"code":200,
				"message":"Commented Video detail",
				"data":serializers.data	
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def delete(self,request):
		try:
			if not request.GET.get('id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Comment Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			comment_obj = UserVideosCommentAction.objects.filter(id=request.GET.get('id'))
			if comment_obj.first():
				if comment_obj.first().comment_by == request.user:
					comment_obj.delete()
				else:
					return Response({
						"status":False,
						"code":400,
						"message":"You do not have permission to delete this comment."
					},status=status.HTTP_400_BAD_REQUEST)
			return Response({
				"status":True,
				"code":200,
				"message":"Comment deleted Successfully."
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class CommentedReplyApi(APIView):
	"""
		Comments Reply of video
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			params = request.data
			if 'id' not in params or params['id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Comment Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'reply' not in params or params['reply'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Reply is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			comment_obj = UserVideosCommentAction.objects.filter(id=params['id']).first()
			comment_reply_obj = UserCommentReply.objects.create(comment_id_id=params['id'],reply_by=request.user,comment=params['reply'])
			name = request.user.name if request.user.name else request.user.user_name
			data = {
				"device_id":comment_obj.video_id.user.device_id,
				"description":name + " has reply " +comment_reply_obj.comment+ " on your comment" + comment_obj.comment,
				"from_user":request.user,
				"to_user":comment_obj.video_id.user,
				"type_of_notification":"Comment Reply",
				"type_of_notification_id":comment_reply_obj.id,
				"device_type":comment_obj.video_id.user.device_type
			}
			notification_obj = send_request_notification(data)
			if not notification_obj['status']:
				return Response({
					"message": "Notification error.",
					"code":400,
					"status":False,
					"error":{"type":"Exception","message":notification_obj['message']}
				}, status=status.HTTP_400_BAD_REQUEST)
			serializers = CommentOnVideoSerializers(comment_obj)
			serializers = CommentOnVideoSerializers(comment_obj,many=True)
			return Response({
				"status":True,
				"code":200,
				"message":"Reply of comment done Successfully.",
				"data":serializers.data
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

	def put(self,request):
		try:
			params = request.data
			if 'id' not in params or params['id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Reply Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			if 'reply' not in params or params['reply'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"reply is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			reply_obj = UserCommentReply.objects.filter(id=params['id']).first()
			comment_obj = UserVideosCommentAction.objects.filter(id=reply_obj.comment_id.id)
			if reply_obj:
				reply_obj.comment = params['reply']
				reply_obj.save()
			serializers = CommentOnVideoSerializers(comment_obj,many=True)
			return Response({
				"status":True,
				"code":200,
				"message":"reply of comment has updated successfully.",
				"data":serializers.data	
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

	def delete(self,request):
		try:
			if not request.GET.get('id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Reply Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			comment_obj = UserCommentReply.objects.filter(id=request.GET.get('id'))
			if comment_obj.first():
				if comment_obj.first().reply_by == request.user:
					comment_obj.delete()
				else:
					return Response({
						"status":False,
						"code":400,
						"message":"You do not have permission to delete this comment."
					},status=status.HTTP_400_BAD_REQUEST)
			return Response({
				"status":True,
				"code":200,
				"message":"Reply deleted Successfully."
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class FollowingUserRequest(APIView):
	"""
		Following user Request with notification.
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			params = request.data
			if 'user_name' in params and params['user_name'] == "" or 'id' in params and params['id'] == "":
				return Response({
					"status":False,
					"code":400,
					"message":"Something Went Wrong!",
					"error":{"type":"Validation","message":"Id or uer name is compulsory for following."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'user_name' not in params and 'id' not in params:
				return Response({
					"status":False,
					"code":400,
					"message":"Something Went Wrong!",
					"error":{"type":"Validation","message":"Id or uer name is compulsory for following."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'user_name' in params:	
				following_user = MyUsers.objects.filter(user_name=params['user_name']).first()
			else:
				following_user = MyUsers.objects.filter(id=params['id']).first()
			if following_user:
				if following_user.type_of_Account == 'Private':
					type_of_request = 'Pending'
				else:
					type_of_request = 'Approved'
				already_sent_request = UserFollowingOrFollwed.objects.filter(following_by_user=request.user,followed_user_id=following_user.id).first()
				if not already_sent_request:
					follow_obj = UserFollowingOrFollwed.objects.create(
						following_by_user=request.user,followed_user=following_user,type_of_request=type_of_request
					)
					name = request.user.name if request.user.name else request.user.user_name
					if follow_obj.type_of_request == "Pending":
						data = {
							"device_id":follow_obj.followed_user.device_id,
							"description":name + " has request to follow you ",
							"from_user":request.user,
							"to_user":follow_obj.followed_user,
							"type_of_notification":"Follow Request",
							"type_of_notification_id":follow_obj.id,
							"device_type":follow_obj.followed_user.device_type
						}
					else:
						data = {
							"device_id":follow_obj.followed_user.device_id,
							"description":name + " has following you",
							"from_user":request.user,
							"to_user":follow_obj.followed_user,
							"type_of_notification":"Following",
							"type_of_notification_id":follow_obj.id,
							"device_type":follow_obj.followed_user.device_type
						}
					notification_obj = send_request_notification(data)
					if not notification_obj['status']:
						return Response({
							"message": "Notification error.",
							"code":400,
							"status":False,
							"error":{"type":"Exception","message":notification_obj['message']}
						}, status=status.HTTP_400_BAD_REQUEST)
					serializers = FollowingUserSerializer(follow_obj)
					return Response({
						"message":"Following Request send successfully.",
						"data":serializers.data,
						"code":200,
						"status":True
					},status=status.HTTP_200_OK)
				else:
					serializers = FollowingUserSerializer(already_sent_request)
					return Response({
						"message":"You are already following this user",
						"code":400,
						"data":serializers.data,
						"status":False
					},status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({
					"message":"No User Found for following.",
					"code":404,
					"status":False
				},status=status.HTTP_404_NOT_FOUND)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})
	
	def put(self,request):
		try:
			if 'id' not in request.data or request.data['id'] == "":
				return Response({
					"status":False,
					"code":400,
					"message":"Something Went Wrong!",
					"error":{"type":"Validation","message":"Request id is comuplsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			follow_obj = UserFollowingOrFollwed.objects.filter(id=request.data['id']).first()
			follow_obj.type_of_request = "Approved"		
			follow_obj.save()
			follow_back = UserFollowingOrFollwed.objects.filter(following_by_user=request.user,followed_user=follow_obj.following_by_user).first()
			name = request.user.name if request.user.name else request.user.user_name
			data = {
				"device_id":follow_obj.followed_user.device_id,
				"description":name + " has Approved your folloe request.",
				"from_user":request.user,
				"to_user":follow_obj.following_by_user,
				"type_of_notification":"Follow Approve",
				"type_of_notification_id":follow_obj.id,
				"device_type":follow_obj.following_by_user.device_type
			}
			notification_obj = send_request_notification(data)
			if not notification_obj['status']:
				return Response({
					"message": "Notification error.",
					"code":400,
					"status":False,
					"error":{"type":"Exception","message":notification_obj['message']}
				}, status=status.HTTP_400_BAD_REQUEST)
			serializers = FollowingUserSerializer(follow_obj)
			return Response({
				"message":"Following Request send successfully.",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
			serializers = FollowingUserSerializer(follow_obj)
			data = {
				"following_detail":serializers.data,
				"already_followed_by_following_user": True if  follow_back else False
			}
			return Response({
				"message":"Following Request Approved successfully.",
				"data":data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)	
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class ListOfPendingFollowingRequest(APIView):
	"""
		list of Pending  Following Request
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			serializers = FollowingRequestUserSerializer(request.user)
			return Response({
				"message":"Request list"
				,"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class ListOfApprovedFollowedUser(APIView):
	"""
		list of Following Request
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			serializers = FollowedRequestUserSerializer(request.user)
			return Response({
				"message":"Request list",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class ListOfApprovedFollowingUser(APIView):
	"""
		list of Approved Following Request
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			serializers = ApprovedFollowingUserSerializer(request.user)
			return Response({
				"message":"Request list",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class CountNotification(APIView):
	"""
		Count All not seen Notfication.
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			total_count = Notification.objects.filter(to_user=request.user,seen=False,is_clear=False).count()
			return Response({
				"message":"Request list",
				"data":total_count,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class viewsNotification(APIView):
	"""
		Count All not seen Notfication.
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			if not  request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)

			total_count = Notification.objects.filter(to_user=request.user,seen=False).update(seen=True,read=True)
			notification_obj = Notification.objects.filter(to_user=request.user,is_clear=False)
			limit = 30
			list2, page, paginator = paginatorData(notification_obj, limit,  request.GET.get('page'))
			serializers = GetAllNotification(list2, many=True)
			return Response({
				"message":"Request list",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

	def put(self,request):
		try:
			if not  request.data['page']:
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'clear_all' not in request.data or request.data['clear_all'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Clear all is comuplsory."}
				})
			if request.data['clear_all'] == False:
				if 'id' not in request.data or request.data['id'] == "":
					return Response({
						"message": "Something Went Wrong!",
						"code":400,
						"status":False,
						"error":{"type":"Validation","message":"Notification id is comuplsory."}
					})
				total_count = Notification.objects.filter(id=request.data['id']).update(is_clear=True)
			else:
				total_count = Notification.objects.filter(to_user=request.user).update(is_clear=True)
			notification_obj = Notification.objects.filter(to_user=request.user,is_clear=False)
			limit = 30
			list2, page, paginator = paginatorData(notification_obj, limit,  request.data['page'])
			serializers = GetAllNotification(list2, many=True)
			return Response({
				"message":"Request list",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			})

class SearchApi(APIView):
	"""
		Search
	"""
	def get(self,request):
		try:
			key = request.GET.get('search_key')
			page = request.GET.get('page')
			if not key:
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Key is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if not page:
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if key.startswith("@"):
				user_name = key[1:]
				user_obj = MyUsers.objects.filter(
					Q(user_name__icontains=user_name) | Q(email_address__icontains=user_name) | Q(name__icontains=user_name)
				).all()
				limit = 20
				list2, page, paginator = paginatorData(user_obj, limit,page)
				serializers = UserRedirectProfileSerializer(list2,many=True)
				return Response({
					"message":"Search Result",
					"data":{"user_data":serializers.data,"video_data":[]},
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)
			elif key.startswith("#"):
				video_obj = UserVideo.objects.filter(video_tag__icontains=key,type_of_video="Public").all()
				limit = 20
				list2, page, paginator = paginatorData(video_obj, limit,page)
				serializers = GetAllVideosSerializers(list2, many=True)
				return Response({
					"message":"Search Result",
					"data":{"user_data":[],"video_data":serializers.data},
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)
			else:
				user_obj = MyUsers.objects.filter(Q(user_name__icontains=key) | Q(name__icontains=key) | Q(email_address__icontains=user_name)).all()
				limit = 20
				list2, page, paginator = paginatorData(user_obj, limit,page)
				user_serializers = UserRedirectProfileSerializer(list2,many=True)
				video_obj = UserVideo.objects.filter(Q(Q(video_tag__icontains=key) | Q(description__contains=key) | Q(video_title__contains=key)) & Q(type_of_video="Public")).all()
				limit = 20
				list3, page, paginator = paginatorData(video_obj, limit,page)
				video_serializers = GetAllVideosSerializers(list3, many=True)
				return Response({
					"message":"Search Result",
					"data":{"user_data":user_serializers.data,"video_data":video_serializers.data},
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)

		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class ShareUserVideoApi(APIView):
	"""
		Share User video
	"""
	permission_classes = (IsTokenValid,)
	def post(self, request):
		try:
			params = request.data
			if 'id' not in params or params['id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.filter(id=params['id']).first()
			if video_obj:
				share_obj = ShareVideo.objects.filter(share_by=request.user,video_id=video_obj).first()
				if share_obj:
					share_obj.share_count = share_obj.share_count+1
					share_obj.save()
				else:
					share_obj = ShareVideo.objects.create(share_by=request.user,video_id=video_obj,share_count=1)
				serializers = ShareVideoSerializers(share_obj)
				return Response({
					"message":"Shared video detail",
					"data":serializers.data,
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)
			else:
				return Response({
					"message":"Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Vakidation","message":"No Video Found with provided id."}
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		try:
			if not request.GET.get('id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Video Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.filter(id=request.GET.get('id')).first()
			serializers = GetAllUserOfSharedVideo(video_obj)
			return Response({
				"message":"Share video user detail",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class ChatListApi(APIView):
	"""
      Chat list of user
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			page = request.GET.get('page')
			if not page:
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			chat_list_obj = ChatList.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).all()
			limit = 30
			list2, page, paginator = paginatorData(chat_list_obj, limit,page)
			serializers = ChatListSerializers(chat_list_obj,many=True,context={"user":request.user})
			return Response({
				"message":"User Chat list.",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class AllChatList(APIView):
	"""
		All message of user
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			if not request.GET.get('id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Chat list Id is compulsory."}
				}, status=status.HTTP_400_BAD_REQUEST)
			page = request.GET.get('page')
			if not page:
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			chat_list_obj = ChatList.objects.filter(id=request.GET.get('id')).first()
			chat_update_obj = Chats.objects.filter(chat=chat_list_obj,receiver=request.user).update(is_seen=True)
			chat_obj = Chats.objects.filter(chat=chat_list_obj).all()
			limit = 30
			list2, page, paginator = paginatorData(chat_obj, limit,page)
			serializers = ChatSerializers(list2,many=True)
			return Response({
				"message":"All User Chat.",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class VideosAccordingToViews(APIView):
	"""
		Get data according to views
	"""
	def get(Self,request):
		try:
			video_obj = UserVideo.objects.filter(type_of_video="Public").order_by('-Views_count')
			limit = 20
			list2, page, paginator = paginatorData(video_obj, limit,1)
			serializers = GetAllVideosSerializers(list2, many=True)
			return Response({
				"message":"Search Result",
				"data":{"user_data":[],"video_data":serializers.data},
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class UserDetail(APIView):
	"""
		User detail
	"""
	def get(self,request):
		try:
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			user_obj = MyUsers.objects.all()
			limit = 100
			list2, page, paginator = paginatorData(user_obj, limit,request.GET.get('page'))
			serializers = VideoUserDetailSerializers(list2,many=True)
			return Response({
				"message":"User Detail",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class VideoDetail(APIView):
	"""
		All Video Tag
	"""
	def get(self,request):
		try:
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			video_obj = UserVideo.objects.filter(type_of_video="Public")
			limit = 100
			list2, page, paginator = paginatorData(video_obj, limit,1)
			serializers = GetAllVideosTagSerializers(list2, many=True)
			return Response({
				"message":"Search Result",
				"data":serializers.data,
				"code":200,
				"status":True
			},status=status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class CreatUserOrder(APIView):
	"""
		Create user payment
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			params = request.data	
			if 'amount' not in params or params['amount'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Amount is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'order_currency' not in params or params['order_currency'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Order Currency is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			params['sender'] = request.user
			params['receiver'] = MyUsers.objects.filter(email_address='admin@penutg.com').first()
			order_detail_obj = create_order(params)
			if order_detail_obj['status']:
				return Response({
					"message":"Order detail",
					"data":order_detail_obj['razorpay_response'],
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)
			else:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"payment Gateway Exception","message":order_detail_obj['message']}
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		try:
			if not request.GET.get('id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Order id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			order_detail = get_order_detail(request.GET.get('id'))
			if order_detail['status']:
				return Response({
					"message":"Order detail",
					"data":order_detail['razorpay_response'],
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)
			else:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"payment Gateway Exception","message":order_detail['message']}
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class VerifyPayment(APIView):
	"""
		Verify razor pay signature.
	"""
	def post(self,request):
		try:
			data = request.data
			if 'razorpay_order_id' not in data or data['razorpay_order_id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Razorpay order id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'razorpay_payment_id' not in data or data['razorpay_payment_id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Razorpay payment id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'razorpay_signature' not in data or data['razorpay_signature'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Razorpay signature is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			verify_obj = verify_payment(data)
			if verify_obj['status']:
				return Response({
					"message":"payment signature verify successfully.",
					"data":verify_obj['razorpay_response'],
					"code":200,
					"status":True
				},status=status.HTTP_200_OK)
			else:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"payment Gateway Exception","message":verify_obj['message']}
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class PaymentCaptureApi(APIView):
	"""
		Payment related Api
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			data = request.data
			if 'payment_id' not in data or data['payment_id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Payment id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'order_id' not in data or data['order_id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Order id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'payment_currency' not in data or data['payment_currency'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Payment Currency is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'amount' not in data or data['amount'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Amount is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			payment_detail = PaymentDetail.objects.filter(sender=request.user,order_id=data['order_id']).first()
			params = {
				"payment_id":data['payment_id'],
				"payment_amount": data['amount'],
				"payment_currency":data['payment_currency']
			}
			capture_detail = capture_payment(params)
			if capture_detail['status']:
				payment_detail.payment_id = data['payment_id']
				payment_detail.order_status = "Paid"
				payment_detail.type_of_payment = capture_detail['razorpay_response']['method']
				payment_detail.payment_capture = capture_detail['razorpay_response']['captured']
				payment_detail.save()
				total_coin = walletDetail(request.user,payment_detail.amount)
				if total_coin['status']:
					return Response({
						"message":"payment captured Successfully.",
						"data":{"payment_detail":capture_detail['razorpay_response'],"total_coin":total_coin['total_coin']},
						"code":200,
						"status":True
					},status=status.HTTP_200_OK)
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Wallet Exception","message":total_coin['message']}
				},status=status.HTTP_400_BAD_REQUEST)	
			else:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"payment Gateway Exception","message":capture_detail['message']}
				},status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		try:
			if not request.GET.get('payment_id'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Payment id is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			payment_detail = get_payment_detail(request.GET.get('payment_id'))
			if payment_detail['status']:
				return Response({
					"status":True,
					"code":200,
					"data":payment_detail['razorpay_response']
				},status=status.HTTP_200_OK)
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Payment Gateway Exception","message":payment_detail['message']}
			})
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class GetAllPaymentDetail(APIView):
	"""
		Get all payment detail
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			serializers = AllPaymentSerializers(PaymentDetail.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).all(), many=True)
			return Response({
				"status":True,
				"code":200,
				"data":serializers.data
			},status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class GetAllCardDetail(APIView):
	"""
		Get all payment detail
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			serializers = AllCardDetailSerializers(CardDetail.objects.filter(user=request.user).all(), many=True)
			return Response({
				"status":True,
				"code":200,
				"data":serializers.data
			},status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class GetwalletDetail(APIView):
	"""
		Get all payment detail
	"""
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			wallet_obj = WalletDetail.objects.filter(user=request.user,type_of_coin='Wallet').first()
			if not wallet_obj:
				wallet_obj = WalletDetail.objects.create(user=request.user,type_of_coin='Wallet',total_coin=0)
			my_collention_coin_obj = WalletDetail.objects.filter(user=request.user,type_of_coin='My Collection').first()
			if not my_collention_coin_obj:
				my_collention_coin_obj = WalletDetail.objects.create(user=request.user,type_of_coin='My Collection',total_coin=0)
			wallet_detail = {
				"user_name":request.user.user_name,
				"id":request.user.id,
				"name":request.user.name,
				"image":request.user.image,
				"wallet_coin":wallet_obj.total_coin,
				"my_collention_coin":my_collention_coin_obj.total_coin if my_collention_coin_obj else 0
			}
			return Response({
				"status":True,
				"code":200,
				"data":wallet_detail,
				"message":"Your Wallet or My Collection Detail"
			},status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

def index(request):
    return render(request, 'chat/room.html')

class FetchAudioApi(APIView):
	permission_classes = (IsTokenValid,)
	def get(self,request):
		try:
			if not request.GET.get('page'):
				return Response({
					"status":False,
					"message":"Something Went Wrong!",
					"code":400,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			user_obj = MyUsers.objects.filter(email_address='admin@penutg.com').first()
			audio_obj = videoAudio.objects.filter(user=user_obj).all()
			limit = 50
			list2, page, paginator = paginatorData(audio_obj, limit,  request.GET.get('page'))
			serializers = AudioSerializers(list2, many=True)
			return Response({
				"status":True,
				"code":200,
				"data":serializers.data
			},status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

class ShareCoin(APIView):
	"""
		Sharing coin 
	"""
	permission_classes = (IsTokenValid,)
	def post(self,request):
		try:
			data = request.data
			receiver_obj = ""
			if 'user_id' not in data and 'user_name' not in data:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"User id or User name is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			elif 'user_id' in data and data['user_id'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"User id should not be empty."}
				},status=status.HTTP_400_BAD_REQUEST)
			elif 'user_name' in data and data['user_name'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"User name should not be empty."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'share_coin' not in data or data['share_coin'] == "":
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"share coin is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			if 'user_name' in data:
				receiver_obj = MyUsers.objects.filter(user_name=data['user_name']).first()
			else:
				receiver_obj = MyUsers.objects.filter(id=data['user_id']).first()
			wallet_obj = WalletDetail.objects.filter(user=request.user,type_of_coin="Wallet").first()
			if not wallet_obj:
				wallet_obj = WalletDetail.objects.create(user=request.user,type_of_coin="Wallet",total_coin=0)
			if wallet_obj.total_coin < data['share_coin']:
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"wallet_error","message":"You don't have enough coin to share.", "available_coin":wallet_obj.total_coin}
				},status=status.HTTP_400_BAD_REQUEST)
			else:
				receiver_wallet_obj = WalletDetail.objects.filter(user=receiver_obj,type_of_coin="My Collection").first()
				if not receiver_wallet_obj:
					receiver_wallet_obj = WalletDetail.objects.create(user=receiver_obj,type_of_coin="My Collection",total_coin=0)
				receiver_wallet_obj.total_coin = receiver_wallet_obj.total_coin+data['share_coin']
				receiver_wallet_obj.save()
				share_history_obj = CoinSharingHistory.objects.create(sender=request.user,receiver=receiver_obj,coin=data['share_coin'])
				wallet_obj.total_coin = wallet_obj.total_coin-data['share_coin']
				wallet_obj.save()
				my_collention_coin_obj = WalletDetail.objects.filter(user=request.user,type_of_coin="My Collection").first()
				wallet_detail = {
					"user_name":request.user.user_name,
					"id":request.user.id,
					"name":request.user.name,
					"image":request.user.image,
					"wallet_coin":wallet_obj.total_coin,
					"my_collention_coin":my_collention_coin_obj.total_coin if my_collention_coin_obj else 0
				}
				return Response({
					"message":"Coin has shared Successfully.",
					"data":wallet_detail,
					"code":200,
					"status":True
				},status=status.HTTP_200_OK) 
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		try:
			if not request.GET.get('page'):
				return Response({
					"message": "Something Went Wrong!",
					"code":400,
					"status":False,
					"error":{"type":"Validation","message":"Page is compulsory."}
				},status=status.HTTP_400_BAD_REQUEST)
			share_coin_history = CoinSharingHistory.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).all()
			limit = 30
			list2, page, paginator = paginatorData(share_coin_history, limit,  request.GET.get('page'))
			serializers = ShareHistorySerializers(list2,context={"user":request.user},many=True)
			return Response({
				"status":True,
				"code":200,
				"data":serializers.data,
				"message":"Your Wallet or My Collection Detail"
			},status.HTTP_200_OK)
		except Exception as e:
			return Response({
				"message": "Something Went Wrong!",
				"code":400,
				"status":False,
				"error":{"type":"Exception","message":e.__str__()}
			},status=status.HTTP_400_BAD_REQUEST)