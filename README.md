<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/animationem/prism-slack/blob/main/Resources/prism_slack_logo_long_light_banner.png">
  <source media="(prefers-color-scheme: light)" srcset="https://github.com/animationem/prism-slack/blob/main/Resources/prism_slack_logo_long_dark_banner.png">
  <img alt="Prism and Slack branding" src="https://github.com/animationem/prism-slack/blob/main/Resources/prism_slack_logo_long_light_banner.png">
</picture>  
  
<div>
<img src="https://img.shields.io/badge/Prism_Pipeline-2.0.13-mediumseagreen" alt="Prism Pipeline Version"> 
<img src="https://img.shields.io/badge/Slack_Plugin-2.0.13-4A154B?logo=slack" alt="Slack Plugin Version">
</div>


## Introduction
This is the Slack plugin for Prism-Pipeline 2.0  


## Requirements
### Prism  
Currently the Slack plugin uses your Real Name to cross compare the Prism User and the Slack User. Your Prism username needs to be set to your first initial along with your last name. As an example my username in Prism is: jkesig. It will compare this username with my Real Name on Slack: John Kesig. It will find my user id information and publish a message, while tagging me, to the channel.

This will be fixed with the option to allow for the users input, as this was a leftover feature from the studios internal version of this plugin. Once it is updated, this readme will reflect it.
  
### Slack  
1. Slack Bot
    - You are required to create a bot application in Slack. You can find the installation process for this below.

2. Your Name
    - You are also required to input your Real Name in your Slack profile. Your display name can be something different, but your Name must be input for proper tagging.

3. Channel Name = Project Name
    - Your channel must match the name of your current project. Will add the option for a [custom slack channel](#custom-slack-channel) in the future
  
## Installation
To install the Slack plugin, either download the current release package or you can download the zip file using the 'Code' dropdown menu option on the main repo page.  
  
Once you have it downloaded or unzipped, simply drag it into your Plugin folder and reload Prism. It should automatically be checked.

In order to get Prism to work with Slack, you will need to install a Slack bot to the workspace. In the 'Resources' folder of this repo, you can find a file called [manifest.yml](Resources/manifest.yml). This will make the process of creating a bot much simpler. 

To start creating your app head to the [Your Apps](https://api.slack.com/apps/) page on the Slack API website. Follow the instructions on this page to successfully install your bot using the provided manigest: [Creating Apps using manifests](https://api.slack.com/reference/manifests#creating_apps).  

Once you have created your app, feel free to give it an App Icon on the Basic Information page, under Display Information.  

Select the 'Install App' section on the left side, and Install it to your workspace.  

Finally, head to the 'OAuth & Permissions' page on the left side menu, and copy the **Bot User OAuth Token**. You will copy that and input it into the Slack Project/Studio Settings page. 


## Plugin Options  
### Publish to Slack  
Currently there are two options that would allow you to publish you renders/playblasts directly to Slack. You can either do it via the Project Browser in the Media tab, or by sending it straight to Slack from the State Manager. 
<details>
    <summary>Project Browser</summary>

</details>

<details> 
    <summary>State Manager</summary>

</details>


### Notify Artist/User  



## Devs/Admins  
<details>
    <summary>Where is the Access Token stored?</summary>  

### Prism Plus/Pro with Studio
> {PRISM_STUDIO_PATH}\configs\slack.json  
### Open Source
> {PRISM_PROJECT_PATH}\00_Pipeline\pipeline.json
</details>

<details>
<summary>Notify Users Pool</summary>

### Studio  
This pool of artists will be drawn from the Prism Studio plugin. By default, it accepts all default user roles in the pool with the exception of users with the role: *Deactivated*

### Channel
This pool will be drawn from the list of users currently in the Slack Project Channel

### Team
This pool of artists is pulled from the entire Team in Slack. Please note that this list could get rather large if you are working with a big production team. I plan to include some options for Usergroups with the Teams option, but it will take time.
</details>


## Planned Features  

<details>
    <summary>Comments Based on Threads</summary>
    I will be including the option to include comments in threads on Slack as comments on Prism versions in the media tab.
</details>

<details>
    <summary>Version Status Actions</summary>
    I will be including some Actionable buttons below a publish to choose the current status once it's reviewed
</details>

<details>
    <summary><a name="custom-slack-channel">Custom Slack Channel Names</a></summary>
    
    
    I will give you the option to add custom slack channel names. Default option will still be the name of the project

</details>

<details>
    <summary>Multi-Notification Channels</summary>
    There has been some discussion around channels that are more suited for different department. This can also reduce the flood of notifications from larger projects.
</details>

<details>
    <summary>User Chosen Names</summary>
    I'll be adding a feature that will let the user choose their name according to their name on Slack in the Prism User Settings
</details>

<details>
    <summary>Notify via Ephemeral Messages</summary>
    Lots of messages could potentially flood the channel unncessarily to alert another artist of an incoming update. Ephemeral messages can help to reduce the impact.
</details>

<details>
    <summary>Notify via Direct Messages</summary>
    Direct messages to individual artists can bebe chosen as an option in order to avoid flooding the channel unneccesarily.
</details>

<details>
    <summary>Include Usergroups for Team selection</summary>
</details>


## Known Bugs/Limitations  
<details>
    <summary>Deadline Unsupported</summary>
    Currently publishing to the farm is unsupported. It will need a separate Python task as part of the job in order to carry out the publishing via render farm.
</details>