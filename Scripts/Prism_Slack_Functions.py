#-----------
# This plugin is for Prism-Pipeline 2.0. It integrates Slack features into Prism. IF you have any questions or need to reach out to me, send me an email or shoot me a message.

# Created by John Kesig while at Warm & Fuzzy in Los Angeles, CA, USA
# Contact: john.d.kesig@gmail.com
#-----------

import os
import requests
import subprocess
import glob
import re
import json

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

# Upload box to let the user know their content is being uploaded
class UploadDialog(QDialog):
    def __init__(self):
        super(UploadDialog, self).__init__()
        self.setWindowTitle('Slack Upload')
        self.setModal(True)
        self.setLayout(QVBoxLayout())
        
        self.label = QLabel('Uploading to Slack...')
        self.layout().addWidget(self.label)

# Comment box for users to leave comments
class CommentDialog(QDialog):
    def __init__(self):
        super(CommentDialog, self).__init__()

        file_directory = os.path.dirname(os.path.abspath(__file__))
        plugin_directory = os.path.dirname(file_directory)

        self.setWindowTitle('Slack Additional Comments')
        self.setWindowIcon(QIcon(os.path.join(plugin_directory, "Resources", "slack-icon.png")))
        self.setModal(True)
        self.setLayout(QVBoxLayout())
        self.buttonLayout = QHBoxLayout()
        
        self.label = QLabel('Please leave your additional comments below (optional)')
        self.layout().addWidget(self.label)
        
        self.text_edit = QTextEdit()
        self.layout().addWidget(self.text_edit)
        
        self.button_ok = QPushButton('OK')
        self.button_cancel = QPushButton('Cancel')

        self.buttonLayout.addWidget(self.button_ok)
        self.buttonLayout.addWidget(self.button_cancel)
        self.layout().addLayout(self.buttonLayout)

        self.button_ok.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)

    def get_comments(self):
        return self.text_edit.toPlainText()

class WarningDialog(QDialog):
    def __init__(self, team_user=None):
        super(WarningDialog, self).__init__(team_user)

        self.setWindowTitle('Warning')
        self.setModal(True)
        self.setLayout(QVBoxLayout())

        self.l_warning = QLabel(f'{team_user} is not in the Channel!\nThis could unintentionally invite them to a channel by tagging them, or let them know what you are working on.\n\nAre you sure you want to proceed?')
        
        self.button_layout = QHBoxLayout()
        self.button_yes = QPushButton('Yes')
        self.button_no = QPushButton('No')
        self.button_layout.addWidget(self.button_yes)
        self.button_layout.addWidget(self.button_no)

        self.layout().addWidget(self.l_warning)
        self.layout().addLayout(self.button_layout)

        self.button_yes.accepted.connect(self.accept)
        self.button_no.rejected.connect(self.reject)

