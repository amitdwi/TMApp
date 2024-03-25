import os
# Use the package we installed
from slack_bolt import App

# Initialize your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_APP_TOKEN")
)

# New functionality
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",

        # body of the view
        "blocks": [
          {
            "type": "header",
            "text": {
              "type": "plain_text",
              "text": "Task Management App Home",
              "emoji": True
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Open tasks"
                },
                "style": "primary",
                "value": "open_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Completed tasks"
                },
                "style": "danger",
                "value": "completed_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a task"
                },
                "value": "create_a_task"
              }
            ]
          },
          {
            "type": "divider"
          }
        ]
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

# Ready? Start your app!
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))

