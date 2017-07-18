#!/usr/bin/env python
import os
import copy
import fire
import boto3
import echokit
import traceback

# Initialization
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table(os.environ['DYNAMODB_FHE_ALEXA_PRD_DB_TABLE_NAME'])

echokit.application_id = 'amzn1.ask.skill.31864ddd-cc63-4274-bd5c-8f851cca8fc1'

lambda_handler = echokit.handler

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
    {'id': 'testing', 'family_members': ['mom', 'dad'], 'assignments': ['treat', 'lesson']}
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
    True
    >>> is_setup('fake id')
    False
    """
    response = table.get_item(Key={'id': user_id})
    return 'Item' in response

def get_this_week_assignments(user_id):
    """
    >>> get_this_week_assignments('testing')
    {'id': 'testing', 'family_members': ['mom', 'dad'], 'assignments': ['treat', 'lesson']}
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

# ASK functions

# TODO submit a pull request to the ask library saying we are using the library

@echokit.on_session_launch
@echokit.on_intent('AssignmentsIntent')
@echokit.slot('Week', dest='week')
def launch_request_handler(request, week='this'):
    if not is_setup(request.user_id()):
        return echokit.ask("You haven't setup your family members and assignments yet.  If you ready to do that now, just say setup.")
    try:
        assignments = get_assignments(week, request.user_id())
        response = "The assignments {}: ".format(conjunction_junction(week, individual=False))
        for i, family_member in enumerate(assignments['family_members']):
            family_member = normalize_family_member(family_member)
            response += '{} {}, '.format(family_member, assignments['assignment'])
        return echokit.tell(response)
    except:
        print(traceback.format_exc())
        return echokit.tell("There was a problem retrieving the assignments.")

@echokit.on_intent('AMAZON.HelpIntent')
def help_intent_handler(request):
    return echokit.tell("Hi there! I can tell you and your family which family members have which assignments for family home evening each week. And, I'll automatically rotate those assignments each week so you don't have to do that. To start, just say, 'Alexa, open family home evening assignments.'")

def test(verbose=False):
    import doctest
    return doctest.testmod(verbose=verbose)[0]

if __name__ == "__main__":
    fire.Fire()
