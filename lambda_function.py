#!/usr/bin/env python
import os
import copy
import fire
import boto3
import traceback

# Initialization
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table(os.environ['DYNAMODB_FHE_ALEXA_PRD_DB_TABLE_NAME'])

app_id = 'amzn1.ask.skill.31864ddd-cc63-4274-bd5c-8f851cca8fc1'
testing=False

def log(text):
    if not testing:
        print(text)

def respond(responseText, shouldEndSession=True, sessionAttributes={}, cardTitle="", cardContent="", repromptText=""):
    response = {
      "version": "1.0",
      "sessionAttributes": sessionAttributes,
      "response": {
        "outputSpeech": {
          "type": "PlainText",
          "text": responseText
        },
        "shouldEndSession": shouldEndSession
      }
    }
    if cardContent:
        response['response']['card'] = {
          "type": "Simple",
          "title": cardTitle,
          "content": cardContent
        }
    if repromptText:
        response['response']['reprompt'] = {
          "outputSpeech": {
            "type": "PlainText",
            "text": repromptText
          }
        }
    log(f"returning response: {response}")
    return response

def handler(event, context):
    """
    event = {
    'session':{
      'new':True,
      'sessionId':'SessionId.asdfasdfasdfasdfasdf',
      'application':{
         'applicationId':'asdfasdfasdfasdfasdfasdfasdf'
      },
      'attributes':{

      },
      'user':{
         'userId':'amzn1.ask.account.asdfasdfasdfasdfasdf'
      }
   },
   'request':{
      'type':'LaunchRequest',
      'requestId':'EdwRequestId.asdfasdfasdfasdfasdf',
      'locale':'en-US',
      'timestamp':'2017-09-05T02:38:33Z'
   },
   OR
   "request": {
    "type": "IntentRequest",
    "requestId": "EdwRequestId.asdfasdfasdfasdfasdf",
    "intent": {
      "name": "AssignmentsIntent",
      "slots": {
        "Week": {
          "name": "Week"
        }
      }
    },
    "locale": "en-US",
    "timestamp": "2017-09-05T02:58:05Z"
   },
   'context':{
      'AudioPlayer':{
         'playerActivity':'IDLE'
      },
      'System':{
         'application':{
            'applicationId':'amzn1.ask.skill.asdfasdfasdfasdf'
         },
         'user':{
            'userId':'amzn1.ask.account.asdfasdfasdfasdf'
         },
         'device':{
            'supportedInterfaces':{

            }
         }
      }
   },
   'version':'1.0'
    }

    >>> handler({'session': {'application': {'applicationId': '1223'}}}, {})
    Traceback (most recent call last):
    ...
    Exception: Invalid app id
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'LaunchRequest'}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': "You haven't setup your family members and assignments yet.  If you ready to do that now, just say, 'setup'."}, 'shouldEndSession': False}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'AssignmentsIntent'}}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': "You haven't setup your family members and assignments yet.  If you ready to do that now, just say, 'setup'."}, 'shouldEndSession': False}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'AMAZON.HelpIntent'}}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': "Hi there! I can tell you and your family which family members have which assignments for family home evening each week. And, I'll automatically rotate those assignments each week so you don't have to do that. To start, just say, 'Alexa, open family home evening assignments.'"}, 'shouldEndSession': True}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'AMAZON.CancelIntent'}}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': 'Cancelling'}, 'shouldEndSession': True}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'AMAZON.StopIntent'}}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': 'Cancelling'}, 'shouldEndSession': True}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'SetupIntent', 'confirmationStatus': 'NONE'}, 'dialogState': 'STARTED'}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'shouldEndSession': False, 'directives': [{'type': 'Dialog.Delegate'}]}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'SetupIntent', 'confirmationStatus': 'DENIED'}, 'dialogState': 'COMPLETED'}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': 'OK, not proceeding.'}, 'shouldEndSession': True}}
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'SetupIntent', 'confirmationStatus': 'CONFIRMED'}, 'dialogState': 'COMPLETED'}}, {})
    Traceback (most recent call last):
    ...
    botocore.exceptions.ClientError: An error occurred (ValidationException) when calling the PutItem operation: One or more parameter values were invalid: An AttributeValue may not contain an empty string
    >>> handler({'session': {'user': {'userId': 'user123'}, 'application': {'applicationId': app_id}}, 'request': {'type': 'IntentRequest', 'intent': {'name': 'ClearIntent'}}}, {})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'outputSpeech': {'type': 'PlainText', 'text': 'The assignments and family members are now empty.  To add new ones just run setup again.'}, 'shouldEndSession': True}}
    """
    log(f"Incoming request: {event}")
    if "rotate" in event:
        rotate_all_assignments(event)
    if event['session']['application']['applicationId'] != app_id:
        raise Exception('Invalid app id')
    request_type = event['request']['type']
    if request_type == 'LaunchRequest' or request_type == 'IntentRequest' and event['request']['intent']['name'] == 'AssignmentsIntent':
        week = get_slot(event, 'week')
        if not week:
            week = 'this'
        return launch_request_handler(event, week)
    if request_type == 'IntentRequest':
        if event['request']['intent']['name'] == 'AMAZON.HelpIntent':
            return help_intent_handler(event)
        if event['request']['intent']['name'] in ['AMAZON.CancelIntent', 'AMAZON.StopIntent']:
            return respond('Cancelling')
        if event['request']['intent']['name'] == 'SetupIntent':
            return setup_intent_handler(event)
        if event['request']['intent']['name'] == 'ClearIntent':
            return clear_intent_handler(event)

