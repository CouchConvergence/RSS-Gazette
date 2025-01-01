# RSS-Gazette
A tool to automatically generate Epub newspapers from RSS feeds, and email them to your Kindle device. 

## Installation 
Clone the repo, then inside the main folder execute:
```
$ pip install -r requirements.text
```
##  Configuration 
First, you need to configure your feeds and settings, to do so, execute
```
$ python gui.py
```
Set your settings as desired, and save. 
### Note on SMTP and emails:
You will have to use an email service that supports SMTP. For one examples: [Gmail with app passwords enabled](https://support.google.com/mail/answer/185833?hl=en). 

Refer to your email provider for SMTP configuration information. For example, if you're using Gmail, you'd need to follow [this guide](https://support.google.com/a/answer/176600?hl=en).

## Usage

After configuration is done, you can manually execute the script by running
```
$ python sender.py
```

### Automation
To make this script run automatically at your desired time, you'll have to manually create a cron job. 

First, execute the following command to open your crontab file
```
$ crontab -e
```
Let's say we want to run the script every day at 6:00 AM, we'd have to add th is line:
```
0 6 * * * /usr/bin/python3 /path/to/sender.py
```
Then save and quit. Replace `/usr/bin/python3` with whatever is your python path. 

To find your python path, execute 
```
$ which python3
```

To check that your cron job was added succesfully, execute 
```
$ crontab -l
```
And it should appear.

Do note that the script won't execute if your computer is asleep. You'll neeed to use some other method to accomplish that, such as systemd timer. Refer to the documentation of your distro's init system to find out how.

