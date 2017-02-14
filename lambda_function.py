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

# Lambda function
def lambda_handler(request_obj, context=None):
    if request_obj == 'rotate':
        rotate_assignments(request)
    else:
        metadata = {}
        # use the metadata in a handler method like so `return alexa.respond('Hello there {}!'.format(request.metadata['user_name']))`
        return alexa.route_request(request_obj, metadata) 

# ASK functions
@alexa.default
def default_handler(request):
    return launch_request_handler(request)

@alexa.request("LaunchRequest")
def launch_request_handler(request):
    if not is_setup():
        request.session['previous_message'] = "Since you haven't set up your assignments or family members yet, we'll do that now."
        return setup_intent_handler(request)
    return assignments_intent_handler(request)

@alexa.intent('SetupIntent')
def setup_intent_handler(request):
    message = ""
    if 'previous_message' in request.session:
        message = request.session['previous_message'] + message
    return alexa.respond(message)

@alexa.intent('AssignmentsIntent')
def assignments_intent_handler(request):
    try:
        assignments = get_assignments(request.slots["week"])
        response = ""
        for assignment in assignments:
            # TODO format dictionary to spoken string
        return alexa.respond(response, end_session=True)
    except:
        print(traceback.format_exc())
        return alexa.respond("There was a problem retrieving the assignments.", end_session=True)

@alexa.intent('FamilyMemberAssignmentIntent')
def family_member_assignment_intent_handler(request):
    family_member = request.slots['family_member']
    try:
        assignments = get_assignments(request.slots["week"])
        if family_member in assignments.keys():
            return alexa.respond("{}'s assignment is {}".format(family_member, assignment[family_member.lower()], end_session=True)
        else:
            request.session['next_intent'] = 'SetupIntent'
            return alexa.return("{} isn't one of the family members defined. Would you like to run setup again?")
    except:
        print(traceback.format_exc())
        return alexa.respond("There was a problem retrieving {}'s assignments.".format(family_member), end_session=True)

@alexa.intent('YesIntent')
def yes_intent_handler(request):
    if 'next_intent' in request.session:
        return globals()[request.session['next_intent']](request)
    return alexa.respond("", end_session=True)
    
@alexa.intent('NoIntent')
def no_intent_handler(request):
    return alexa.respond("", end_session=True)

# Helper functions
def get_assignments(week):
    """
    Returns the assignments in {'person': 'assignment', 'person2': 'assignment2'} format
    """
    # TODO implement dynamo query

def is_setup():
    """
    Returns a boolean indicating if the setup has been done.
    """
    # TODO implement is_setup() with Dynamo

if __name__ == "__main__":    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve','-s', action='store_true', default=False)
    args = parser.parse_args()
    
    if args.serve:        
        print('Serving ASK functionality locally.')
        import flask
        server = flask.Flask(__name__)
        @server.route('/')
        def alexa_skills_kit_requests():
            request_obj = flask.request.get_json()
            return lambda_handler(request_obj)
        server.run()
