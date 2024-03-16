# Define Slack webhook URL
SLACK_WEBHOOK_URL="Enter slack webhook"

# Function to send a message to Slack webhook
send_slack_notification() {
    curl -X POST -H 'Content-type: application/json' --data '{"text":"'"$1"'"}' $SLACK_WEBHOOK_URL
}

# Notify start of scan
send_slack_notification "Trufflehog scan started."

for i in $(cat gitrepo.txt) ; do docker run --rm -it -v "$PWD:/pwd" trufflesecurity/trufflehog:latest github --repo https://github.com/organisation_name/$i.git --only-verified --exclude-detectors=GCP,SlackWebhook,FacebookOAuth,Twilio --token=token-value > /home/ubuntu/truffelhog_automation/truffel_output/git-$i.txt ; done

# Notify completion of scan
send_slack_notification "Trufflehog scan completed."

#This script is compatable on ubuntu server
