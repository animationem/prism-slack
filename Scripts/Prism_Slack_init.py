#-----------
# This plugin is for Prism-Pipeline 2.0. It integrates Slack features into Prism. IF you have any questions or need to reach out to me, send me an email or shoot me a message.

# Created by John Kesig while at Warm & Fuzzy in Los Angeles, CA, USA
# Contact: john.d.kesig@gmail.com
#-----------

from Prism_Slack_Variables import Prism_Slack_Variables
from Prism_Slack_Functions import Prism_Slack_Functions
from Prism_Slack_externalAccess_Functions import Prism_Slack_externalAccess_Functions


class Prism_Slack(Prism_Slack_Variables, Prism_Slack_Functions, Prism_Slack_externalAccess_Functions):
    def __init__(self, core):
        Prism_Slack_Variables.__init__(self, core, self)
        Prism_Slack_Functions.__init__(self, core, self)
        Prism_Slack_externalAccess_Functions.__init__(self, core, self)
