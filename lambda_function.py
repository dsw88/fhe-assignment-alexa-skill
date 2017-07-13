#!/usr/bin/env python
import os
import copy
import fire
import boto3
import traceback
from ask import alexa

# Initialization
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table(os.environ['DYNAMODB_FHE_ALEXA_PRD_DB_TABLE_NAME'])

# Lambda function
def lambda_handler(request_obj, context=None):
    try:
        print(request_obj)
        if 'rotate' in request_obj:
            rotate_all_assignments(request_obj)
        else:
            if request_obj['session']['application']['applicationId'] != 'amzn1.ask.skill.31864ddd-cc63-4274-bd5c-8f851cca8fc1':
                raise Exception('Invalid application id')
            metadata = {}
            # use the metadata in a handler method like so `return alexa.create_response('Hello there {}!'.format(request.metadata['user_name']))`
            return alexa.route_request(request_obj, metadata)
    except:
        message = traceback.format_exc()
        print(message)
        sns.publish(Message=message, Subject="Error on FHE Alexa Skill", TopicArn=os.environ["SNS_FHE_ALEXA_PRD_DB_TOPIC_ARN"])
        return alexa.create_response("There was a problem. Please try again.", end_session=True)

# ASK functions

# TODO submit a pull request to the ask library saying we are using the library

@alexa.default_handler()
@alexa.request_handler('LaunchRequest')
@alexa.intent_handler('AssignmentsIntent')
def launch_request_handler(request):
    if not is_setup(request.user_id()):
        return alexa.create_response("You haven't setup your family members and assignments yet.  If you ready to do that now say setup.", end_session=False)
    try:
        week = 'this'
        if hasattr(request, 'slots'):
            week = request.slots['Week']
        assignments = get_assignments(week, request.user_id())
        response = "The assignments {}: ".format(conjunction_junction(week, individual=False))
        for i, family_member in enumerate(assignments['family_members']):
            family_member = normalize_family_member(family_member)
            response += "{} {}, ".format(family_member, assignments['assignments'][i])
        return alexa.create_response(response, end_session=True)
    except:
        print(traceback.format_exc())
        return alexa.create_response("There was a problem retrieving the assignments.", end_session=True)

@alexa.intent_handler('AMAZON.HelpIntent')
def help_intent_handler(request):
    return alexa.create_response("Hi there! I can tell you and your family which family members have which assignments for family home evening each week. And, I'll automatically rotate those assignments each week so you don't have to do that. To start, just say, 'Alexa, open family home evening assignments.'", end_session=True)

@alexa.intent_handler('AMAZON.CancelIntent')
@alexa.intent_handler('AMAZON.StopIntent')
def stop_cancel_intent_handler(request):
    return alexa.create_response(" ", end_session=True)

# Helper functions
def conjunction_junction(week, individual=True):
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
    Returns the assignments in {'id': aaaaaaaa, 'family_members': ['person', 'person2'], 'assignments': ['assignment1', 'assignment2']} format
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
    return array[-num_to_shift:]+array[:-num_to_shift]

def next_week_assignments(this_week_assignments):
    return shift_assignments(this_week_assignments, 1)

def last_week_assignments(this_week_assignments):
    return shift_assignments(this_week_assignments, -1)

def shift_assignments(this_week_assignments, num_to_shift):
    na = copy.deepcopy(this_week_assignments)
    na['assignments'] = shift(num_to_shift, this_week_assignments['assignments'])
    return na

def is_setup(user_id):
    """
    Returns a boolean indicating if the setup has been done.
    """
    response = table.get_item(Key={'id': user_id})
    return 'Item' in response

def get_this_week_assignments(user_id):
    response = table.get_item(Key={'id': user_id})
    if 'Item' in response:
        return response['Item']
    return None

def normalize_family_member(fm):
    if fm:
        return fm.replace("'s", "").lower()
    return fm

def lower_list(l):
    return [item.lower() for item in l]

def test(verbose=False):
    import doctest
    doctest.testmod(verbose=verbose)

def serve():
    print('Serving ASK functionality locally.')
    import flask
    server = flask.Flask(__name__)
    @server.route('/', methods=['POST'])
    def alexa_skills_kit_requests():
        request_obj = flask.request.get_json()
        return lambda_handler(request_obj)
    server.run()

if __name__ == "__main__":
    fire.Fire()
