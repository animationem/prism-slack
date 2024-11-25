#-----------
# This plugin is for Prism-Pipeline 2.0. It integrates Slack features into Prism. IF you have any questions or need to reach out to me, send me an email or shoot me a message.

# Created by John Kesig while at Warm & Fuzzy in Los Angeles, CA, USA
# Contact: john.d.kesig@gmail.com
#-----------

import os
import json

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

class Prism_Slack_externalAccess_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.core.registerCallback("onPluginsLoaded", self.onPluginsLoaded, plugin=self)

    # Callback function when the plugins are loaded
    @err_catcher(__name__)
    def onPluginsLoaded(self):
        studio = self.isStudioLoaded()

        if studio is not None:
            self.core.registerCallback("studioSettings_loadSettings", self.studioSettings_loadSettings, plugin=self)
            
        else:
            self.core.registerCallback("projectSettings_loadUI", self.projectSettings_loadUI, plugin=self)
    
    # Load the UI for the Slack plugin in the studio settings window
    @err_catcher(__name__)
    def studioSettings_loadSettings(self, origin, settings):
        self.createUI(origin, settings)

    # Load the UI for the Slack plugin in the project settings window
    @err_catcher(__name__)
    def projectSettings_loadUI(self, origin):
        self.createUI(origin, settings=None)

    # Create the UI for the Slack plugin
    @err_catcher(__name__)
    def createUI(self, origin, settings):
        self.w_slackTab = QWidget()
        self.lo_slack = QVBoxLayout(self.w_slackTab)

        self.l_slack = QLabel()
        file_directory = os.path.dirname(os.path.abspath(__file__))
        plugin_directory = os.path.dirname(file_directory)
        self.i_slack = os.path.join(plugin_directory, "Resources", "slack-logo.png")
        self.l_slack.setPixmap(QPixmap(self.i_slack))
        scale = 0.05
        self.l_slack.setScaledContents(True)
        self.l_slack.setFixedSize(self.l_slack.pixmap().width() * scale, self.l_slack.pixmap().height() * scale)
        self.l_slack.setContentsMargins(0, 0, 0, 0)

        self.le_slack = QLineEdit()
        self.le_slack.setPlaceholderText("Enter your Slack API Token")
        self.le_slack.setEchoMode(QLineEdit.Password)
        self.le_slack.setReadOnly(True)
        self.le_slack.setFocusPolicy(Qt.NoFocus)
        self.le_slack.setContextMenuPolicy(Qt.NoContextMenu)
        self.checkToken()

        self.lo_dual = QVBoxLayout()
        self.lo_one = QHBoxLayout()
        self.lo_one.addStretch()
        self.lo_dual.addLayout(self.lo_one)

        self.lo_notify_method = QHBoxLayout()
        self.l_notify_method = QLabel("Notify Method:")
        self.cb_notify_method = QComboBox()
        self.cb_notify_method.setPlaceholderText("Notify Method")
        self.cb_notify_method.setLayoutDirection(Qt.RightToLeft)
        self.l_notify_help = QLabel()
        self.help_icon = os.path.join(self.core.prismLibs, "Scripts", "UserInterfacesPrism", "help.png")
        self.l_notify_help.setPixmap(QPixmap(self.help_icon))
        self.l_notify_help.setToolTip("""<p style='line-height:1;'>
                                      <span style='color:DodgerBlue;'><b>Studio</b></span>: Draw from the users in the Studio plugin pool<br>
                                      <br>
                                      <span style='color:Tomato;'><b>Project</b></span>: Draw from the users in the Slack Project Channel<br>
                                      <br>
                                      <span style='color:MediumSeaGreen;'><b>Team</b></span>: Draw from the users in the Slack Team pool<br>
                                      <i>Note: If not kept up to date, your Team pool could be rather large</i>
                                      </p>""")
        self.lo_notify_method.addStretch()
        self.lo_notify_method.addWidget(self.l_notify_method)
        self.lo_notify_method.addWidget(self.cb_notify_method)
        self.lo_notify_method.addWidget(self.l_notify_help)
        self.lo_notify_method.setContentsMargins(0, 80, 0, 0)
        self.lo_dual.addLayout(self.lo_notify_method)
        
        if self.isStudioLoaded():
            self.cb_notify_method.addItem("Studio")

        self.cb_notify_method.addItem("Channel")
        self.cb_notify_method.addItem('Team')
        self.checkNotifyMethod()

        self.b_slack = QPushButton("Input Token")
        self.b_slack.clicked.connect(self.inputToken)

        self.lo_slack.addStretch()
        self.lo_slack.addWidget(self.l_slack)
        self.lo_slack.setAlignment(self.l_slack, Qt.AlignBottom)

        self.lo_slack.addWidget(self.le_slack)
        self.lo_slack.setAlignment(self.le_slack, Qt.AlignBottom)

        self.lo_slack.addWidget(self.b_slack)
        self.lo_slack.setAlignment(self.b_slack, Qt.AlignBottom | Qt.AlignCenter)

        self.lo_slack.addLayout(self.lo_dual)
        self.lo_slack.setAlignment(self.lo_dual, Qt.AlignTop)

        self.lo_slack.addStretch()

        self.cb_notify_method.currentIndexChanged.connect(self.updateNotifyMethod)

        origin.addTab(self.w_slackTab, "Slack")

    @err_catcher(__name__)
    def updateNotifyMethod(self, index):
        notify_method = self.cb_notify_method.currentText()

        pipeline_data = self.loadConfig()
        if "slack" in pipeline_data:
            pipeline_data["slack"]["notify_method"] = notify_method
        
        pipeline_file = self.getConfig()
        with open(pipeline_file, "w") as f:
            json.dump(pipeline_data, f, indent=4)
    
    # Check the method of notification to Slack users
    @err_catcher(__name__)
    def checkNotifyMethod(self):
        pipeline_data = self.loadConfig()

        if "slack" in pipeline_data:
            notify_method = pipeline_data["slack"].get("notify_method")
            self.cb_notify_method.setCurrentText(notify_method)
        else:
            notify_method = None

    # Pop up a dialog to input the Slack API token
    @err_catcher(__name__)
    @err_catcher(name=__name__)
    def inputToken(self):
        text, ok = QInputDialog.getText(
            None,
            "Slack",
            "Enter your Slack API token",
            QLineEdit.Normal,
            ""
        )
        if ok:
            self.slackToken = text
            self.le_slack.setText(self.slackToken)
            self.saveToken(self.slackToken)
    
    # Check if the Slack API token is present in the pipeline configuration file
    @err_catcher(name=__name__)
    def checkToken(self):
        pipeline_data = self.loadConfig()

        if "slack" not in pipeline_data:
            pipeline_data["slack"] = {}
            pipeline_data["slack"]["token"] = {}
        
            self.le_slack.setPlaceholderText("Enter your Slack API Token")

        studio = self.isStudioLoaded()
        if studio is not None:
            token = pipeline_data["slack"]["token"]
            self.le_slack.setText(token)
            return

        else:
            token = self.core.getConfig("slack", "token", configPath=self.core.prismIni)
            self.le_slack.setText(token)
            return


    # Save the token in the pipeline configuration file
    @err_catcher(name=__name__)
    def saveToken(self, token):
        pipeline_data = self.loadConfig()
        self.checkSlackOptions(pipeline_data)

        pipeline_data["slack"]["token"] = token

        pipeline_file = self.getConfig()
        with open(pipeline_file, "w") as f:
            json.dump(pipeline_data, f, indent=4)

    # Load the pipeline configuration file
    @err_catcher(name=__name__)
    def loadConfig(self):
        pipeline_file = self.getConfig()

        if not os.path.exists(pipeline_file):
            os.makedirs(os.path.dirname(pipeline_file), exist_ok=True)
            with open(pipeline_file, "w") as f:
                json.dump({"slack": {"token": ""}}, f, indent=4)
        
        elif os.path.exists(pipeline_file):
            with open(pipeline_file, "r") as f:
                return json.load(f)
        else:
            print("Could not find/create Studio Slack Config file")
            return 

    # Get the path to the pipeline configuration file
    @err_catcher(name=__name__)
    def getConfig(self):
        # Get the path to the pipeline configuration file from the environment variable PRISM_STUDIO_PATH
        if os.getenv("PRISM_STUDIO_PATH") is not None:
            studio_path = os.path.join(os.getenv("PRISM_STUDIO_PATH")) 
            slack_config = os.path.join(studio_path, "configs", "slack.json")
            return slack_config
        
        # If the Studio plugin is not available, check the project configuration file
        elif self.core.getPlugin("Studio") is None:
            prjConfig_path = os.path.dirname(self.core.prismIni)
            prjConfig = os.path.join(prjConfig_path, "pipeline.json")
            return prjConfig
        
        # Get the config from the studio path
        else: 
            studio_plugin = self.core.getPlugin("Studio")
            studio_path = studio_plugin.getStudioPath()
            slack_config = os.path.join(studio_path, "configs", "slack.json")
            return slack_config

    # Check if Slack options are present in the pipeline configuration file. If it's not, add them
    @err_catcher(name=__name__)
    def checkSlackOptions(self, pipeline_data):
        if "slack" not in pipeline_data:
            pipeline_data["slack"] = {}
        
        if "token" not in pipeline_data["slack"]:
            pipeline_data["slack"]["token"] = ""

    # Check if the studio plugin is loaded
    @err_catcher(__name__)
    def isStudioLoaded(self):
        studio = self.core.plugins.getPlugin("Studio")
        return studio