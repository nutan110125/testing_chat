from django.core.validators import RegexValidator

EMAILREGEX = RegexValidator(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$','Email must contain at least one @ and .')
MOBILEREGEX = RegexValidator(r'^\+?1?\d{9,15}$', 'Mobile number must be integer')
NAMEREGEX = RegexValidator(r'^[a-zA-Z-]+$', 'Only character is allowed')
YEARREGEX = RegexValidator(r'^\+?1?\d{4,5}$', 'Year must be integer')
COUNTRYCODEREGEX=RegexValidator(r'^(\+?\d{1,3}|\d{1,4})$',"Country Code Start with + and follow only integer")


#s3 bucket information
S3_bucket_username = "pythonDeveloper "
S3_bucket_name = "penut.bucket"
video_s3_bucket_name="vod-watchfolder-ag"
S3_bucket_access_token = "AKIAWS6ELJ3G3DKPGFU2"
S3_bucket_secret_access_token = "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"
S3_bucket_image_url = "https://s3.ap-south-1.amazonaws.com/penut.bucket/"
S3_bucket_video_url = "https://vod-watchfolder-ag.s3.amazonaws.com/"
s3_get_video_url = "https://vod-mediabucket-ag.s3.ap-south-1.amazonaws.com/"


Rozors_key_id = "rzp_test_Xm44XvhPbb8xpe"
Rozors_secret_key = "eHbrKI8bneoe76Cvt329cj5S"