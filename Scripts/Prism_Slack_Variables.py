#-----------
# This plugin is for Prism-Pipeline 2.0. It integrates Slack features into Prism. IF you have any questions or need to reach out to me, send me an email or shoot me a message.

# Created by John Kesig while at Warm & Fuzzy in Los Angeles, CA, USA
# Contact: john.d.kesig@gmail.com
#-----------

import os


class Prism_Slack_Variables(object):
    def __init__(self, core, plugin):
        self.version = "v2.0.13"
        self.pluginName = "Slack"
        self.pluginType = "Custom"
        self.platforms = ["Windows"]
        self.pluginDirectory = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
