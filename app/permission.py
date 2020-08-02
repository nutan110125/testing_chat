from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated
from .models import *

class IsTokenValid(BasePermission):
	message = {
		"status":False,
		"message":"You do not have permission for this action.",
		"error":{
			"type":"PermissionDenied",
			"message":"Please login Again because you do not have permission for this action."
		}
	}
	def has_permission(self, request, view):
		user_id = request.user.id            
		is_allowed_user = True
		try:
			if request.user.is_authenticated:
				token = request.auth.decode("utf-8")
				is_valid_token = UserNewToken.objects.get(user=request.user, token=token)
				if is_valid_token:
					is_allowed_user = True
					return is_allowed_user
			else:
				is_allowed_user = False
				message = {
					"status":False,
					"message":"Something Went Wrong!",
					"error":{
						"type":"Exception",
						"message":"Please login Again because Un-Authorizer user is not allowed for this Action."
					}
				}
				raise NotAuthenticated(message)
		except UserNewToken.DoesNotExist:
			is_allowed_user = False
			return is_allowed_user


class UserViewsPermission(BasePermission):
	message = {
		"status":False,
		"message":"You do not have permission for this action.",
		"error":{
			"type":"PermissionDenied",
			"message":"Please login Again because you do not have permission for this action."
		}
	}
	def has_permission(self, request, view):
		user_id = request.user.id            
		is_allowed_user = True
		try:
			if request.user.is_authenticated:
				token = request.auth.decode("utf-8")
				is_valid_token = UserNewToken.objects.get(user=request.user, token=token)
				if is_valid_token:
					is_allowed_user = True
					return is_allowed_user
			else:
				return "User does not login."
		except UserNewToken.DoesNotExist:
			is_allowed_user = False
			return is_allowed_user

