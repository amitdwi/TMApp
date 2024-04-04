import os
# Use the package we installed
from slack_bolt import App, Say

from slack_bolt.adapter.socket_mode import SocketModeHandler

import requests

import json

# Initialize your app with your bot token and signing secret
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def main():
   handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
   handler.start()

# Update App Home
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
  try:
    # Get the all tasks 
    response = requests.get('http://127.0.0.1:5000/tasks')
    if response.status_code == 200:
      #print(response.json())
      tasks = response.json()
      #print(tasks)
      tasks_block = []
      for task in tasks:
        #print(task)
        tasks_block.append(
            {
              "type": "section",
              "text": {
                "type": "plain_text",
                "text": task["description"],
                "emoji": True
              }
            }
        )
        tasks_block.append(
           {
              "type": "actions",
              "elements": [
                {
                  "type": "button",
                  "text": {
                    "type": "plain_text",
                    "text": "Update",
                    "emoji": True
                  },
                  "style": "primary",
                  "value": "action_value_123",
                  "action_id": "actionId-0"
                },
                {
                  "type": "button",
                  "text": {
                    "type": "plain_text",
                    "text": "Delete",
                    "emoji": True
                  },
                  "style": "danger",
                  "value": task["_id"],
                  "action_id": "actionId-1"
                }
              ]
            }
        )
    else:
      raise Exception(f"Non-success status code: {response.status_code}")
    # get_tasks = json.dumps(response)
    # for task in get_tasks:
    #   print(response)

    # task_block = {
    #     "type": "header",
    #     "text": {
    #       "type": "plain_text",
    #       "text": "description",
    #       "emoji": True
    #     }
    #   }

    home_blocks = [
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
            "value": "completed_tasks"
          },
          {
            "type": "button",
            "text": {
              "type": "plain_text",
              "text": "Create a task"
            },
            "value": "create_a_task",
            "action_id": "create_new_task"
          }
        ]
      },
      {
        "type": "divider"
      },
      {
        "type": "header",
        "text": {
          "type": "plain_text",
          "text": "You have 3 open tasks",
          "emoji": True
        }
      }
    ]
    home_blocks.extend(tasks_block)
    #print(home_blocks)
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=event["user"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",
        "blocks" : home_blocks
        # body of the view
        
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")


@app.shortcut("new_task")
def open_modal(ack, shortcut, client, logger):
    # Acknowledge shortcut request
    ack()

    try:
        # Call the views.open method using the WebClient passed to listeners
        result = client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "My App"},
                "close": {"type": "plain_text", "text": "Close"},
                "blocks": [
                  {
                      "type": "section",
                      "text": {
                          "type": "mrkdwn",
                          "text": "Create task the simplest modal.",
                      },
                  }
                ],
            },
        )
        logger.info(result)

    except Exception as e:
        logger.error("Error creating conversation: {}".format(e))

@app.action("create_new_task")
def create_new_task (ack, logger, body, client):
    logger.info(f"request body: {body}")
    ack()
    try:
        # Call the views.open method using the WebClient passed to listeners
        result = client.views_open(
            trigger_id=body["trigger_id"],
            view={
              "type": "modal",
              "callback_id": "create_task_view",
              "title": {
                "type": "plain_text",
                "text": "Create new task",
                "emoji": True
              },
              "submit": {
                "type": "plain_text",
                "text": "Submit",
                "emoji": True
              },
              "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
              },
              "blocks": [
                {
                  "type": "divider"
                },
                {
                  "type": "input",
                  "block_id": "input_task_details",
                  "element": {
                    "type": "plain_text_input",
                    "action_id": "input_task_details-action"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "New task",
                    "emoji": True
                  }
                },
                {
                  "type": "input",
                  "element": {
                    "type": "multi_users_select",
                    "placeholder": {
                      "type": "plain_text",
                      "text": "Select users",
                      "emoji": True
                    },
                    "action_id": "multi_users_select-action"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "Assign user",
                    "emoji": True
                  }
                }
              ]
            }
        )
        logger.info(result)

    except Exception as e:
        logger.error("Error creating conversation: {}".format(e))

# Handle a view_submission request
@app.view("create_task_view")
def handle_submission(ack, body, context, view, logger, say:Say):
    ack()
    data = view["state"]["values"]
    new_data = {
        "assignee": body["user"]["id"],
        "description": data["input_task_details"]["input_task_details-action"]["value"],
        "status": "TODO"
    }
    #user = body["user"]["id"]
    request_dat= requests.post('http://127.0.0.1:5000/tasks', json=new_data)
    #print(user)
    #print(data)
    #print(context)
    # Validate the inputs
    errors = {}
    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return
    
    say(channel=context["user_id"], text="Task created successfully")
    logger.info(body)


@app.action("actionId-1")
def delete_task_action(ack, body, logger, payload, say):
    ack()
    logger.info(body)
    #print(payload["value"])
    requests.delete(f'http://127.0.0.1:5000/tasks/{payload["value"]}')

    say(channel=body["user"]["id"], text="Task deleted successfully")

# Ready? Start your app!
if __name__ == "__main__":
  main()

