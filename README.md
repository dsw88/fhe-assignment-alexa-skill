# FHE Assignments Alexa Skill
An Alexa skill to record which family members have what assignments each week for Family Home Evening and rotate them automatically each week.

Members of the [Church of Jesus Christ of Latter-day Saints](https://www.mormon.org/) spend an evening together with their families once a week to strengthen family ties. We abbreviate it FHE. See more about Family Home Evening [here](https://www.lds.org/topics/family-home-evening/purpose?lang=eng&old=true).

This project is a Crazy Friday project of the Office of IT (OIT) at Brigham Young University. Crazy Friday is OIT's R&D time on Friday's each week. I wanted an easier way to track our family's FHE assignments and also wanted to try out DynamoDB. And after having tried DynamoDB, I have to say I like it.

My family kept our assignment schedule previously in a Google Spreadsheet but even that felt cumbersome compared to the amazing ease of use and almost fritionless voice interface experience of the Amazon Echo devices. 

# One-time Setup
Say, "Alexa, enable FHE Assignments".

Then say, "Alexa, open FHE Assignments".  Since you don't have any assignments or family members defined yet Alexa will run you through the guided setup.

# Usage
Once the setup process interact with your new skill like so:
* "Alexa, open FHE assignments" 
* "Alexa, start FHE assignments" 
* "Alexa, ask FHE assignments for this week's assignments" 
* "Alexa, ask FHE assignments for next week's assignments" 
* "Alexa, ask FHE assignments for last week's assignments" 
* "Alexa, ask FHE assignments who has what" 
* "Alexa, ask FHE assignments to give me the assignemnts" 
* "Alexa, ask FHE assignments for Joseph's assignment" if you have a family member named Joseph 
* "Alexa, what is Joseph's assignment using FHE assignments" if you have a family member named Joseph 
* "Alexa, what is Joseph's next week assignment using FHE assignments" if you have a family member named Joseph 
* "Alexa, ask FHE assignments who has Treat" if you have Treat as one of your family home evening assignments
* "Alexa, ask FHE assignments who is assigned to Treat next week" if you have Treat as one of your family home evening assignments
* "Alexa, tell FHE assignemnts to run setup"
* "Alexa, tell FHE assignemnts to setup assignments"
** "Joseph has Treat" if you have a family member named Joseph who is assigned to treat this week
** "Joseph is assigned Treat" if you have a family member named Joseph who is assigned to treat this week

Sometimes Alexa doesn't always hear you correctly, the next two utterances let you fix that.
* "Alexa, delete the family member Joseph" 
* "Alexa, delete the assignment Treat" 

You can always start the setup over and fix errors by saying, "Alexa, tell FHE assignments to run setup."

The skill also tries hard to catch any unknown utterances you say to it so that the developer can enhance the skill with your feedback.
