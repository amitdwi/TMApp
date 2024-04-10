import os
# Use the package we installed
from slack_bolt import App, Say

from slack_bolt.adapter.socket_mode import SocketModeHandler

from auth.mongo import db

import requests

import json

# Initialize your app with your bot token and signing secret
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def main():
   handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
   handler.start()


def guest_home_view(client,event, logger, context):
    try:
      # views.publish is the method that your app uses to push a view to the Home tab
      client.views_publish(
          # the user that opened your app's app home
          user_id=context['user_id'],
          view = {
            "type": "home",
            "callback_id": "guest_home_view",
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
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "Click the Login button to start using TM App"
                },
                "accessory": {
                  "type": "button",
                  "text": {
                    "type": "plain_text",
                    "text": "Login",
                    "emoji": True
                  },
                  "style": "primary",
                  "value": "login_button",
                  "action_id": "login-button-action"
                }
              }
            ]
          }
        )
    except Exception as e:
      logger.error(f"Error publishing home tab: {e}")

# Login button Modal

@app.action("login-button-action")
def open_login_modal(ack, body, logger, context, client):
    ack()
    logger.info(body)
    try:
        # Call the views.open method using the WebClient passed to listeners
        client.views_open(
          trigger_id=body["trigger_id"],
          view={
            "callback_id": "login_view",
            "title": {
              "type": "plain_text",
              "text": "Login",
              "emoji": True
            },
            "submit": {
              "type": "plain_text",
              "text": "Login",
              "emoji": True
            },
            "type": "modal",
            "close": {
              "type": "plain_text",
              "text": "Cancel",
              "emoji": True
            },
            "blocks": [
              {
                  "type": "section",
                  "block_id": "user_name_details",
                  "text": {
                      "type": "mrkdwn",
                      "text": f"Username: *{context['user_id']}*"
                  }
              },
              {
                "type": "input",
                "block_id": "password_details",
                "element": {
                  "type": "plain_text_input",
                  "action_id": "user_password",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Password"
                  }
                },
                "label": {
                  "type": "plain_text",
                  "text": "Password",
                  "emoji": True
                }
              }
            ]
          }
        )
    except Exception as e:
      logger.error(f"Error publishing home tab: {e}")

# Handle login data 

# Handle a view_submission request
@app.view("login_view")
def handle_submission(ack, body, client, context, view, payload):
    ack()
    view_data = view["state"]["values"]
    data = {
      "username": context['user_id'],
      "password": view_data ["password_details"]["user_password"]["value"]
    }
    result = requests.post('http://127.0.0.1:5000/user/login', json=data)
    print(data)
    print("--------------------------------------------")
    print(payload)
    print("--------------------------------------------")
    user_result = result.json()

    tokens = db['token']

    tokenData = {
        'workspace': payload["team_id"],
        'user': context['user_id'],
        'salt': user_result["salt"]
    }
    tokens.insert_one(tokenData)
    errors = {}
    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return


def check_token(context):
    tokens = db['token']
    result = tokens.find_one({'user': context["user_id"]})
    print(result)
    if result and result["salt"] != None :
        print(result["salt"])
        return True
    return False


#Update App Home

def update_home_tab(client, context, logger):
  try:
    # Get the all tasks 
    response = requests.get('http://127.0.0.1:5000/tasks')
    tasks_length = None
    if response.status_code == 200:
      #print(response.json())
      tasks = response.json()[0]
      tasks_length = len(response.json()[0])
      print(tasks_length)
      #print(tasks)
      if(tasks_length):
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
                      "text": "Edit",
                      "emoji": True
                    },
                    "value": task["id"],
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
                    "value": task["id"],
                    "action_id": "actionId-1"
                  }
                ]
              }
          )
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
                  "text": "My Tasks"
                },
                "value": "my_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "To Do"
                },
                "value": "todo_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "In Progress"
                },
                "value": "inprogress_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Completed Tasks"
                },
                "value": "completed_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create Task"
                },
                "style": "primary",
                "value": "create_a_task",
                "action_id": "create_new_task"
              }
            ]
          },
          {
            "type": "divider"
          }
        ]
        home_blocks.extend(tasks_block)
      else:
        home_blocks = [
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a task",
                  "emoji": True
                },
                "value": "create_a_task",
                "action_id": "create_new_task"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a project",
                  "emoji": True
                },
                "value": "create_a_project",
                "action_id": "create_project"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Join a project",
                  "emoji": True
                },
                "value": "join_a_project",
                "action_id": "join_project"
              }
            ]
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "plain_text",
              "text": "You have not created any task yet, Please click on 'Create a task' button and create your first task.",
              "emoji": True
            }
          }
        ]
    else:
      raise Exception(f"Non-success status code: {response.status_code}")

    #print(home_blocks)
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=context["user_id"],
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