def dialog(dialogType, promptText="", updatedIntent={}):
    """
    >>> dialog('Delegate')
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'shouldEndSession': False, 'directives': [{'type': 'Dialog.Delegate'}]}}
    >>> dialog('delegate')
    Traceback (most recent call last):
    ...
    AssertionError
    >>> dialog('ConfirmSlot', 'testing', {'hi': 'there'})
    {'version': '1.0', 'sessionAttributes': {}, 'response': {'shouldEndSession': False, 'directives': [{'type': 'Dialog.ConfirmSlot', 'updatedIntent': {'hi': 'there'}}]}, 'outputSpeech': {'type': 'PlainText', 'text': 'testing'}}
    """
    assert dialogType in ['Delegate', 'ElicitSlot', 'ConfirmSlot', 'ConfirmIntent']
    dialogResponse = {
      "version": "1.0",
      "sessionAttributes": {},
      "response": {
        "shouldEndSession": False,
        "directives": [
          {
            "type": f"Dialog.{dialogType}"
          }
        ]
      }
    }
    if promptText:
        dialogResponse['outputSpeech'] = {
          "type": "PlainText",
          "text": promptText
        }
    if updatedIntent:
        dialogResponse['response']['directives'][0]['updatedIntent'] = updatedIntent
    log(f"returning dialog: {dialogResponse}")
    return dialogResponse

# Helper functions
def conjunction_junction(week, individual=True):
    """
    >>> conjunction_junction('this')
    'this week is'
    >>> conjunction_junction('next')
    'next week will be'
    >>> conjunction_junction('last')
    'last week was'
    >>> conjunction_junction('this', False)
    'this week are'
    >>> conjunction_junction('next', False)
    'next week will be'
    >>> conjunction_junction('last', False)
    'last week were'
    """
    if individual:
        if week == 'next':
            return 'next week will be'
        elif week == 'last':
            return 'last week was'
        else:
            return 'this week is'
    else:
        if week == 'next':
            return 'next week will be'
        elif week == 'last':
            return 'last week were'
        else:
            return 'this week are'

def get_assignments(week, user_id):
    """
    >>> get_assignments({'id': 'testing', 'family_members': ['person', 'person2'], 'assignments': ['assignment1', 'assignment2']}, 'testing')
    """
    this_week_assignments = get_this_week_assignments(user_id)
    if week == 'last':
        return last_week_assignments(this_week_assignments)
    elif week == 'next':
        return next_week_assignments(this_week_assignments)
    else:
        return this_week_assignments

def rotate_all_assignments(request):
    """
    Rotate all the assignments for each setup entry (TODO rethink design to be more scalable if needed)
    """
    response = table.scan(ConsistentRead=True)
    count = 0
    for household_assignments in response['Items']:
        nwa = next_week_assignments(household_assignments)
        table.put_item(Item=nwa)
        count += 1
    log("Rotated {} users' assignments".format(count))

def shift(num_to_shift, array):
    """
    >>> shift(1, ['one', 'two'])
    ['two', 'one']
    >>> shift(-2, ['one', 'two', 'three'])
    ['three', 'one', 'two']
    """
    return array[-num_to_shift:]+array[:-num_to_shift]

def next_week_assignments(this_week_assignments):
    return shift_assignments(this_week_assignments, 1)

def last_week_assignments(this_week_assignments):
    return shift_assignments(this_week_assignments, -1)

def shift_assignments(this_week_assignments, num_to_shift):
    """
    >>> shift_assignments({'family_members': ['dad', 'mom'], 'assignments': ['lesson', 'treat']}, 1)
    {'family_members': ['dad', 'mom'], 'assignments': ['treat', 'lesson']}
    >>> shift_assignments({'family_members': ['dad', 'mom'], 'assignments': ['lesson', 'treat']}, -2)
    {'family_members': ['dad', 'mom'], 'assignments': ['lesson', 'treat']}
    """
    na = copy.deepcopy(this_week_assignments)
    na['assignments'] = shift(num_to_shift, this_week_assignments['assignments'])
    return na

def is_setup(user_id):
    """
    Returns a boolean indicating if the setup has been done.
    >>> is_setup('testing')
    False
    >>> is_setup('fake id')
    False
    """
    response = table.get_item(Key={'id': user_id})
    return 'Item' in response

