# FHE Assignments Alexa Skill
An Alexa skill to record which family members have what assignments each week for Family Home Evening and rotate them automatically each week.

Members of the [Church of Jesus Christ of Latter-day Saints](https://www.mormon.org/) spend an evening together with their families once a week to strengthen family ties. We abbreviate it FHE. See more about Family Home Evening [here](https://www.lds.org/topics/family-home-evening/purpose?lang=eng&old=true).

This project is a Crazy Friday project of the Office of IT (OIT) at Brigham Young University. Crazy Friday is OIT's R&D time on Friday's each week. I wanted a better way to track our family's FHE assignments and also wanted to try out DynamoDB.

My family kept our assignment schedule previously in a Google Spreadsheet but even that felt cumbersome compared to the amazing ease of use and almost fritionless voice interface experience of the Amazon Echo devices. 

# One-time Setup
Say, "Alexa, enable FHE Assignments".

Then say, "Alexa, open FHE Assignments".  Since you don't have any assignments or family members defined yet Alexa will run you through the guided setup.

# Usage
Once the setup process is done say, "Alexa, ask FHE assignments for this week's assignments" and Alexa will tell you who is assigned for what this week.
