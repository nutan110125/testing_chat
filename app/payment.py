import razorpay
from .utils import *
from .models import *
import hmac
import hashlib
import sys
client = razorpay.Client(auth=(Rozors_key_id, Rozors_secret_key))

def create_order(data):
	try:
		order_detail = client.order.create(dict(amount=int(data['amount']), currency=data['order_currency'], payment_capture=0))
		if order_detail:
			order_obj = PaymentDetail.objects.create(
				sender=data['sender'], receiver=data['receiver'], order_id=order_detail['id'],order_currency=order_detail['currency'],
				order_status=order_detail['status'],payment_attempts=order_detail['attempts'],amount=order_detail['amount']
			)
			return {"razorpay_response":order_detail,"api_Response":order_obj,"status":True}
	except Exception as e:
		return {"status":False,"message":e.__str__()}

def get_order_detail(data):
	try:
		order_detail = resp = client.order.fetch(data)
		return {"razorpay_response":order_detail,"status":True}
	except Exception as e:
		return {"status":False,"message":e.__str__()}

def verify_signature(body, signature, key):
	if sys.version_info[0] == 3:  # pragma: no cover
	    key = bytes(key, 'utf-8')
	    body = bytes(body, 'utf-8')

	dig = hmac.new(key=key,
	               msg=body,
	               digestmod=hashlib.sha256)

	generated_signature = dig.hexdigest()

	if sys.version_info[0:3] < (2, 7, 7):
	    result = compare_string(generated_signature, signature)
	else:
	    result = hmac.compare_digest(generated_signature, signature)

	if not result:
	    raise SignatureVerificationError(
	        'Razorpay Signature Verification Failed')
	return result


def verify_payment(data):
	try:
		order_id = str(data['razorpay_order_id'])
		payment_id = str(data['razorpay_payment_id'])
		razorpay_signature = str(data['razorpay_signature'])
		msg = "{}|{}".format(order_id, payment_id)
		secret = Rozors_secret_key
		verify_obj = verify_signature(msg, razorpay_signature, secret)
		if verify_obj:
			payment_obj = PaymentDetail.objects.filter(order_id=data['razorpay_order_id']).first()
			if payment_obj:
				payment_obj.payment_signature = data['razorpay_signature']
				payment_obj.payment_verify = True
				payment_obj.save()
			return {"status":True,"razorpay_response":verify_obj}
		return {"status":False,"message":"No Response from Razorpay."}
	except razorpay.errors.SignatureVerificationError:
		return {"status":False,"message":" Razorpay Signature Verification Failed."}
	except Exception as e:
		return {"status":False,"message":e.__str__()}

def capture_payment(data):
	try:
		resp = client.payment.capture(data['payment_id'], data['payment_amount'], {"currency":data['payment_currency']})
		if 'error' in resp:
			return {"status":False,"message":resp['error']['description']}
		else:
			return {"status":True,"razorpay_response":resp}
	except Exception as e:
		return {"status":False,"message":e.__str__()}

def get_payment_detail(payment_id):
	try:
		resp = client.payment.fetch(payment_id)
		if 'error' in resp:
			return {"status":False,"message":resp['error']['description']}
		else:
			return {"status":True,"razorpay_response":resp}
	except Exception as e:
		return {"status":False,"message":e.__str__()}

