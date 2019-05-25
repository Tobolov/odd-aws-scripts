import boto3
import argparse
import time
import re

# Sender ID only works if available in your region.
# https://docs.aws.amazon.com/sns/latest/dg/sms_supported-countries.html

# parse arguments
parser = argparse.ArgumentParser(
    description='Send a single message via multiple SMS messages.')
parser.add_argument('--mobile', action="store", dest="mobile",
                    help='Mobile number to send SMS to. Must be in E.164 format.')
parser.add_argument('--message', action="store",
                    dest="message", help='Message to send.')
parser.add_argument('--dry', action="store_true", default=False,
                    dest="dry", help='Dry run. Don\'t send message to mobile.')
args = parser.parse_args()

# get boto3 sns session
sns_client = boto3.client('sns')

# print status
if args.dry:
    print('Dry run of sending message "%s" to "%s"' % (args.message, args.mobile))
else:
    print('Sending message "%s" to "%s"' % (args.message, args.mobile))

# deconstuct message and validate
split_message = args.message.split(' ')
deconstructed_message = [split_message[i:i+2] for i in range(0, len(split_message), 2)]
for message_component in deconstructed_message:
    # validate sender id length
    if len(message_component[0]) > 11:
        print("Can't send message as %s is longer than 11 characters" % message_component[0])
        exit(1)
    # validate sender id is only alphanumeric
    if not message_component[0].isalnum():
        print("Can't send message as \"%s\" is not alphanumeric" % message_component[0])
        exit(1)


# check if total sms count exceeds 22
if len(deconstructed_message) > 22:
    print("Warning, message will not be able to be sent if service limit has not been increased. \n"
        + "Are you sure you would like to send the message?")
    while True:
        response = input("[yes/no]: ").lower()
        if response == 'yes':
            break
        if response == 'no':
            exit(0)

# check if mobile number is not e.164
if not re.match(r"^\+?[1-9]\d{1,14}$", args.mobile):
    print('Mobile number "%s" is not in e.164 format' % args.mobile)
    exit(1)

# send the message
for message_component in deconstructed_message[::-1]:
    sms_sender = message_component[0]
    sms_content = message_component[1] if len(message_component) == 2 else "-"

    print("Subject: %s" % sms_sender)
    print("Message: %s" % sms_content)

    if (not args.dry):
        response = sns_client.publish(
            PhoneNumber=args.mobile,
            Message=sms_content,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': sms_sender
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                } 
            }
        )
        print("Response: %s\n" % response['MessageId'])
        time.sleep(5)


