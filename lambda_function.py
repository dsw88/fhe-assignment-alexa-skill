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
    """
    print(f"Log stream: {context.log_stream_name}\n"
          f"Log group: {context.log_group_name}\n"
          f"Request ID: {context.aws_request_id}\n"
          f"Mem limits(MB): {context.memory_limit_in_mb}\n"
          f"Event received: {event}")
    if "rotate" in event:
        rotate_all_assignments(event)
    if event['session']['application']['applicationId'] != app_id:
        raise Exception('Invalid app id')
    request_type = event['request']['type']
    if request_type == 'LaunchRequest' or request_type == 'IntentRequest' and event['request']['name'] == 'AssignmentsIntent':
        week = get_slot(event, 'week')
        if not week:
            week = 'this'
        return launch_request_handler(event, week)
    if request_type == 'LaunchRequest':
        if event['request']['name'] == 'AMAZON.HelpIntent':
            return help_intent_handler(event)
        if event['request']['name'] in ['AMAZON.CancelIntent', 'AMAZON.StopIntent']:
            return respond('Cancelling')
        if event['request']['name'] == 'SetupIntent':
            return setup_intent_handler(event)

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
    print("Rotated {} users' assignments".format(count))

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
    >>> get_slot({'request':{'type':'LaunchRequest'}}, 'zodiacsign')
    ''
    """
    if not 'intent' in request['request']:
        return ''
    if 'slots' in request['request']['intent']:
        if slot_name.lower() in [key.lower() for key in request['request']['intent']['slots']]:
            slots = {k.lower():v for k,v in request['request']['intent']['slots'].items()}
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
        return respond("You haven't setup your family members and assignments yet.  If you ready to do that now, just say, 'setup'.")
    try:
        assignments = get_assignments(week, userId)
        response = "The assignments {}: ".format(conjunction_junction(week, individual=False))
        for i, family_member in enumerate(assignments['family_members']):
            family_member = normalize_family_member(family_member)
            response += '{} {}, '.format(family_member, assignments['assignment'])
        return respond(response)
    except:
        print(traceback.format_exc())
        return respond("There was a problem retrieving the assignments.")

def help_intent_handler(request):
    return respond("Hi there! I can tell you and your family which family members have which assignments for family home evening each week. And, I'll automatically rotate those assignments each week so you don't have to do that. To start, just say, 'Alexa, open family home evening assignments.'")

def setup_intent_handler(request):
    family_member = get_slot(request, 'FamilyMember')
    assignment = get_slot(request, 'Assignment')

    item = get_assignments('this', get_user_id(request))
    if item:
        item['family_members'].append(family_member)
        item['assignments'].append(assignment)
    else:
        item = {'id': get_user_id(request), 'family_members': [family_member], 'assignments': [assignment]}
    table.put_item(Item=item)
    return respond(f"{family_member} added to {assignment}.")

def test(verbose=False):
    import doctest
    return doctest.testmod(verbose=verbose)[0]

if __name__ == "__main__":
    fire.Fire()