@app.event("app_home_opened")
def show_home_tab_conditionaly(client, context, logger):
  if check_token(context) : 
     print("Amit")
     update_home_tab(client, context, logger)
  else:
     guest_home_view(client, context, logger, context)

# @app.shortcut("new_task")
# def open_modal(ack, shortcut, client, logger):
#     # Acknowledge shortcut request
#     ack()

#     try:
#         # Call the views.open method using the WebClient passed to listeners
#         result = client.views_open(
#             trigger_id=shortcut["trigger_id"],
#             view={
#                 "type": "modal",
#                 "title": {"type": "plain_text", "text": "My App"},
#                 "close": {"type": "plain_text", "text": "Close"},
#                 "blocks": [
#                   {
#                       "type": "section",
#                       "text": {
#                           "type": "mrkdwn",
#                           "text": "Create task the simplest modal.",
#                       },
#                   }
#                 ],
#             },
#         )
#         logger.info(result)

#     except Exception as e:
#         logger.error("Error creating conversation: {}".format(e))

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
def handle_submission(ack, body, context, client, view, logger, say:Say):
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
    update_home_tab(client, context, logger)
    logger.info(body)


@app.action("actionId-1")
def delete_task_action(ack, body, logger, payload, context, say, client):
    ack()
    logger.info(body)
    #print(payload["value"])
    requests.delete(f'http://127.0.0.1:5000/tasks/{payload["value"]}')

    say(channel=body["user"]["id"], text="Task deleted successfully")

    update_home_tab(client, context, logger)

#def create_your_first_task () : 
   

@app.action("actionId-0")
def edit_task(ack, body, client, logger, payload):
    ack()
    try:
        # Call the views.open method using the WebClient passed to listeners
        result = client.views_open(
            trigger_id=body["trigger_id"],
            view={
              "type": "modal",
              "callback_id": "update_task_view",
              "title": {
                "type": "plain_text",
                "text": "Update task",
                "emoji": True
              },
              "private_metadata": payload["value"],
              "submit": {
                "type": "plain_text",
                "text": "Update",
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
                  "block_id": "update_input_task",
                  "element": {
                    "type": "plain_text_input",
                    "action_id": "update_task_details-action"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "New task",
                    "emoji": True
                  }
                },
                {
                  "type": "input",
                  "block_id": "update_user_id",
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

@app.view("update_task_view")
def update_task(ack, body, logger, payload, say, view, client, context):
    ack()
    logger.info(body)
    print(view["private_metadata"])
    model_data = body["view"]["state"]["values"]
    print(model_data["update_input_task"]["update_task_details-action"]["value"])
    print(model_data["update_user_id"]["multi_users_select-action"]["selected_users"][0])
    #print(model_data["selected_users"])
    data = {
        "assignee": model_data["update_user_id"]["multi_users_select-action"]["selected_users"][0],
        "description": model_data["update_input_task"]["update_task_details-action"]["value"],
        "status": "DONE"
    }
    print(data)
    requests.put(f'http://127.0.0.1:5000/tasks/{view["private_metadata"]}', json=data)

    say(channel=body["user"]["id"], text="Task updated successfully")

    update_home_tab(client, context, logger)

# Ready? Start your app!
if __name__ == "__main__":
  main()

