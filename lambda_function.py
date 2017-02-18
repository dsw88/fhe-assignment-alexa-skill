# Copyright 2017 Brigham Young University
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function
from ask import alexa
import boto3
import traceback
import os
import copy

# Initialization
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

# Lambda function
def lambda_handler(request_obj, context=None):
    if 'rotate' in request_obj:
        rotate_all_assignments(request_obj)
    else:
        metadata = {}
        print(request_obj)
        # use the metadata in a handler method like so `return alexa.create_response('Hello there {}!'.format(request.metadata['user_name']))`
        return alexa.route_request(request_obj, metadata) 

# ASK functions
@alexa.default_handler()
def default_handler(request):
    return launch_request_handler(request)

# TODO implement voice setup
# TODO update the documentation 
# TODO disable any client except Alexa
# TODO add a catch all intent with only one custom slot that has very generic sample utterances and send slot value to SNS topic
# TODO submit for certification

@alexa.request_handler("LaunchRequest")
def launch_request_handler(request):
    if not is_setup(request.user_id()):
        request.session['previous_message'] = "Since you haven't set up your assignments or family members yet, we'll do that now."
        return setup_intent_handler(request)
    return assignments_intent_handler(request)

@alexa.intent_handler('SetupIntent')
def setup_intent_handler(request):
    message = " "
    if 'previous_message' in request.session:
        message = request.session['previous_message'] + message
    return alexa.create_response(message)

@alexa.intent_handler('AssignmentsIntent')
def assignments_intent_handler(request):
    try:
        assignments = get_assignments(request.slots["AWeek"], request.user_id())
        response = "The assignments {} as follows: ".format(conjunction_junction(request.slots['AWeek'], individual=False))
        for i, family_member in enumerate(assignments['family_members']):
            family_member = normalize_family_member(family_member)
            response += "{} {}, ".format(family_member, assignments['assignments'][i])
        return alexa.create_response(response, end_session=True)
    except:
        print(traceback.format_exc())
        return alexa.create_response("There was a problem retrieving the assignments.", end_session=True)

@alexa.intent_handler('FamilyMemberAssignmentIntent')
def family_member_assignment_intent_handler(request):
    family_member = normalize_family_member(request.slots['FamilyMember'])
    try:
        wa = get_assignments(request.slots["FMAWeek"], request.user_id())
        family_members = lower_list(wa['family_members'])
        assignments = lower_list(wa['assignments'])
        if family_member in family_members:
            return alexa.create_response("{}'s assignment {} {}".format(family_member, 
                conjunction_junction(request.slots['FMAWeek']), 
                assignments[family_members.index(family_member)]), end_session=True)
        else:
            request.session['next_intent'] = 'SetupIntent'
            return alexa.create_response("{} isn't one of the family members defined. Would you like to run setup again?".format(family_member))
    except:
        print(traceback.format_exc())
        return alexa.create_response("There was a problem retrieving {}'s assignments.".format(family_member), end_session=True)

@alexa.intent_handler('AssignmentFamilyMemberIntent')
def assignment_family_member_intent_handler(request):
    assignment_to_find = request.slots['Assignment'].lower()
    week = request.slots['Week']
    try:
        wa = get_assignments(week, request.user_id())
        family_members = lower_list(wa['family_members'])
        assignments = lower_list(wa['assignments'])
        if assignment_to_find in assignments:
            return alexa.create_response("{}'s assignment {} {}".format(family_members[assignments.index(assignment_to_find)],
                conjunction_junction(week), assignment_to_find), end_session=True)
        else:
            request.session['next_intent'] = 'SetupIntent'
            return alexa.create_response("{} isn't one of the assignments defined. Would you like to run setup again?".format(assignment_to_find))
    except:
        print(traceback.format_exc())
        return alexa.create_response("There was a problem retrieving who is assigned to {}.".format(assignment_to_find), end_session=True)

@alexa.intent_handler('YesIntent')
def yes_intent_handler(request):
    if 'next_intent' in request.session:
        return globals()[request.session['next_intent']](request)
    return alexa.create_response(" ", end_session=True)
    
@alexa.intent_handler('NoIntent')
def no_intent_handler(request):
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
    Returns the assignments in {'id': aaaaaaaa, 'family_members': ['person': 'person2'], 'assignments': ['assignment1', 'assignment2']} format
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
    return fm.replace("'s", "").lower()

def lower_list(l):
    return [item.lower() for item in l]

if __name__ == "__main__":    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve','-s', action='store_true', default=False)
    args = parser.parse_args()
    
    if args.serve:        
        print('Serving ASK functionality locally.')
        import flask
        server = flask.Flask(__name__)
        @server.route('/', methods=['POST'])
        def alexa_skills_kit_requests():
            request_obj = flask.request.get_json()
            return lambda_handler(request_obj)
        server.run()