def get_this_week_assignments(user_id):
    """
    >>> get_this_week_assignments('testing')
    """
    response = table.get_item(Key={'id': user_id})
    if 'Item' in response:
        return response['Item']
    return None

def normalize_family_member(fm):
    """
    >>> normalize_family_member("Dad's")
    'dad'
    """
    if fm:
        return fm.replace("'s", "").lower()
    return fm

def lower_list(l):
    """
    >>> lower_list(['One', 'TWO', 'ThRee'])
    ['one', 'two', 'three']
    """
    return [item.lower() for item in l]

def get_slot(request, slot_name):
    """
    >>> get_slot({'request': {'type': 'IntentRequest', 'dialogState': 'COMPLETED', 'intent': {'name': 'AIntent', 'confirmationStatus': 'NONE', 'slots': {'ZodiacSign': {'name': 'ZodiacSign', 'value': 'virgo', 'confirmationStatus': 'NONE'}}}}}, 'testing')
    ''
    >>> get_slot({'request': {'type': 'IntentRequest', 'dialogState': 'COMPLETED', 'intent': {'name': 'AIntent', 'confirmationStatus': 'NONE', 'slots': {'ZodiacSign': {'name': 'ZodiacSign', 'value': 'virgo', 'confirmationStatus': 'NONE'}}}}}, 'zodiacsign')
    'virgo'
    >>> get_slot({'request': {'type': 'IntentRequest', 'dialogState': 'COMPLETED', 'intent': {'name': 'AIntent', 'confirmationStatus': 'NONE', 'slots': {'ZodiacSign': {'name': 'ZodiacSign', 'value': 'virgo', 'confirmationStatus': 'NONE'}}}}}, 'ZodiacSign')
    'virgo'
    >>> get_slot({'request': {'type': 'IntentRequest', 'dialogState': 'COMPLETED', 'intent': {'name': 'AIntent', 'confirmationStatus': 'NONE', 'slots': {'ZodiacSign': {'name': 'ZodiacSign', 'confirmationStatus': 'NONE'}}}}}, 'zodiacsign')
    ''
    >>> get_slot({'request':{'type':'LaunchRequest'}}, 'zodiacsign')
    ''
    """
    if not 'intent' in request['request']:
        return ''
    if 'slots' in request['request']['intent']:
        slot_name = slot_name.lower()
        if slot_name in [key.lower() for key in request['request']['intent']['slots']]:
            slots = {k.lower():v for k,v in request['request']['intent']['slots'].items()}
            if 'value' in slots[slot_name]:
                return slots[slot_name]['value']
    return ''

def get_user_id(request):
    """
    >>> get_user_id({'session':{'user':{'userId':'buggabugga'}}})
    'buggabugga'
    """
    return request['session']['user']['userId']


# ASK functions

def launch_request_handler(request, week='this'):
    userId = get_user_id(request)
    if not is_setup(userId):
        return respond("You haven't setup your family members and assignments yet.  If you're ready to do that now, just say, 'setup' or say stop to finish.", shouldEndSession=False)
    try:
        assignments = get_assignments(week, userId)
        response = "The assignments {}: ".format(conjunction_junction(week, individual=False))
        for i, family_member in enumerate(assignments['family_members']):
            family_member = normalize_family_member(family_member)
            response += '{} {}, '.format(family_member, assignments['assignments'][i])
        return respond(response)
    except:
        print(f"these are the assignments from the db: {assignments}")
        print(traceback.format_exc())
        return respond("There was a problem retrieving the assignments.")

def help_intent_handler(request):
    return respond("Hi there! I can tell you and your family which family members have which assignments for family home evening each week. And, I'll automatically rotate those assignments each week so you don't have to do that. To start, just say, 'Alexa, open family home evening assignments.'")

def setup_intent_handler(request):
    if not 'dialogState' in request['request'] or request['request']['dialogState'] != 'COMPLETED':
            return dialog('Delegate')

    family_member = get_slot(request, 'FamilyMember')
    assignment = get_slot(request, 'Assignment')

    item = get_assignments('this', get_user_id(request))
    if item:
        item['family_members'].append(family_member)
        item['assignments'].append(assignment)
    else:
        item = {'id': get_user_id(request), 'family_members': [family_member], 'assignments': [assignment]}
    table.put_item(Item=item)
    return respond(f"{family_member} added to {assignment}. To add another family member or assignment just run setup again. To clear the assignments just say clear. And to finish say all done.", shouldEndSession=False)

def clear_intent_handler(request):
    table.delete_item(Key={'id': get_user_id(request)})
    return respond("The assignments and family members are now empty.  To add new ones just run setup again.")

def test(verbose=False):
    import doctest
    global testing
    testing=True
    return doctest.testmod(verbose=verbose)[0]

if __name__ == "__main__":
    fire.Fire()