# Publish content to Slack
class Prism_Slack_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.core.registerCallback("mediaPlayerContextMenuRequested", self.mediaPlayerContextMenuRequested, plugin=self)
        self.core.registerCallback("onStateStartup", self.onStateStartup, plugin=self)
        self.core.registerCallback("postPlayblast", self.postPlayblast, plugin=self)
        self.core.registerCallback("postRender", self.postRender, plugin=self)
        self.core.registerCallback("preRender", self.preRender, plugin=self)

    @err_catcher(name=__name__)
    def onStateStartup(self, state):
        # Add Slack publishing options to the State Manager
        if state.className == "Playblast":
            lo = state.gb_playblast.layout()
        elif state.className == "ImageRender":
            lo = state.gb_imageRender.layout() 
        else:
            return

        if not hasattr(state, 'gb_slack'):
            state.gb_slack = QGroupBox()
            state.gb_slack.setTitle("Slack")
            state.gb_slack.setCheckable(True)
            state.gb_slack.setChecked(False)
            state.gb_slack.setObjectName("gb_slack")
            state.gb_slack.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            self.lo_slack_group = QVBoxLayout()
            self.lo_slack_group.setContentsMargins(-1, 15, -1, -1)
            state.gb_slack.setLayout(self.lo_slack_group)
            
            lo.addWidget(state.gb_slack)

        state.gb_slack.toggled.connect(lambda toggled: self.createSlackSubmenu(toggled, state))
    
    # Handle output result after playblast
    @err_catcher(name=__name__) 
    def postPlayblast(self, **kwargs):
        global state 
        state = kwargs.get('state', None)

        if state.chb_slackPublish.isChecked():
            outputPath = kwargs.get("settings", None)["outputName"]
            ext = os.path.splitext(outputPath)[1].replace(".", "")

            rangeType = state.cb_rangeType.currentText()

            if rangeType == "Single Frame" or rangeType in ['Scene', 'Shot']:
                startFrame = state.l_rangeStart.text()
                endFrame = state.l_rangeEnd.text()

            if rangeType == "Custom":
                startFrame = state.sp_rangeStart.text()
                endFrame = state.sp_rangeEnd.text()
            
            if rangeType == "Expression":
                self.core.popup("Your render has been published but the Slack plugin does not support expression ranges yet.")
                return

            if ext in ['.png', '.jpg']:
                if rangeType == "Single Frame":
                    outputList = [outputPath]
                
                if rangeType != "Single Frame" and startFrame == endFrame:
                    file = outputPath.replace("#" * self.core.framePadding, str(startFrame))
                    outputList = [file]

                if rangeType != "Single Frame" and startFrame < endFrame:                    
                    if state.chb_mediaConversion.isChecked() is False:
                        convert = self.convertImageSequence(outputPath)
                        outputList = [convert]
                
                if state.chb_mediaConversion.isChecked() is True:
                    option = state.cb_mediaConversion.currentText().lower()

                    base = os.path.basename(outputPath).split(".")[0]
                    top_directory = os.path.dirname(outputPath)

                    converted_directory = f"{top_directory} ({ext})"
                    converted_file = f"{converted_directory}/{base} ({ext}).{ext}"
                    outputList = [converted_file]

                    if option in ['png', 'jpg']:
                        framePad = '#' * self.core.framePadding
                        sequence = f"{converted_directory}/{base} ({ext}).{framePad}.{ext}"
                        convert = self.convertImageSequence(sequence)
                        outputList = [convert]

            self.publishToSlack_fromSM(outputList)

        return

    @err_catcher(name=__name__)
    def preRender(self, **kwargs):
        global state 
        state = kwargs.get('state', None)

        access_token = self.getAccessToken()
        
        if state.chb_slackNotify.isChecked():
            notify_studio_user = state.cb_studioUsers.currentText()
            project = self.getCurrentProject()
            channel = self.getChannelId(access_token, project)
            slack_user = self.getSlackUser(access_token, notify_studio_user, channel)
            product = state.l_taskName.text()
            sender = self.getSlackUser(access_token, self.core.username, channel)
            
            self.notifySlackUser(access_token, slack_user, channel, product, sender)

    # Handle the output result after rendering
    @err_catcher(name=__name__)
    def postRender(self, **kwargs):
        global state 
        state = kwargs.get('state', None)

        if state.chb_slackPublish.isChecked():
            outputPath = kwargs.get("settings", None)["outputName"]
            ext = os.path.splitext(outputPath)[1].replace(".", "")

            rangeType = state.cb_rangeType.currentText()

            if rangeType == "Single Frame" or rangeType in ['Scene', 'Shot']:
                startFrame = state.l_rangeStart.text()
                endFrame = state.l_rangeEnd.text()

            if rangeType == "Custom":
                startFrame = state.sp_rangeStart.text()
                endFrame = state.sp_rangeEnd.text()
            
            if rangeType == "Expression":
                self.core.popup("Your render has been published but the Slack plugin does not support expression ranges yet.")
                return

            if ext in ['exr', 'png', 'jpg']:
                if rangeType == "Single Frame":
                    outputList = [outputPath]

                if rangeType != "Single Frame" and startFrame == endFrame:
                    file = outputPath.replace("#" * self.core.framePadding, str(startFrame))
                    outputList = [file]

                if rangeType != "Single Frame" and startFrame < endFrame:                 
                    if state.chb_mediaConversion.isChecked() is False:
                        convert = self.convertImageSequence(outputPath)
                        outputList = [convert]
                    else:
                        option = state.cb_mediaConversion.currentText().lower()
                        ext = self.retrieveExtension(option)

                        base = os.path.basename(outputPath).split(".")[0]
                        version_directory = os.path.dirname(os.path.dirname(outputPath))
                        aov_directory = os.path.basename(os.path.dirname(outputPath))
                        file = base.split(f'_{aov_directory}')[0]

                        converted_directory = f"{version_directory} ({ext})/{aov_directory}"
                        converted_files = f"{converted_directory}/{file} ({ext})_{aov_directory}.{ext}"
                        
                        outputList = [converted_files]

                        if ext in ['png', 'jpg']:
                            framePad = '#' * self.core.framePadding
                            sequence = f"{converted_directory}/{file} ({ext})_{aov_directory}.{framePad}.{ext}"
                            convert = self.convertImageSequence(sequence)
                            outputList = [convert]
                            
            self.publishToSlack_fromSM(outputList)
        
        return
    
    # Sets the plugin as active
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    # Get current version in the Media tab in the Prism Project Browser
    @err_catcher(name=__name__)
    def mediaPlayerContextMenuRequested(self, origin, menu):
        if not type(origin.origin).__name__ == "MediaBrowser":
            return

        version = origin.origin.getCurrentVersion()
        if not version:
            return

        if not origin.seq:
            return

        action = QAction("Publish to Slack", origin)
        
        file_directory = os.path.dirname(os.path.abspath(__file__))
        plugin_directory = os.path.dirname(file_directory)
        iconPath = os.path.join(plugin_directory, "Resources", "slack-icon.png")
        icon = self.core.media.getColoredIcon(iconPath)
        
        action.triggered.connect(lambda: self.publishToSlack_fromMedia(origin.seq))
        
        menu.insertAction(menu.actions()[0], action)
        action.setIcon(icon)

    @err_catcher(name=__name__)
    def createSlackSubmenu(self, toggled, state):
        # If the group box is toggled on
        if toggled:
            if not hasattr(state, 'cb_studioUsers'):
                state.cb_studioUsers = QComboBox()
                state.cb_studioUsers.setPlaceholderText("Select Artist")

                lo_slack_publish = QHBoxLayout()
                lo_slack_publish.setContentsMargins(10, 5, 0, 0)

                state.l_slackPublish = QLabel("Publish to Slack:")
                state.chb_slackPublish = QCheckBox()
                state.chb_slackPublish.setLayoutDirection(Qt.RightToLeft)

                lo_slack_notify = QHBoxLayout()
                lo_slack_notify.setContentsMargins(10, 5, 0, 0)

                state.l_slackNotify = QLabel("Notify Artist:")
                state.chb_slackNotify = QCheckBox()
                state.chb_slackNotify.setLayoutDirection(Qt.RightToLeft)

                lo_slack_publish.addWidget(state.l_slackPublish)
                lo_slack_publish.addWidget(state.chb_slackPublish)
                lo_slack_notify.addWidget(state.l_slackNotify)
                lo_slack_notify.addWidget(state.chb_slackNotify)
                lo_slack_notify.addWidget(state.cb_studioUsers)

                state.lo_slack_publish = lo_slack_publish
                state.lo_slack_notify = lo_slack_notify
                state.gb_slack.layout().addLayout(lo_slack_publish)
                state.gb_slack.layout().addLayout(lo_slack_notify)

                self.populateStudioUsers(state)

        else:
            layout = state.gb_slack.layout()

            self.removeCleanupLayout(layout, 'lo_slack_publish', state)
            self.removeCleanupLayout(layout, 'lo_slack_notify', state)

            for attr in [
                'chb_slackPublish', 
                'l_slackPublish', 
                'cb_studioUsers', 
                'l_slackNotify', 
                'chb_slackNotify'
                ]:
                if hasattr(state, attr):
                    delattr(state, attr)

    @err_catcher(name=__name__)
    def populateStudioUsers(self, state):
        access_token = self.getAccessToken()
        proj = self.getCurrentProject()
        channel_id = self.getChannelId(access_token, proj)

        notify_method = self.getNotifyMethod().lower()
        users = []
        if notify_method == "studio":
            users = self.getStudioUsers(state)
        
        elif notify_method == "channel":
            members = self.getChannelUsers(access_token, channel_id)
            users = [member['real_name'] for member in members]
        
        elif notify_method == "team":
            members = self.getTeamUsers(access_token)
            users = [member['real_name'] for member in members]

        state.cb_studioUsers.addItems(users)

    # remove widgets and cleanup sub-layouts when the group box is toggled off
    @err_catcher(name=__name__)
    def removeCleanupLayout(self,layout, attribute_name, state):
        if hasattr(state, attribute_name):
            sub_layout = getattr(state, attribute_name)
            if sub_layout:
                for i in reversed(range(sub_layout.count())):
                    item = sub_layout.itemAt(i)
                    if item.widget(): 
                        widget = item.widget()
                        sub_layout.removeWidget(widget)
                        widget.deleteLater()

                layout.removeItem(sub_layout)
                sub_layout.deleteLater()

                delattr(state, attribute_name)

    # Get proper extension from media conversion type
    @err_catcher(name=__name__)
    def retrieveExtension(self, option):
        if 'png' in option:
            ext = 'png'
        elif 'jpg' in option:
            ext = 'jpg'
        elif 'mp4' in option:
            ext ='mp4'
        elif 'mov' in option:
            ext ='mov'
        else:
            ext = option
        
        return ext
    
    # Convert image sequence to MP4 for Slack
    @err_catcher(name=__name__)
    def convertImageSequence(self, sequence):
        # Define the "slack" output folder
        folder_path = os.path.dirname(sequence)
        slack_folder = os.path.join(folder_path, "slack")
        
        if not os.path.exists(slack_folder):
            os.makedirs(slack_folder)

        # Construct input and output paths
        input_sequence = sequence.replace('.####.', '.%04d.')
        basename = os.path.basename(sequence).split('.####.')[0]
        output_file = os.path.join(slack_folder, basename + '.mp4')
        
        ffmpegPath = os.path.join(self.core.prismLibs, "Tools", "FFmpeg", "bin", "ffmpeg.exe")
        ffmpegPath = ffmpegPath.replace('\\', '/')

        if not os.path.exists(ffmpegPath):
            self.core.popup(f"ffmpeg not found at {ffmpegPath}")
            return

        # Search for matching files to determine the start frame
        pattern = sequence.replace('.####.', '.*.')
        files = sorted(glob.glob(pattern))
        if not files:
            self.core.popup(f"No files found matching pattern: {pattern}")
            return
        
        start_frame = re.search(r"\.(\d{4})\.", files[0])
        if start_frame:
            start_frame = start_frame.group(1)
        else:
            self.core.popup("Failed to determine the starting frame.")
            return

        # Run ffmpeg to create the video
        try:
            result = subprocess.run([
                ffmpegPath,
                "-framerate", "24",
                "-start_number", start_frame,
                "-i", input_sequence,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_file
            ], capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            self.core.popup(f"Error running ffmpeg: {e.stderr.decode()}")
            return

        output_file = output_file.replace("\\", "/")
        return output_file

    @err_catcher(name=__name__)
    def getStudioSlackConfig(self):
        studio_plugin = self.core.plugins.getPlugin("Studio")
        studio_slack_config = os.path.join(studio_plugin.getStudioPath(), "configs", "slack.json")

        return studio_slack_config
    
    @err_catcher(name=__name__)
    def getNotifyMethod(self):
        studio_slack_config = self.getStudioSlackConfig()
        with open(studio_slack_config, "r") as f:
            load_config = json.load(f)
            
            return load_config["slack"]["notify_method"]

    # Get Slack Access Token from environment variable
    @err_catcher(name=__name__)
    def getAccessToken(self):
        studio_plugin = self.isStudioLoaded()
        
        if studio_plugin is None:
            access_token = self.core.getConfig("slack", "token", configPath=self.core.prismIni)
            return access_token
        else:
            studio_slack_config = self.getStudioSlackConfig()
            with open(studio_slack_config, "r") as f:
                load_config = json.load(f)
                
                return load_config["slack"]["token"]

    # Get Slack Channel ID from conversation list
    @err_catcher(name=__name__)
    def getChannelId(self, access_token, project_name):
        conversation_id = None

        try:
            url = "https://slack.com/api/conversations.list"
            headers = {
                "Authorization": f"Bearer {access_token}"
                }
            response = requests.get(url, headers=headers)

            conversations = response.json()

            for conversation in conversations["channels"]:
                if conversation["name"] == project_name:
                    conversation_id = conversation["id"]
                    return conversation_id

        except:
            print("Failed to retrieve conversation members.")
            return None
    
    # Get current prism user
    @err_catcher(name=__name__)
    def getPrismUser(self):
        user = self.core.username
        return user
    
    # Get Slack User ID from user list
    @err_catcher(name=__name__)
    def getSlackUser(self, prism_user, channel_users):
        for user in channel_users:
            try:
                first, last = user['real_name'].split(" ")
                username = first[0] + last
            except:
                continue

            if username.lower() == prism_user:
                slack_user = user['id']
                return slack_user

    # Get team users from Slack
    @err_catcher(name=__name__)
    def getTeamUsers(self, access_token):
        url = "https://slack.com/api/users.list"
        headers = {
            "Authorization": f"Bearer {access_token}"
            }
        response = requests.get(url, headers=headers)
        
        members = response.json()['members']

        team_users = []
        
        for m in members:
            if m.get('real_name') is not None and m.get('is_bot') == False:
                team_users.append({'real_name': m.get('real_name'), 'id': m.get('id')})
        
        return team_users
    
    @err_catcher(name=__name__)
    def getChannelUsers(self, access_token, conversation_id):
        url = "https://slack.com/api/conversations.members"
        headers = {
            "Authorization": f"Bearer {access_token}"
            }
        params = {
            "channel": conversation_id
            }
        
        response = requests.get(url, headers=headers, params=params)

        channel_members = response.json()['members']
        channel_users = []

        for m in channel_members:
            url = "https://slack.com/api/users.info"
            headers = {
                "Authorization": f"Bearer {access_token}"
                }
            params = {
                "user": m
                }

            response = requests.get(url, headers=headers, params=params)

            user = response.json()

            user_info = user['user']['real_name']
            user_id = user['user']['id']

            channel_users.append({"id": user_id, "real_name": user_info})
        
        return channel_users

    @err_catcher(name=__name__)
    def getStudioUsers(self, state):
        studio= self.core.getPlugin("Studio")
        data = studio.getStudioUsers()
        users = []
        for user in data:
            if user.get('role') in ['admin', 'manager', 'artist']:
                users.append(user.get('name'))
        
        return users

    @err_catcher(name=__name__)
    def teamsUserWarning(self, user):
        dialog = WarningDialog(team_user=user)
        if dialog.exec_() == QDialog.Accepted:
            return True
        else:
            return False

    # Notify user about new version of product is on the way!
    @err_catcher(name=__name__)
    def notifySlackUser(self, access_token, slack_user, channel, product, sender):
        import random

        if os.getenv('PRISM_SEQUENCE') is not None:
            seq = os.getenv('PRISM_SEQUENCE')
            shot = os.getenv('PRISM_SHOT')

        message = self.getMessage(slack_user, seq, shot, product, sender)

        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {access_token}"
            }
        payload = {
            "channel": channel,
            "text": f"{message}"
        }
        requests.post(url, headers=headers, json=payload)

    @err_catcher(name=__name__)
    def getMessage(self, slack_user, seq, shot, product, sender):
        import random
        if random.randint(0, 100) == 90:
            message = f"Dearest <@{slack_user}>,\nI bring you tidings of the utmost importance! The {product} render for Shot `{shot}` in the enchanting Sequence `{seq}` has begun. Courtesy of the illustrious <@{sender}>, of course. May the pixels align in harmonious perfection!\nYours in cinematic anticipation,\nMoira Rose"

        elif 1== 1:
            message = f"<@{slack_user}>\n`{product}`/`{seq}`/`{shot}`\n<https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeW4xNGl1dGxtMWY5d2tsMTBuYXc3enYza3FkNnpoZDNoYWlremh5NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/SSiwN19NtD1xUAikqf/giphy.gif>"

        elif state.cb_studioUsers.currentText() == "dwalz" and random.randint(0, 100) == 80:
            message = f"<@{slack_user}>! Ew, David! Okay, like, I just had to tell you—{product} for Shot `{shot}` in Sequence {seq} is, like, officially rendering. It’s going to be so fabulous, like, total gallery-wall vibes. Don’t mess this up, okay bye!"

        else:
            message = f"Heads up <@{slack_user}>!\n A new version of `{product}` for `{seq}`/`{shot}` is on the way!"

        return message

    @err_catcher(name=__name__)
    def getCurrentProject(self):
        proj = self.core.getConfig("globals", "project_name", configPath=self.core.prismIni).lower()

        return proj
    
    # Upload file to Slack
    @err_catcher(name=__name__)
    def uploadToSlack(self, access_token, conversation_id, file_upload, method):
        prism_user = self.getPrismUser()
        channel_users = self.getChannelUsers(access_token, conversation_id)
        slack_user = self.getSlackUser(prism_user, channel_users)

        file_stats = os.stat(file_upload)
        file_size = file_stats.st_size
        
        url_request = "https://slack.com/api/files.getUploadURLExternal"
        headers = {
            "Authorization": f"Bearer {access_token}"
            }
        payload = {
            "filename": file_upload, 
            "length": file_size
            }
        response = requests.get(url_request, headers=headers, params=payload)

        upload_url = response.json()['upload_url']
        id = response.json()['file_id']

        with open(file_upload, "rb") as f:
            files = {"file": f}
            response = requests.post(upload_url, headers=headers, files=files)

        try:
            comment_dialog = CommentDialog()
            if comment_dialog.exec_() == QDialog.Accepted:
                init_comment = f"Uploaded By: <@{slack_user}>\n"
                comment = init_comment + comment_dialog.get_comments()

            else:
                self.upload_message.close()
                return

            post_url = "https://slack.com/api/files.completeUploadExternal"
            post_payload = {
                "files": [{"id": id, "title": file_upload}], 
                "channel_id": conversation_id, 
                "initial_comment": comment
                }

            response = requests.post(post_url, headers=headers, json=post_payload)

            uploaded = True
            self.successfulPOST(uploaded, method)
        
        except Exception as e:
            uploaded = False
            self.successfulPOST(uploaded, method)

    # Publish file to Slack
    @err_catcher(name=__name__)
    def publishToSlack_fromMedia(self, file):
        current_project = self.core.getConfig("globals", "project_name", configPath=self.core.prismIni).lower()
        
        access_token = self.getAccessToken()
        conversation_id = self.getChannelId(access_token, current_project)

        file_upload = file[0]
        file_upload.replace("\\", "/")

        self.upload_message = UploadDialog()
        self.upload_message.show()

        QTimer.singleShot(0, lambda: self.uploadToSlack(access_token, conversation_id, file_upload, method="Media" ))

    @err_catcher(name=__name__)
    def publishToSlack_fromSM(self, file):
        current_project = self.core.getConfig("globals", "project_name", configPath=self.core.prismIni).lower()
        
        access_token = self.getAccessToken()
        conversation_id = self.getChannelId(access_token, current_project)
        file_upload = file[0]
        file_upload.replace("\\", "/")

        self.upload_message = UploadDialog()
        self.upload_message.show()

        QTimer.singleShot(0, lambda: self.uploadToSlack(access_token, conversation_id, file_upload, method="SM" ))

    def successfulPOST(self, uploaded, method):
        self.upload_message.close()

        if uploaded == True and method == "Media":
            QMessageBox.information(None, "Slack Upload", "Asset has been uploaded successfully")
        elif uploaded == False:
            QMessageBox.warning(None, "Slack Upload", "Failed to upload asset to Slack")
        else:
            None        

    @err_catcher(__name__)
    def isStudioLoaded(self):
        studio = self.core.plugins.getPlugin("Studio")
        return studio